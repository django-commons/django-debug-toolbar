import asyncio
import datetime
import os
import unittest
from unittest.mock import call, patch

import django
from asgiref.sync import sync_to_async
from django.apps import apps
from django.contrib.auth.models import User
from django.db import connection, transaction
from django.db.backends.utils import CursorDebugWrapper, CursorWrapper
from django.db.models import Count
from django.db.utils import DatabaseError
from django.shortcuts import render
from django.test.utils import override_settings

import debug_toolbar.panels.sql.tracking as sql_tracking
from debug_toolbar import settings as dt_settings
from debug_toolbar.models import HistoryEntry
from debug_toolbar.panels.sql import SQLPanel, tracking

try:
    import psycopg
except ImportError:
    psycopg = None

from ..base import BaseMultiDBTestCase, BaseTestCase
from ..models import Binary, PostgresJSON


def sql_call(*, use_iterator=False):
    qs = User.objects.all()
    if use_iterator:
        qs = qs.iterator()
    return list(qs)


def sql_call_toolbar_model():
    """Query one of the toolbar's models to test tracking of SQL queries."""
    qs = HistoryEntry.objects.all()
    return list(qs)


async def async_sql_call_toolbar_model():
    """(async) Query one of the toolbar's models to test tracking of SQL queries."""
    qs = HistoryEntry.objects.all()
    return await sync_to_async(list)(qs)


async def async_sql_call(*, use_iterator=False):
    qs = User.objects.all()
    if use_iterator:
        qs = qs.iterator()
    return await sync_to_async(list)(qs)


async def concurrent_async_sql_call(*, use_iterator=False):
    qs = User.objects.all()
    if use_iterator:
        qs = qs.iterator()
    return await asyncio.gather(sync_to_async(list)(qs), User.objects.acount())


def patch_tracking_ddt_models():
    """
    Set the tracking.DDT_MODELS constant to the toolbar's models.
    This only gets configured when the store is set to the DatabaseStore.
    """
    if (
        dt_settings.get_config()["TOOLBAR_STORE_CLASS"]
        == "debug_toolbar.store.DatabaseStore"
    ):
        apps.get_app_config("debug_toolbar").import_models()
        tracking.DDT_MODELS = {
            m._meta.db_table for m in apps.get_app_config("debug_toolbar").get_models()
        }


class SQLPanelTestCase(BaseTestCase):
    panel_id = SQLPanel.panel_id

    def test_disabled(self):
        config = {"DISABLE_PANELS": {"debug_toolbar.panels.sql.SQLPanel"}}
        self.assertTrue(self.panel.enabled)
        with self.settings(DEBUG_TOOLBAR_CONFIG=config):
            self.assertFalse(self.panel.enabled)

    def test_recording(self):
        self.assertEqual(len(self.panel._queries), 0)

        sql_call()

        # ensure query was logged
        self.assertEqual(len(self.panel._queries), 1)
        query = self.panel._queries[0]
        self.assertEqual(query["alias"], "default")
        self.assertTrue("sql" in query)
        self.assertTrue("duration" in query)
        self.assertTrue("stacktrace" in query)

        # ensure the stacktrace is populated
        self.assertTrue(len(query["stacktrace"]) > 0)

    def test_assert_num_queries_works(self):
        """
        Confirm Django's assertNumQueries and CaptureQueriesContext works

        See  https://github.com/django-commons/django-debug-toolbar/issues/1791
        """
        self.assertEqual(len(self.panel._queries), 0)
        with self.assertNumQueries(1):
            sql_call()
        self.assertEqual(len(self.panel._queries), 1)

    async def test_recording_async(self):
        self.assertEqual(len(self.panel._queries), 0)

        await async_sql_call()

        # ensure query was logged
        self.assertEqual(len(self.panel._queries), 1)
        query = self.panel._queries[0]
        self.assertEqual(query["alias"], "default")
        self.assertTrue("sql" in query)
        self.assertTrue("duration" in query)
        self.assertTrue("stacktrace" in query)

        # ensure the stacktrace is populated
        self.assertTrue(len(query["stacktrace"]) > 0)

    async def test_recording_concurrent_async(self):
        self.assertEqual(len(self.panel._queries), 0)

        await concurrent_async_sql_call()

        # ensure query was logged
        self.assertEqual(len(self.panel._queries), 2)
        query = self.panel._queries[0]
        self.assertEqual(query["alias"], "default")
        self.assertTrue("sql" in query)
        self.assertTrue("duration" in query)
        self.assertTrue("stacktrace" in query)

        # ensure the stacktrace is populated
        self.assertTrue(len(query["stacktrace"]) > 0)

    @override_settings(
        DEBUG_TOOLBAR_CONFIG={
            "SKIP_TOOLBAR_QUERIES": False,
            "TOOLBAR_STORE_CLASS": "debug_toolbar.store.DatabaseStore",
        }
    )
    def test_toolbar_model_query_is_tracked(self):
        """
        Test is toolbar models are tracked when the `SKIP_TOOLBAR_QUERIES`
        is set to False.
        """
        self.assertEqual(len(self.panel._queries), 0)

        patch_tracking_ddt_models()
        sql_call_toolbar_model()

        # ensure query was logged
        self.assertEqual(len(self.panel._queries), 1)
        query = self.panel._queries[0]
        self.assertTrue(HistoryEntry._meta.db_table in query["sql"])

    @override_settings(
        DEBUG_TOOLBAR_CONFIG={
            "SKIP_TOOLBAR_QUERIES": False,
            "TOOLBAR_STORE_CLASS": "debug_toolbar.store.DatabaseStore",
        }
    )
    async def test_toolbar_model_query_is_tracked_async(self):
        """
        (async) Test is toolbar models are tracked when the `SKIP_TOOLBAR_QUERIES`
        is set to False.
        """
        self.assertEqual(len(self.panel._queries), 0)

        patch_tracking_ddt_models()
        await async_sql_call_toolbar_model()

        # ensure query was logged
        self.assertEqual(len(self.panel._queries), 1)
        query = self.panel._queries[0]
        self.assertTrue(HistoryEntry._meta.db_table in query["sql"])

    @override_settings(
        DEBUG_TOOLBAR_CONFIG={
            "SKIP_TOOLBAR_QUERIES": True,
            "TOOLBAR_STORE_CLASS": "debug_toolbar.store.DatabaseStore",
        }
    )
    def test_toolbar_model_query_is_not_tracked(self):
        """
        Test is toolbar models are not tracked when the `SKIP_TOOLBAR_QUERIES`
        is set to True.
        """
        self.assertEqual(len(self.panel._queries), 0)

        patch_tracking_ddt_models()
        sql_call_toolbar_model()

        self.assertEqual(len(self.panel._queries), 0)

    @override_settings(
        DEBUG_TOOLBAR_CONFIG={
            "SKIP_TOOLBAR_QUERIES": True,
            "TOOLBAR_STORE_CLASS": "debug_toolbar.store.DatabaseStore",
        }
    )
    async def test_toolbar_model_query_is_not_tracked_async(self):
        """
        (async) Test is toolbar models are not tracked when the `SKIP_TOOLBAR_QUERIES`
        is set to True.
        """
        self.assertEqual(len(self.panel._queries), 0)

        patch_tracking_ddt_models()
        await async_sql_call_toolbar_model()

        self.assertEqual(len(self.panel._queries), 0)

    @unittest.skipUnless(
        connection.vendor == "postgresql", "Test valid only on PostgreSQL"
    )
    def test_recording_chunked_cursor(self):
        self.assertEqual(len(self.panel._queries), 0)

        sql_call(use_iterator=True)

        # ensure query was logged
        self.assertEqual(len(self.panel._queries), 1)

    @patch(
        "debug_toolbar.panels.sql.tracking.patch_cursor_wrapper_with_mixin",
        wraps=sql_tracking.patch_cursor_wrapper_with_mixin,
    )
    def test_cursor_wrapper_singleton(self, mock_patch_cursor_wrapper):
        sql_call()
        # ensure that cursor wrapping is applied only once
        self.assertIn(
            mock_patch_cursor_wrapper.mock_calls,
            [
                [call(CursorWrapper, sql_tracking.NormalCursorMixin)],
                # CursorDebugWrapper is used if the test is called with `--debug-sql`
                [call(CursorDebugWrapper, sql_tracking.NormalCursorMixin)],
            ],
        )

    @patch(
        "debug_toolbar.panels.sql.tracking.patch_cursor_wrapper_with_mixin",
        wraps=sql_tracking.patch_cursor_wrapper_with_mixin,
    )
    def test_chunked_cursor_wrapper_singleton(self, mock_patch_cursor_wrapper):
        sql_call(use_iterator=True)

        # ensure that cursor wrapping is applied only once
        self.assertIn(
            mock_patch_cursor_wrapper.mock_calls,
            [
                [call(CursorWrapper, sql_tracking.NormalCursorMixin)],
                # CursorDebugWrapper is used if the test is called with `--debug-sql`
                [call(CursorDebugWrapper, sql_tracking.NormalCursorMixin)],
            ],
        )

    @patch(
        "debug_toolbar.panels.sql.tracking.patch_cursor_wrapper_with_mixin",
        wraps=sql_tracking.patch_cursor_wrapper_with_mixin,
    )
    async def test_cursor_wrapper_async(self, mock_patch_cursor_wrapper):
        await sync_to_async(sql_call)()

        self.assertIn(
            mock_patch_cursor_wrapper.mock_calls,
            [
                [call(CursorWrapper, sql_tracking.NormalCursorMixin)],
                # CursorDebugWrapper is used if the test is called with `--debug-sql`
                [call(CursorDebugWrapper, sql_tracking.NormalCursorMixin)],
            ],
        )

    @patch(
        "debug_toolbar.panels.sql.tracking.patch_cursor_wrapper_with_mixin",
        wraps=sql_tracking.patch_cursor_wrapper_with_mixin,
    )
    async def test_cursor_wrapper_asyncio_ctx(self, mock_patch_cursor_wrapper):
        self.assertTrue(sql_tracking.allow_sql.get())
        await sync_to_async(sql_call)()

        async def task():
            sql_tracking.allow_sql.set(False)
            # By disabling sql_tracking.allow_sql, we are indicating that any
            # future SQL queries should be stopped. If SQL query occurs,
            # it raises an exception.
            with self.assertRaises(sql_tracking.SQLQueryTriggered):
                await sync_to_async(sql_call)()

        # Ensure this is called in another context
        await asyncio.create_task(task())
        # Because it was called in another context, it should not have affected ours
        self.assertTrue(sql_tracking.allow_sql.get())

        self.assertIn(
            mock_patch_cursor_wrapper.mock_calls,
            [
                [
                    call(CursorWrapper, sql_tracking.NormalCursorMixin),
                    call(CursorWrapper, sql_tracking.ExceptionCursorMixin),
                ],
                # CursorDebugWrapper is used if the test is called with `--debug-sql`
                [
                    call(CursorDebugWrapper, sql_tracking.NormalCursorMixin),
                    call(CursorDebugWrapper, sql_tracking.ExceptionCursorMixin),
                ],
            ],
        )

    def test_generate_server_timing(self):
        self.assertEqual(len(self.panel._queries), 0)

        sql_call()

        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)
        self.panel.generate_server_timing(self.request, response)

        # ensure query was logged
        self.assertEqual(len(self.panel._queries), 1)
        query = self.panel._queries[0]

        expected_data = {
            "sql_time": {"title": "SQL 1 queries", "value": query["duration"]}
        }

        self.assertEqual(self.panel.get_server_timing_stats(), expected_data)

    def test_non_ascii_query(self):
        self.assertEqual(len(self.panel._queries), 0)

        # non-ASCII text query
        list(User.objects.extra(where=["username = 'apéro'"]))
        self.assertEqual(len(self.panel._queries), 1)

        # non-ASCII text parameters
        list(User.objects.filter(username="thé"))
        self.assertEqual(len(self.panel._queries), 2)

        # non-ASCII bytes parameters
        list(Binary.objects.filter(field__in=["café".encode()]))
        self.assertEqual(len(self.panel._queries), 3)

        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)

        # ensure the panel renders correctly
        self.assertIn("café", self.panel.content)

    @unittest.skipUnless(
        connection.vendor == "postgresql", "Test valid only on PostgreSQL"
    )
    def test_bytes_query(self):
        self.assertEqual(len(self.panel._queries), 0)

        with connection.cursor() as cursor:
            cursor.execute(b"SELECT 1")

        self.assertEqual(len(self.panel._queries), 1)

    def test_param_conversion(self):
        self.assertEqual(len(self.panel._queries), 0)

        list(
            User.objects.filter(first_name="Foo")
            .filter(is_staff=True)
            .filter(is_superuser=False)
        )
        list(
            User.objects.annotate(group_count=Count("groups__id"))
            .filter(group_count__lt=10)
            .filter(group_count__gt=1)
        )
        list(
            User.objects.filter(
                date_joined=datetime.datetime(
                    2017, 12, 22, 16, 7, 1, tzinfo=datetime.timezone.utc
                )
            )
        )

        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)

        # ensure query was logged
        self.assertEqual(len(self.panel._queries), 3)

        if connection.vendor == "mysql" and django.VERSION >= (4, 1):
            # Django 4.1 started passing true/false back for boolean
            # comparisons in MySQL.
            expected_bools = '["Foo", true, false]'
        else:
            expected_bools = '["Foo"]'

        if connection.vendor == "postgresql":
            # PostgreSQL always includes timezone
            expected_datetime = '["2017-12-22 16:07:01+00:00"]'
        else:
            expected_datetime = '["2017-12-22 16:07:01"]'

        self.assertEqual(
            tuple(query["params"] for query in self.panel._queries),
            (
                expected_bools,
                "[10, 1]",
                expected_datetime,
            ),
        )

    @unittest.skipUnless(
        connection.vendor == "postgresql", "Test valid only on PostgreSQL"
    )
    def test_json_param_conversion(self):
        self.assertEqual(len(self.panel._queries), 0)

        list(PostgresJSON.objects.filter(field__contains={"foo": "bar"}))

        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)

        # ensure query was logged
        self.assertEqual(len(self.panel._queries), 1)
        self.assertEqual(
            self.panel._queries[0]["params"],
            '["{\\"foo\\": \\"bar\\"}"]',
        )

    @unittest.skipUnless(
        connection.vendor == "postgresql" and psycopg is None,
        "Test valid only on PostgreSQL with psycopg2",
    )
    def test_tuple_param_conversion(self):
        """
        Regression test for tuple parameter conversion.
        """
        self.assertEqual(len(self.panel._queries), 0)

        list(
            PostgresJSON.objects.raw(
                "SELECT * FROM tests_postgresjson WHERE field ->> 'key' IN %s",
                [("a", "b'")],
            )
        )

        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)

        # ensure query was logged
        self.assertEqual(len(self.panel._queries), 1)
        self.assertEqual(self.panel._queries[0]["params"], '[["a", "b\'"]]')

    def test_binary_param_force_text(self):
        self.assertEqual(len(self.panel._queries), 0)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM tests_binary WHERE field = %s",
                [connection.Database.Binary(b"\xff")],
            )

        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)

        self.assertEqual(len(self.panel._queries), 1)
        self.assertIn(
            "<strong>SELECT</strong> * <strong>FROM</strong>"
            " tests_binary <strong>WHERE</strong> field =",
            self.panel.content,
        )

    @unittest.skipUnless(connection.vendor != "sqlite", "Test invalid for SQLite")
    def test_raw_query_param_conversion(self):
        self.assertEqual(len(self.panel._queries), 0)

        list(
            User.objects.raw(
                " ".join(
                    [
                        "SELECT *",
                        "FROM auth_user",
                        "WHERE first_name = %s",
                        "AND is_staff = %s",
                        "AND is_superuser = %s",
                        "AND date_joined = %s",
                    ]
                ),
                params=["Foo", True, False, datetime.datetime(2017, 12, 22, 16, 7, 1)],
            )
        )

        list(
            User.objects.raw(
                " ".join(
                    [
                        "SELECT *",
                        "FROM auth_user",
                        "WHERE first_name = %(first_name)s",
                        "AND is_staff = %(is_staff)s",
                        "AND is_superuser = %(is_superuser)s",
                        "AND date_joined = %(date_joined)s",
                    ]
                ),
                params={
                    "first_name": "Foo",
                    "is_staff": True,
                    "is_superuser": False,
                    "date_joined": datetime.datetime(2017, 12, 22, 16, 7, 1),
                },
            )
        )

        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)

        # ensure query was logged
        self.assertEqual(len(self.panel._queries), 2)

        self.assertEqual(
            tuple(query["params"] for query in self.panel._queries),
            (
                '["Foo", true, false, "2017-12-22 16:07:01"]',
                " ".join(
                    [
                        '{"first_name": "Foo",',
                        '"is_staff": true,',
                        '"is_superuser": false,',
                        '"date_joined": "2017-12-22 16:07:01"}',
                    ]
                ),
            ),
        )

    def test_insert_content(self):
        """
        Test that the panel only inserts content after generate_stats and
        not the process_request.
        """
        list(User.objects.filter(username="café"))
        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)
        # ensure the panel renders correctly.
        content = self.panel.content
        self.assertIn("café", content)
        self.assertValidHTML(content)

    @override_settings(DEBUG_TOOLBAR_CONFIG={"ENABLE_STACKTRACES_LOCALS": True})
    def test_insert_locals(self):
        """
        Test that the panel inserts locals() content.
        """
        local_var = "<script>alert('test');</script>"  # noqa: F841
        list(User.objects.filter(username="café"))
        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)
        self.assertIn("local_var", self.panel.content)
        # Verify the escape logic works
        content = self.panel.content
        self.assertNotIn("<script>alert", content)
        self.assertIn("&lt;script&gt;alert", content)
        self.assertIn("djdt-locals", content)

    def test_not_insert_locals(self):
        """
        Test that the panel does not insert locals() content.
        """
        list(User.objects.filter(username="café"))
        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)
        self.assertNotIn("djdt-locals", self.panel.content)

    @unittest.skipUnless(
        connection.vendor == "postgresql", "Test valid only on PostgreSQL"
    )
    def test_erroneous_query(self):
        """
        Test that an error in the query isn't swallowed by the middleware.
        """
        try:
            connection.cursor().execute("erroneous query")
        except DatabaseError as e:
            self.assertTrue("erroneous query" in str(e))

    @unittest.skipUnless(
        connection.vendor == "postgresql", "Test valid only on PostgreSQL"
    )
    def test_execute_with_psycopg_composed_sql(self):
        """
        Test command executed using a Composed psycopg object is logged.
        Ref: https://www.psycopg.org/psycopg3/docs/api/sql.html
        """
        try:
            from psycopg import sql
        except ImportError:
            from psycopg2 import sql

        self.assertEqual(len(self.panel._queries), 0)

        with connection.cursor() as cursor:
            command = sql.SQL("select {field} from {table}").format(
                field=sql.Identifier("username"), table=sql.Identifier("auth_user")
            )
            cursor.execute(command)

        self.assertEqual(len(self.panel._queries), 1)

        query = self.panel._queries[0]
        self.assertEqual(query["alias"], "default")
        self.assertTrue("sql" in query)
        self.assertEqual(query["sql"], 'select "username" from "auth_user"')

    def test_disable_stacktraces(self):
        self.assertEqual(len(self.panel._queries), 0)

        with self.settings(DEBUG_TOOLBAR_CONFIG={"ENABLE_STACKTRACES": False}):
            sql_call()

        # ensure query was logged
        self.assertEqual(len(self.panel._queries), 1)
        query = self.panel._queries[0]
        self.assertEqual(query["alias"], "default")
        self.assertTrue("sql" in query)
        self.assertTrue("duration" in query)
        self.assertTrue("stacktrace" in query)

        # ensure the stacktrace is empty
        self.assertEqual([], query["stacktrace"])

    @override_settings(
        DEBUG=True,
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "OPTIONS": {"debug": True, "loaders": ["tests.loaders.LoaderWithSQL"]},
            }
        ],
    )
    def test_regression_infinite_recursion(self):
        """
        Test case for when the template loader runs a SQL query that causes
        an infinite recursion in the SQL panel.
        """
        self.assertEqual(len(self.panel._queries), 0)

        render(self.request, "basic.html", {})

        # Two queries are logged because the loader runs SQL every time a
        # template is loaded and basic.html extends base.html.
        self.assertEqual(len(self.panel._queries), 2)
        query = self.panel._queries[0]
        self.assertEqual(query["alias"], "default")
        self.assertTrue("sql" in query)
        self.assertTrue("duration" in query)
        self.assertTrue("stacktrace" in query)

        # ensure the stacktrace is populated
        self.assertTrue(len(query["stacktrace"]) > 0)

    def test_prettify_sql(self):
        """
        Test case to validate that the PRETTIFY_SQL setting changes the output
        of the sql when it's toggled. It does not validate what it does
        though.
        """
        with override_settings(DEBUG_TOOLBAR_CONFIG={"PRETTIFY_SQL": True}):
            list(User.objects.filter(username__istartswith="spam"))
            response = self.panel.process_request(self.request)
            self.panel.generate_stats(self.request, response)
            # The content formats the sql and prettifies it
            self.assertTrue(self.panel.content)
            pretty_sql = self.panel._queries[-1]["sql"]
            self.assertEqual(len(self.panel._queries), 1)

        # Recreate the panel to reset the queries. Content being a cached_property
        # which doesn't have a way to reset it.
        self.panel.disable_instrumentation()
        self.panel = SQLPanel(self.panel.toolbar, self.panel.get_response)
        self.panel.enable_instrumentation()
        # Run it again, but with prettify off. Verify that it's different.
        with override_settings(DEBUG_TOOLBAR_CONFIG={"PRETTIFY_SQL": False}):
            list(User.objects.filter(username__istartswith="spam"))
            response = self.panel.process_request(self.request)
            self.panel.generate_stats(self.request, response)
            # The content formats the sql and prettifies it
            self.assertTrue(self.panel.content)
            self.assertEqual(len(self.panel._queries), 1)
            self.assertNotIn(pretty_sql, self.panel.content)

        self.panel.disable_instrumentation()
        self.panel = SQLPanel(self.panel.toolbar, self.panel.get_response)
        self.panel.enable_instrumentation()
        # Run it again, but with prettify back on.
        # This is so we don't have to check what PRETTIFY_SQL does exactly,
        # but we know it's doing something.
        with override_settings(DEBUG_TOOLBAR_CONFIG={"PRETTIFY_SQL": True}):
            list(User.objects.filter(username__istartswith="spam"))
            response = self.panel.process_request(self.request)
            self.panel.generate_stats(self.request, response)
            # The content formats the sql and prettifies it
            self.assertTrue(self.panel.content)
            self.assertEqual(len(self.panel._queries), 1)
            self.assertIn(pretty_sql, self.panel.content)

    def test_simplification(self):
        """
        Test case to validate that select lists for .count() and .exist() queries do not
        get elided, but other select lists do.
        """
        User.objects.count()
        User.objects.exists()
        list(User.objects.values_list("id"))
        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)
        # The content formats the sql which injects the ellipsis character
        self.assertTrue(self.panel.content)
        self.assertEqual(len(self.panel._queries), 3)
        self.assertNotIn("\u2022", self.panel._queries[0]["sql"])
        self.assertNotIn("\u2022", self.panel._queries[1]["sql"])
        self.assertIn("\u2022", self.panel._queries[2]["sql"])

    def test_top_level_simplification(self):
        """
        Test case to validate that top-level select lists get elided, but other select
        lists for subselects do not.
        """
        list(User.objects.filter(id__in=User.objects.filter(is_staff=True)))
        list(User.objects.filter(id__lt=20).union(User.objects.filter(id__gt=10)))
        if connection.vendor != "mysql":
            list(
                User.objects.filter(id__lt=20).intersection(
                    User.objects.filter(id__gt=10)
                )
            )
            list(
                User.objects.filter(id__lt=20).difference(
                    User.objects.filter(id__gt=10)
                )
            )
        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)
        # The content formats the sql which injects the ellipsis character
        self.assertTrue(self.panel.content)
        if connection.vendor != "mysql":
            self.assertEqual(len(self.panel._queries), 4)
        else:
            self.assertEqual(len(self.panel._queries), 2)
        # WHERE ... IN SELECT ... queries should have only one elided select list
        self.assertEqual(self.panel._queries[0]["sql"].count("SELECT"), 4)
        self.assertEqual(self.panel._queries[0]["sql"].count("\u2022"), 3)
        # UNION queries should have two elidid select lists
        self.assertEqual(self.panel._queries[1]["sql"].count("SELECT"), 4)
        self.assertEqual(self.panel._queries[1]["sql"].count("\u2022"), 6)
        if connection.vendor != "mysql":
            # INTERSECT queries should have two elidid select lists
            self.assertEqual(self.panel._queries[2]["sql"].count("SELECT"), 4)
            self.assertEqual(self.panel._queries[2]["sql"].count("\u2022"), 6)
            # EXCEPT queries should have two elidid select lists
            self.assertEqual(self.panel._queries[3]["sql"].count("SELECT"), 4)
            self.assertEqual(self.panel._queries[3]["sql"].count("\u2022"), 6)

    @override_settings(
        DEBUG=True,
    )
    def test_flat_template_information(self):
        """
        Test case for when the query is used in a flat template hierarchy
        (without included templates).
        """
        self.assertEqual(len(self.panel._queries), 0)

        users = User.objects.all()
        render(self.request, "sql/flat.html", {"users": users})

        self.assertEqual(len(self.panel._queries), 1)

        query = self.panel._queries[0]
        template_info = query["template_info"]
        template_name = os.path.basename(template_info["name"])
        self.assertEqual(template_name, "flat.html")
        self.assertEqual(template_info["context"][3]["content"].strip(), "{{ users }}")
        self.assertEqual(template_info["context"][3]["highlight"], True)

    @override_settings(
        DEBUG=True,
    )
    def test_nested_template_information(self):
        """
        Test case for when the query is used in a nested template
        hierarchy (with included templates).
        """
        self.assertEqual(len(self.panel._queries), 0)

        users = User.objects.all()
        render(self.request, "sql/nested.html", {"users": users})

        self.assertEqual(len(self.panel._queries), 1)

        query = self.panel._queries[0]
        template_info = query["template_info"]
        template_name = os.path.basename(template_info["name"])
        self.assertEqual(template_name, "included.html")
        self.assertEqual(template_info["context"][0]["content"].strip(), "{{ users }}")
        self.assertEqual(template_info["context"][0]["highlight"], True)

    def test_similar_and_duplicate_grouping(self):
        self.assertEqual(len(self.panel._queries), 0)

        User.objects.filter(id=1).count()
        User.objects.filter(id=1).count()
        User.objects.filter(id=2).count()
        User.objects.filter(id__lt=10).count()
        User.objects.filter(id__lt=20).count()
        User.objects.filter(id__gt=10, id__lt=20).count()

        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)

        self.assertEqual(len(self.panel._queries), 6)

        queries = self.panel._queries
        query = queries[0]
        self.assertEqual(query["similar_count"], 3)
        self.assertEqual(query["duplicate_count"], 2)

        query = queries[1]
        self.assertEqual(query["similar_count"], 3)
        self.assertEqual(query["duplicate_count"], 2)

        query = queries[2]
        self.assertEqual(query["similar_count"], 3)
        self.assertTrue("duplicate_count" not in query)

        query = queries[3]
        self.assertEqual(query["similar_count"], 2)
        self.assertTrue("duplicate_count" not in query)

        query = queries[4]
        self.assertEqual(query["similar_count"], 2)
        self.assertTrue("duplicate_count" not in query)

        query = queries[5]
        self.assertTrue("similar_count" not in query)
        self.assertTrue("duplicate_count" not in query)

        self.assertEqual(queries[0]["similar_color"], queries[1]["similar_color"])
        self.assertEqual(queries[0]["similar_color"], queries[2]["similar_color"])
        self.assertEqual(queries[0]["duplicate_color"], queries[1]["duplicate_color"])
        self.assertNotEqual(queries[0]["similar_color"], queries[0]["duplicate_color"])

        self.assertEqual(queries[3]["similar_color"], queries[4]["similar_color"])
        self.assertNotEqual(queries[0]["similar_color"], queries[3]["similar_color"])
        self.assertNotEqual(queries[0]["duplicate_color"], queries[3]["similar_color"])

    def test_explain_with_union(self):
        list(User.objects.filter(id__lt=20).union(User.objects.filter(id__gt=10)))
        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)
        query = self.panel._queries[0]
        self.assertTrue(query["is_select"])


class SQLPanelMultiDBTestCase(BaseMultiDBTestCase):
    panel_id = SQLPanel.panel_id

    def test_aliases(self):
        self.assertFalse(self.panel._queries)

        list(User.objects.all())
        list(User.objects.using("replica").all())

        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)

        self.assertTrue(self.panel._queries)

        query = self.panel._queries[0]
        self.assertEqual(query["alias"], "default")

        query = self.panel._queries[-1]
        self.assertEqual(query["alias"], "replica")

    def test_transaction_status(self):
        """
        Test case for tracking the transaction status is properly associated with
        queries on PostgreSQL, and that transactions aren't broken on other database
        engines.
        """
        self.assertEqual(len(self.panel._queries), 0)

        with transaction.atomic():
            list(User.objects.all())
            list(User.objects.using("replica").all())

            with transaction.atomic(using="replica"):
                list(User.objects.all())
                list(User.objects.using("replica").all())

        with transaction.atomic():
            list(User.objects.all())

        list(User.objects.using("replica").all())

        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)

        if connection.vendor == "postgresql":
            # Connection tracking is currently only implemented for PostgreSQL.
            self.assertEqual(len(self.panel._queries), 6)

            query = self.panel._queries[0]
            self.assertEqual(query["alias"], "default")
            self.assertIsNotNone(query["trans_id"])
            self.assertTrue(query["starts_trans"])
            self.assertTrue(query["in_trans"])
            self.assertFalse("end_trans" in query)

            query = self.panel._queries[-1]
            self.assertEqual(query["alias"], "replica")
            self.assertIsNone(query["trans_id"])
            self.assertFalse("starts_trans" in query)
            self.assertFalse("in_trans" in query)
            self.assertFalse("end_trans" in query)

            query = self.panel._queries[2]
            self.assertEqual(query["alias"], "default")
            self.assertIsNotNone(query["trans_id"])
            self.assertEqual(query["trans_id"], self.panel._queries[0]["trans_id"])
            self.assertFalse("starts_trans" in query)
            self.assertTrue(query["in_trans"])
            self.assertTrue(query["ends_trans"])

            query = self.panel._queries[3]
            self.assertEqual(query["alias"], "replica")
            self.assertIsNotNone(query["trans_id"])
            self.assertNotEqual(query["trans_id"], self.panel._queries[0]["trans_id"])
            self.assertTrue(query["starts_trans"])
            self.assertTrue(query["in_trans"])
            self.assertTrue(query["ends_trans"])

            query = self.panel._queries[4]
            self.assertEqual(query["alias"], "default")
            self.assertIsNotNone(query["trans_id"])
            self.assertNotEqual(query["trans_id"], self.panel._queries[0]["trans_id"])
            self.assertNotEqual(query["trans_id"], self.panel._queries[3]["trans_id"])
            self.assertTrue(query["starts_trans"])
            self.assertTrue(query["in_trans"])
            self.assertTrue(query["ends_trans"])

            query = self.panel._queries[5]
            self.assertEqual(query["alias"], "replica")
            self.assertIsNone(query["trans_id"])
            self.assertFalse("starts_trans" in query)
            self.assertFalse("in_trans" in query)
            self.assertFalse("end_trans" in query)
        else:
            # Ensure that nothing was recorded for other database engines.
            self.assertTrue(self.panel._queries)
            for query in self.panel._queries:
                self.assertFalse("trans_id" in query)
                self.assertFalse("starts_trans" in query)
                self.assertFalse("in_trans" in query)
                self.assertFalse("end_trans" in query)
