"""
Tests for PostgreSQL compatibility fixes
"""

from django.db import connection
from django.test import TestCase

from debug_toolbar.panels.sql.forms import SQLSelectForm


class PostgreSQLCompatibilityTestCase(TestCase):
    """
    Test that PostgreSQL-specific compatibility issues are handled correctly.
    """

    def test_profiling_only_supported_on_mysql(self):
        """
        Test that profiling raises appropriate error for non-MySQL databases.
        """
        # Skip this test if we're actually using MySQL
        if connection.vendor == "mysql":
            self.skipTest("This test is for non-MySQL databases")

        # Create a form and mock the cleaned_data to test profile method
        form = SQLSelectForm()
        form.cleaned_data = {
            "query": {
                "vendor": connection.vendor,
                "alias": "default",
                "raw_sql": "SELECT 1",
                "params": "[]",
            }
        }

        # Test that profiling raises ValueError for non-MySQL databases
        with self.assertRaises(ValueError) as cm:
            form.profile()

        self.assertIn("Profiling is not supported", str(cm.exception))
        self.assertIn(connection.vendor, str(cm.exception))

    def test_profiling_mysql_check(self):
        """
        Test that profiling only allows MySQL vendor.
        """
        form = SQLSelectForm()

        # Test with PostgreSQL
        form.cleaned_data = {
            "query": {
                "vendor": "postgresql",
                "alias": "default",
                "raw_sql": "SELECT 1",
                "params": "[]",
            }
        }

        with self.assertRaises(ValueError) as cm:
            form.profile()
        self.assertIn("Profiling is not supported for postgresql", str(cm.exception))

        # Test with SQLite
        form.cleaned_data = {
            "query": {
                "vendor": "sqlite",
                "alias": "default",
                "raw_sql": "SELECT 1",
                "params": "[]",
            }
        }

        with self.assertRaises(ValueError) as cm:
            form.profile()
        self.assertIn("Profiling is not supported for sqlite", str(cm.exception))
