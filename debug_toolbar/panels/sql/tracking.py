import contextlib
import contextvars
import datetime
import json
from time import perf_counter

import django.test.testcases
from django.utils.encoding import force_str

from debug_toolbar.utils import get_stack_trace, get_template_info

try:
    import psycopg

    PostgresJson = psycopg.types.json.Jsonb
    STATUS_IN_TRANSACTION = psycopg.pq.TransactionStatus.INTRANS
except ImportError:
    try:
        from psycopg2._json import Json as PostgresJson
        from psycopg2.extensions import STATUS_IN_TRANSACTION
    except ImportError:
        PostgresJson = None
        STATUS_IN_TRANSACTION = None

# Prevents SQL queries from being sent to the DB. It's used
# by the TemplatePanel to prevent the toolbar from issuing
# additional queries.
allow_sql = contextvars.ContextVar("debug-toolbar-allow-sql", default=True)


class SQLQueryTriggered(Exception):
    """Thrown when template panel triggers a query"""


def wrap_cursor(connection):
    # When running a SimpleTestCase, Django monkey patches some DatabaseWrapper
    # methods, including .cursor() and .chunked_cursor(), to raise an exception
    # if the test code tries to access the database, and then undoes the monkey
    # patching when the test case is finished.  If we monkey patch those methods
    # also, Django's process of undoing those monkey patches will fail.  To
    # avoid this failure, and because database access is not allowed during a
    # SimpleTestCase anyway, skip applying our instrumentation monkey patches if
    # we detect that Django has already monkey patched DatabaseWrapper.cursor().
    if isinstance(connection.cursor, django.test.testcases._DatabaseFailure):
        return
    if not hasattr(connection, "_djdt_cursor"):
        connection._djdt_cursor = connection.cursor
        connection._djdt_chunked_cursor = connection.chunked_cursor
        connection._djdt_logger = None

        def cursor(*args, **kwargs):
            # Per the DB API cursor() does not accept any arguments. There's
            # some code in the wild which does not follow that convention,
            # so we pass on the arguments even though it's not clean.
            # See:
            # https://github.com/django-commons/django-debug-toolbar/pull/615
            # https://github.com/django-commons/django-debug-toolbar/pull/896
            logger = connection._djdt_logger
            cursor = connection._djdt_cursor(*args, **kwargs)
            if logger is None:
                return cursor
            mixin = NormalCursorMixin if allow_sql.get() else ExceptionCursorMixin
            return patch_cursor_wrapper_with_mixin(cursor.__class__, mixin)(
                cursor.cursor, connection, logger
            )

        def chunked_cursor(*args, **kwargs):
            # prevent double wrapping
            # solves https://github.com/django-commons/django-debug-toolbar/issues/1239
            logger = connection._djdt_logger
            cursor = connection._djdt_chunked_cursor(*args, **kwargs)
            if logger is not None and not isinstance(cursor, DjDTCursorWrapperMixin):
                mixin = NormalCursorMixin if allow_sql.get() else ExceptionCursorMixin
                return patch_cursor_wrapper_with_mixin(cursor.__class__, mixin)(
                    cursor.cursor, connection, logger
                )
            return cursor

        connection.cursor = cursor
        connection.chunked_cursor = chunked_cursor


def patch_cursor_wrapper_with_mixin(base_wrapper, mixin):
    class DjDTCursorWrapper(mixin, base_wrapper):
        pass

    return DjDTCursorWrapper


class DjDTCursorWrapperMixin:
    def __init__(self, cursor, db, logger):
        super().__init__(cursor, db)
        # logger must implement a ``record`` method
        self.logger = logger


class ExceptionCursorMixin(DjDTCursorWrapperMixin):
    """
    Wraps a cursor and raises an exception on any operation.
    Used in Templates panel.
    """

    def __getattr__(self, attr):
        raise SQLQueryTriggered()


class NormalCursorMixin(DjDTCursorWrapperMixin):
    """
    Wraps a cursor and logs queries.
    """

    def _decode(self, param):
        if PostgresJson and isinstance(param, PostgresJson):
            # psycopg3
            if hasattr(param, "obj"):
                return param.dumps(param.obj)
            # psycopg2
            if hasattr(param, "adapted"):
                return param.dumps(param.adapted)

        # If a sequence type, decode each element separately
        if isinstance(param, (tuple, list)):
            return [self._decode(element) for element in param]

        # If a dictionary type, decode each value separately
        if isinstance(param, dict):
            return {key: self._decode(value) for key, value in param.items()}

        # make sure datetime, date and time are converted to string by force_str
        CONVERT_TYPES = (datetime.datetime, datetime.date, datetime.time)
        try:
            return force_str(param, strings_only=not isinstance(param, CONVERT_TYPES))
        except UnicodeDecodeError:
            return "(encoded string)"

    def _last_executed_query(self, sql, params):
        """Get the last executed query from the connection."""
        # Django's psycopg3 backend creates a new cursor in its implementation of the
        # .last_executed_query() method.  To avoid wrapping that cursor, temporarily set
        # the DatabaseWrapper's ._djdt_logger attribute to None.  This will cause the
        # monkey-patched .cursor() and .chunked_cursor() methods to skip the wrapping
        # process during the .last_executed_query() call.
        self.db._djdt_logger = None
        try:
            return self.db.ops.last_executed_query(self.cursor, sql, params)
        finally:
            self.db._djdt_logger = self.logger

    def _record(self, method, sql, params):
        alias = self.db.alias
        vendor = self.db.vendor

        if vendor == "postgresql":
            # The underlying DB connection (as opposed to Django's wrapper)
            conn = self.db.connection
            initial_conn_status = conn.info.transaction_status

        start_time = perf_counter()
        try:
            return method(sql, params)
        finally:
            stop_time = perf_counter()
            duration = (stop_time - start_time) * 1000
            _params = ""
            with contextlib.suppress(TypeError):
                # object JSON serializable?
                _params = json.dumps(self._decode(params))
            template_info = get_template_info()

            # Sql might be an object (such as psycopg Composed).
            # For logging purposes, make sure it's str.
            if vendor == "postgresql" and not isinstance(sql, str):
                if isinstance(sql, bytes):
                    sql = sql.decode("utf-8")
                else:
                    sql = sql.as_string(conn)
            else:
                sql = str(sql)

            kwargs = {
                "vendor": vendor,
                "alias": alias,
                "sql": self._last_executed_query(sql, params),
                "duration": duration,
                "raw_sql": sql,
                "params": _params,
                "stacktrace": get_stack_trace(skip=2),
                "template_info": template_info,
            }

            if vendor == "postgresql":
                # If an erroneous query was ran on the connection, it might
                # be in a state where checking isolation_level raises an
                # exception.
                try:
                    iso_level = conn.isolation_level
                except conn.InternalError:
                    iso_level = "unknown"
                # PostgreSQL does not expose any sort of transaction ID, so it is
                # necessary to generate synthetic transaction IDs here.  If the
                # connection was not in a transaction when the query started, and was
                # after the query finished, a new transaction definitely started, so get
                # a new transaction ID from logger.new_transaction_id().  If the query
                # was in a transaction both before and after executing, make the
                # assumption that it is the same transaction and get the current
                # transaction ID from logger.current_transaction_id().  There is an edge
                # case where Django can start a transaction before the first query
                # executes, so in that case logger.current_transaction_id() will
                # generate a new transaction ID since one does not already exist.
                final_conn_status = conn.info.transaction_status
                if final_conn_status == STATUS_IN_TRANSACTION:
                    if initial_conn_status == STATUS_IN_TRANSACTION:
                        trans_id = self.logger.current_transaction_id(alias)
                    else:
                        trans_id = self.logger.new_transaction_id(alias)
                else:
                    trans_id = None

                kwargs.update(
                    {
                        "trans_id": trans_id,
                        "trans_status": conn.info.transaction_status,
                        "iso_level": iso_level,
                    }
                )

            # We keep `sql` to maintain backwards compatibility
            self.logger.record(**kwargs)

    def callproc(self, procname, params=None):
        return self._record(super().callproc, procname, params)

    def execute(self, sql, params=None):
        return self._record(super().execute, sql, params)

    def executemany(self, sql, param_list):
        return self._record(super().executemany, sql, param_list)
