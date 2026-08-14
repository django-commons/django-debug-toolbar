import unittest
from unittest.mock import MagicMock, PropertyMock, patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError, connection
from django.test import SimpleTestCase, TestCase

from debug_toolbar.panels.sql.forms import SQLSelectForm
from debug_toolbar.panels.sql.oracle_helper import OracleExplainPlanHelper


def _make_mock_explain_form(raw_sql, params=None, duration=1.0):
    """
    Utility factory helper to construct SQLSelectForm with pre-filled cleaned_data
    to minimize redundant boilerplate across test cases.
    """
    form = SQLSelectForm(data={})
    form.cleaned_data = {
        "request_id": "test_request",
        "djdt_query_id": "test_query",
        "alias": "default",
        "query": {
            "raw_sql": raw_sql,
            "params": params or [],
            "vendor": "oracle",
            "sql": raw_sql,
            "duration": duration,
            "alias": "default",
        },
    }
    return form


@unittest.skipUnless(connection.vendor == "oracle", "Test valid only on Oracle")
class OracleExplainTestCase(TestCase):
    """
    Tests the refined Oracle explain plan support in SQLSelectForm.
    """

    def test_oracle_explain_success(self):
        User = get_user_model()
        User.objects.get_or_create(username="explain_test_user")

        form = _make_mock_explain_form(
            raw_sql="SELECT * FROM auth_user WHERE username = %s",
            params=["explain_test_user"],
        )

        result, headers = form.explain()

        self.assertEqual(headers, ["PLAN_TABLE_OUTPUT"])

        flat_result = [row[0] for row in result if row and row[0] is not None]

        self.assertTrue(
            any(
                "Plan hash value" in line or "Id" in line or "PLAN_TABLE_OUTPUT" in line
                for line in flat_result
            ),
            f"Expected DBMS_XPLAN structure not found in: {flat_result}",
        )

        self.assertTrue(
            any("Schema Health & Statistics Audit" in line for line in flat_result)
        )
        self.assertTrue(any("Table Statistics:" in line for line in flat_result))

    @patch("debug_toolbar.panels.sql.forms.connections")
    def test_oracle_explain_graceful_fallback_on_catalog_error(self, mock_connections):
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value = mock_connection

        mock_cursor.fetchall.side_effect = [
            [("Plan line 1",), ("Plan line 2",)],
            DatabaseError("Access Denied to PLAN_TABLE"),
        ]
        mock_cursor.description = [("PLAN_TABLE_OUTPUT",)]

        form = _make_mock_explain_form(
            raw_sql="SELECT * FROM employees",
            duration=10.0,
        )

        result, headers = form.explain()

        self.assertEqual(headers, ["PLAN_TABLE_OUTPUT"])
        self.assertEqual(result, [("Plan line 1",), ("Plan line 2",)])

        calls = mock_cursor.execute.call_args_list
        cleanup_sql = calls[-1][0][0]
        self.assertEqual(cleanup_sql, "DELETE FROM PLAN_TABLE WHERE statement_id = %s")

    def test_oracle_explain_suppress_query_block_registry(self):
        User = get_user_model()
        User.objects.get_or_create(username="explain_test_user")

        form = _make_mock_explain_form(
            raw_sql="SELECT * FROM auth_user WHERE username = %s",
            params=["explain_test_user"],
        )

        with patch.object(
            OracleExplainPlanHelper, "_oracle_version", new_callable=PropertyMock
        ) as mock_version:
            mock_version.return_value = (19,)
            result, _ = form.explain()

        flat_result = [row[0] for row in result if row and row[0] is not None]

        self.assertNotIn("Query Block Registry:", flat_result)

        self.assertTrue(
            any("Schema Health & Statistics Audit" in line for line in flat_result)
        )
        self.assertTrue(any("Table Statistics:" in line for line in flat_result))

    @patch("debug_toolbar.panels.sql.forms.connections")
    def test_oracle_explain_null_owner_mapping(self, mock_connections):
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value = mock_connection

        mock_cursor.connection = MagicMock()
        mock_cursor.connection.username = "scott"

        mock_cursor.fetchall.side_effect = [
            [("Plan line 1",)],
            [(None, "EMPLOYEES")],
            [],
            [("SCOTT", "EMPLOYEES", 500, 10, 50, "2026-08-07 12:00:00")],
            [],
        ]
        mock_cursor.description = [("PLAN_TABLE_OUTPUT",)]

        form = _make_mock_explain_form(
            raw_sql="SELECT * FROM employees",
            duration=10.0,
        )

        result, _ = form.explain()
        flat_result = [row[0] for row in result]

        self.assertTrue(any("SCOTT" in line for line in flat_result))
        self.assertTrue(any("EMPLOYEES" in line for line in flat_result))

    def test_oracle_explain_custom_settings(self):
        User = get_user_model()
        User.objects.get_or_create(username="explain_test_user")

        form = _make_mock_explain_form(
            raw_sql="SELECT * FROM auth_user WHERE username = %s",
            params=["explain_test_user"],
        )

        with patch.object(OracleExplainPlanHelper, "include_catalog_audit", new=False):
            result, _ = form.explain()

        flat_result = [row[0] for row in result if row and row[0] is not None]

        self.assertFalse(
            any("Schema Health & Statistics Audit" in line for line in flat_result)
        )

    @patch("debug_toolbar.panels.sql.forms.connections")
    def test_oracle_explain_cleanup_plan_table_error(self, mock_connections):
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value = mock_connection

        mock_cursor.fetchall.side_effect = [
            [("Plan line 1",)],
            [],
            [],
        ]

        def execute_side_effect(sql, params=None):
            if "DELETE FROM PLAN_TABLE" in sql:
                raise DatabaseError("Mocked DELETE error")
            return MagicMock()

        mock_cursor.execute.side_effect = execute_side_effect
        mock_cursor.description = [("PLAN_TABLE_OUTPUT",)]

        form = _make_mock_explain_form(
            raw_sql="SELECT * FROM employees",
            duration=10.0,
        )

        with self.assertLogs(
            "debug_toolbar.panels.sql.oracle_helper", level="WARNING"
        ) as cm:
            result, headers = form.explain()

        self.assertEqual(headers, ["PLAN_TABLE_OUTPUT"])
        self.assertEqual(result, [("Plan line 1",)])
        self.assertTrue(
            any("Failed to clean up PLAN_TABLE" in log for log in cm.output)
        )


class OracleExplainPlanHelperUnitTestCase(SimpleTestCase):
    """
    Pure unit tests for OracleExplainPlanHelper independent logic.
    These tests are database-independent and run natively on any environment (e.g. SQLite).
    """

    def test_suppress_qbr_with_audit_present(self):

        helper = OracleExplainPlanHelper(cursor=None)
        raw_result = [
            ("SELECT * FROM employees",),
            ("Query Block Registry:",),
            ("---------------------",),
            ('  <q o="19"><n>SEL$1</n></q>',),
            ("Schema Health & Statistics Audit (ALL_TABLES & ALL_INDEXES)",),
            ("Table Statistics:",),
        ]

        filtered = helper._suppress_qbr(raw_result)
        flat_filtered = [row[0] for row in filtered]

        self.assertEqual(
            flat_filtered,
            [
                "SELECT * FROM employees",
                "Schema Health & Statistics Audit (ALL_TABLES & ALL_INDEXES)",
                "Table Statistics:",
            ],
        )

    def test_suppress_qbr_without_audit_present(self):

        helper = OracleExplainPlanHelper(cursor=None)
        raw_result = [
            ("SELECT * FROM employees",),
            ("Query Block Registry:",),
            ("---------------------",),
            ('  <q o="19"><n>SEL$1</n></q>',),
        ]

        filtered = helper._suppress_qbr(raw_result)
        flat_filtered = [row[0] for row in filtered]

        self.assertEqual(flat_filtered, ["SELECT * FROM employees"])

    def test_suppress_qbr_no_qbr_present(self):

        helper = OracleExplainPlanHelper(cursor=None)
        raw_result = [
            ("SELECT * FROM employees",),
            ("Plan line 2",),
        ]

        filtered = helper._suppress_qbr(raw_result)
        self.assertEqual(filtered, raw_result)

    def test_suppress_qbr_with_note_and_audit_present(self):

        helper = OracleExplainPlanHelper(cursor=None)
        raw_result = [
            ("SELECT * FROM employees",),
            ("Note",),
            ("-----",),
            ("  - dynamic sampling used",),
            ("Query Block Registry:",),
            ("---------------------",),
            ('  <q o="19"><n>SEL$1</n></q>',),
            ("Schema Health & Statistics Audit (ALL_TABLES & ALL_INDEXES)",),
            ("Table Statistics:",),
        ]

        filtered = helper._suppress_qbr(raw_result)
        flat_filtered = [row[0] for row in filtered]

        self.assertEqual(
            flat_filtered,
            [
                "SELECT * FROM employees",
                "Note",
                "-----",
                "  - dynamic sampling used",
                "Schema Health & Statistics Audit (ALL_TABLES & ALL_INDEXES)",
                "Table Statistics:",
            ],
        )

    def test_render_stats_as_ascii_empty_inputs(self):

        helper = OracleExplainPlanHelper(cursor=None)
        lines = helper._render_stats_as_ascii([], [])
        self.assertEqual(lines, [])

    def test_get_involved_tables_without_cursor_connection_metadata(self):
        """
        Cover fallback paths for cursors that don't expose the wrapped driver
        connection metadata and for index mappings without table names. Django's
        Oracle cursor exposes metadata, but the helper is defensive.
        """

        class CursorWithoutConnectionMetadata:
            cursor = object()

            def __init__(self):
                self.calls = 0

            def execute(self, sql, params):
                self.calls += 1

            def fetchall(self):
                if self.calls == 1:
                    return [("DEFAULT_TEST", "AUTH_USER"), (None, None)]
                if self.calls == 2:
                    return [("DEFAULT_TEST", "AUTH_USER_USERNAME_IDX")]
                return [("DEFAULT_TEST", None)]

        helper = OracleExplainPlanHelper(CursorWithoutConnectionMetadata())
        self.assertEqual(
            helper._get_involved_tables("stmt"), {("DEFAULT_TEST", "AUTH_USER")}
        )


@unittest.skipUnless(connection.vendor == "oracle", "Test valid only on Oracle")
class OracleExplainPlanHelperDBTestCase(TestCase):
    """
    Database-dependent integration tests for OracleExplainPlanHelper.
    Requires a running Oracle database.
    """

    def test_get_involved_tables_reverse_maps_index_to_table(self):
        """
        Exercise the real Oracle PLAN_TABLE -> ALL_INDEXES reverse mapping.

        Oracle execution plans can contain only index nodes for indexed lookups.
        The helper must map those indexes back to their parent tables so the
        catalog audit still reports table statistics.
        """

        get_user_model().objects.get_or_create(username="indexed_plan_user")

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT owner, index_name, table_owner, table_name "
                "FROM all_indexes "
                "WHERE table_owner = USER "
                "AND table_name = %s "
                "AND ROWNUM = 1",
                [get_user_model()._meta.db_table.upper()],
            )
            index_row = cursor.fetchone()
            self.assertIsNotNone(index_row)
            index_owner, index_name, table_owner, table_name = index_row

            stmt_id = "dt_test_index_mapping"
            cursor.execute("DELETE FROM PLAN_TABLE WHERE statement_id = %s", [stmt_id])
            try:
                cursor.execute(
                    "INSERT INTO PLAN_TABLE "
                    "(statement_id, object_owner, object_name, object_type) "
                    "VALUES (%s, %s, %s, %s)",
                    [stmt_id, index_owner, index_name, "INDEX"],
                )

                helper = OracleExplainPlanHelper(cursor)
                table_keys = helper._get_involved_tables(stmt_id)

                self.assertIn((table_owner, table_name), table_keys)
            finally:
                cursor.execute(
                    "DELETE FROM PLAN_TABLE WHERE statement_id = %s", [stmt_id]
                )
