import contextlib
import contextvars

# Whether the SQL panel records queries. The toolbar turns this off while it
# persists its own data, so those queries, including the BEGIN/COMMIT of
# their transactions, don't show up in the SQL panel.
record_sql = contextvars.ContextVar("debug-toolbar-record-sql", default=True)


@contextlib.contextmanager
def suppress_sql_recording():
    """
    Hide the queries run inside this block from the SQL panel, unless the
    ``SKIP_TOOLBAR_QUERIES`` setting is ``False``.
    """
    token = record_sql.set(False)
    try:
        yield
    finally:
        record_sql.reset(token)
