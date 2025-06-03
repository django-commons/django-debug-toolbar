import uuid
from collections import defaultdict

from asgiref.sync import sync_to_async
from django.db import connections
from django.template.loader import render_to_string
from django.urls import path
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, ngettext

from debug_toolbar import settings as dt_settings
from debug_toolbar.forms import SignedDataForm
from debug_toolbar.panels import Panel
from debug_toolbar.panels.sql import views
from debug_toolbar.panels.sql.forms import SQLSelectForm
from debug_toolbar.panels.sql.tracking import wrap_cursor
from debug_toolbar.panels.sql.utils import (
    contrasting_color_generator,
    is_select_query,
    reformat_sql,
)
from debug_toolbar.utils import render_stacktrace


def get_isolation_level_display(vendor, level):
    if vendor == "postgresql":
        try:
            import psycopg

            choices = {
                # AUTOCOMMIT level does not exists in psycopg3
                psycopg.IsolationLevel.READ_UNCOMMITTED: _("Read uncommitted"),
                psycopg.IsolationLevel.READ_COMMITTED: _("Read committed"),
                psycopg.IsolationLevel.REPEATABLE_READ: _("Repeatable read"),
                psycopg.IsolationLevel.SERIALIZABLE: _("Serializable"),
            }
        except ImportError:
            import psycopg2.extensions

            choices = {
                psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT: _("Autocommit"),
                psycopg2.extensions.ISOLATION_LEVEL_READ_UNCOMMITTED: _(
                    "Read uncommitted"
                ),
                psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED: _("Read committed"),
                psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ: _(
                    "Repeatable read"
                ),
                psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE: _("Serializable"),
            }

    else:
        raise ValueError(vendor)
    return choices.get(level)


def get_transaction_status_display(vendor, level):
    if vendor == "postgresql":
        try:
            import psycopg

            choices = {
                psycopg.pq.TransactionStatus.IDLE: _("Idle"),
                psycopg.pq.TransactionStatus.ACTIVE: _("Active"),
                psycopg.pq.TransactionStatus.INTRANS: _("In transaction"),
                psycopg.pq.TransactionStatus.INERROR: _("In error"),
                psycopg.pq.TransactionStatus.UNKNOWN: _("Unknown"),
            }
        except ImportError:
            import psycopg2.extensions

            choices = {
                psycopg2.extensions.TRANSACTION_STATUS_IDLE: _("Idle"),
                psycopg2.extensions.TRANSACTION_STATUS_ACTIVE: _("Active"),
                psycopg2.extensions.TRANSACTION_STATUS_INTRANS: _("In transaction"),
                psycopg2.extensions.TRANSACTION_STATUS_INERROR: _("In error"),
                psycopg2.extensions.TRANSACTION_STATUS_UNKNOWN: _("Unknown"),
            }

    else:
        raise ValueError(vendor)
    return choices.get(level)


def _similar_query_key(query):
    return query["raw_sql"]


def _duplicate_query_key(query):
    raw_params = () if query["params"] is None else tuple(query["params"])
    # repr() avoids problems because of unhashable types
    # (e.g. lists) when used as dictionary keys.
    # https://github.com/django-commons/django-debug-toolbar/issues/1091
    return (query["raw_sql"], repr(raw_params))


def _process_query_groups(query_groups, databases, colors, name):
    counts = defaultdict(int)
    for (alias, _key), query_group in query_groups.items():
        count = len(query_group)
        # Queries are similar / duplicates only if there are at least 2 of them.
        if count > 1:
            color = next(colors)
            for query in query_group:
                query[f"{name}_count"] = count
                query[f"{name}_color"] = color
            counts[alias] += count
    for alias, db_info in databases.items():
        db_info[f"{name}_count"] = counts[alias]


class SQLPanel(Panel):
    """
    Panel that displays information about the SQL queries run while processing
    the request.
    """

    is_async = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sql_time = 0
        self._queries = []
        self._databases = {}
        # synthetic transaction IDs, keyed by DB alias
        self._transaction_ids = {}

    def new_transaction_id(self, alias):
        """
        Generate and return a new synthetic transaction ID for the specified DB alias.
        """
        trans_id = uuid.uuid4().hex
        self._transaction_ids[alias] = trans_id
        return trans_id

    def current_transaction_id(self, alias):
        """
        Return the current synthetic transaction ID for the specified DB alias.
        """
        trans_id = self._transaction_ids.get(alias)
        # Sometimes it is not possible to detect the beginning of the first transaction,
        # so current_transaction_id() will be called before new_transaction_id().  In
        # that case there won't yet be a transaction ID. so it is necessary to generate
        # one using new_transaction_id().
        if trans_id is None:
            trans_id = self.new_transaction_id(alias)
        return trans_id

    def record(self, **kwargs):
        kwargs["djdt_query_id"] = uuid.uuid4().hex
        self._queries.append(kwargs)
        alias = kwargs["alias"]
        if alias not in self._databases:
            self._databases[alias] = {
                "time_spent": kwargs["duration"],
                "num_queries": 1,
            }
        else:
            self._databases[alias]["time_spent"] += kwargs["duration"]
            self._databases[alias]["num_queries"] += 1
        self._sql_time += kwargs["duration"]

    # Implement the Panel API

    nav_title = _("SQL")

    @property
    def nav_subtitle(self):
        stats = self.get_stats()
        query_count = len(stats.get("queries", []))
        return ngettext(
            "%(query_count)d query in %(sql_time).2fms",
            "%(query_count)d queries in %(sql_time).2fms",
            query_count,
        ) % {
            "query_count": query_count,
            "sql_time": stats.get("sql_time"),
        }

    @property
    def title(self):
        count = len(self.get_stats().get("databases"))
        return ngettext(
            "SQL queries from %(count)d connection",
            "SQL queries from %(count)d connections",
            count,
        ) % {"count": count}

    template = "debug_toolbar/panels/sql.html"

    @classmethod
    def get_urls(cls):
        return [
            path("sql_select/", views.sql_select, name="sql_select"),
            path("sql_explain/", views.sql_explain, name="sql_explain"),
            path("sql_profile/", views.sql_profile, name="sql_profile"),
        ]

    async def aenable_instrumentation(self):
        """
        Async version of enable instrumentation.
        For async capable panels having async logic for instrumentation.
        """
        await sync_to_async(self.enable_instrumentation)()

    def enable_instrumentation(self):
        # This is thread-safe because database connections are thread-local.
        for connection in connections.all():
            wrap_cursor(connection)
            connection._djdt_logger = self

    def disable_instrumentation(self):
        for connection in connections.all():
            connection._djdt_logger = None

    def generate_stats(self, request, response):
        similar_query_groups = defaultdict(list)
        duplicate_query_groups = defaultdict(list)

        if self._queries:
            sql_warning_threshold = dt_settings.get_config()["SQL_WARNING_THRESHOLD"]

            width_ratio_tally = 0
            factor = int(256.0 / (len(self._databases) * 2.5))
            for n, db in enumerate(self._databases.values()):
                rgb = [0, 0, 0]
                color = n % 3
                rgb[color] = 256 - n // 3 * factor
                nn = color
                # XXX: pretty sure this is horrible after so many aliases
                while rgb[color] < factor:
                    nc = min(256 - rgb[color], 256)
                    rgb[color] += nc
                    nn += 1
                    if nn > 2:
                        nn = 0
                    rgb[nn] = nc
                db["rgb_color"] = rgb

            # the last query recorded for each DB alias
            last_by_alias = {}
            for query in self._queries:
                alias = query["alias"]

                similar_query_groups[(alias, _similar_query_key(query))].append(query)
                duplicate_query_groups[(alias, _duplicate_query_key(query))].append(
                    query
                )

                trans_id = query.get("trans_id")
                prev_query = last_by_alias.get(alias, {})
                prev_trans_id = prev_query.get("trans_id")

                # If two consecutive queries for a given DB alias have different
                # transaction ID values, a transaction started, finished, or both, so
                # annotate the queries as appropriate.
                if trans_id != prev_trans_id:
                    if prev_trans_id is not None:
                        prev_query["ends_trans"] = True
                    if trans_id is not None:
                        query["starts_trans"] = True
                if trans_id is not None:
                    query["in_trans"] = True

                if "iso_level" in query:
                    query["iso_level"] = get_isolation_level_display(
                        query["vendor"], query["iso_level"]
                    )
                if "trans_status" in query:
                    query["trans_status"] = get_transaction_status_display(
                        query["vendor"], query["trans_status"]
                    )
                query["is_slow"] = query["duration"] > sql_warning_threshold
                query["is_select"] = is_select_query(query["raw_sql"])

                query["rgb_color"] = self._databases[alias]["rgb_color"]
                try:
                    query["width_ratio"] = (query["duration"] / self._sql_time) * 100
                except ZeroDivisionError:
                    query["width_ratio"] = 0
                query["start_offset"] = width_ratio_tally
                query["end_offset"] = query["width_ratio"] + query["start_offset"]
                width_ratio_tally += query["width_ratio"]

                last_by_alias[alias] = query

            # Close out any transactions that were in progress, since there is no
            # explicit way to know when a transaction finishes.
            for final_query in last_by_alias.values():
                if final_query.get("trans_id") is not None:
                    final_query["ends_trans"] = True

        group_colors = contrasting_color_generator()
        _process_query_groups(
            similar_query_groups, self._databases, group_colors, "similar"
        )
        _process_query_groups(
            duplicate_query_groups, self._databases, group_colors, "duplicate"
        )

        self.record_stats(
            {
                "databases": sorted(
                    self._databases.items(), key=lambda x: -x[1]["time_spent"]
                ),
                "queries": self._queries,
                "sql_time": self._sql_time,
            }
        )

    def generate_server_timing(self, request, response):
        stats = self.get_stats()
        title = "SQL {} queries".format(len(stats.get("queries", [])))
        value = stats.get("sql_time", 0)
        self.record_server_timing("sql_time", title, value)

    # Cache the content property since it manipulates the queries in the stats
    # This allows the caller to treat content as idempotent
    @cached_property
    def content(self):
        if self.has_content:
            stats = self.get_stats()
            colors = contrasting_color_generator()
            trace_colors = defaultdict(lambda: next(colors))

            for query in stats.get("queries", []):
                query["sql"] = reformat_sql(query["sql"], with_toggle=True)
                query["form"] = SignedDataForm(
                    auto_id=None,
                    initial=SQLSelectForm(
                        initial={
                            "djdt_query_id": query["djdt_query_id"],
                            "request_id": self.toolbar.request_id,
                        }
                    ).initial,
                )
                query["stacktrace"] = render_stacktrace(query["stacktrace"])
                query["trace_color"] = trace_colors[query["stacktrace"]]

            return render_to_string(self.template, stats)
