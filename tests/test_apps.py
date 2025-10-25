from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from debug_toolbar.apps import _manage_migrations_visibility


class AppsTestCase(SimpleTestCase):
    @override_settings(
        DEBUG_TOOLBAR_CONFIG={
            "TOOLBAR_STORE_CLASS": "debug_toolbar.store.DatabaseStore"
        }
    )
    @patch("debug_toolbar.apps.settings.MIGRATION_MODULES")
    def test_migrations_are_visible(self, mocked_migration_modules):
        _manage_migrations_visibility("debug_toolbar")
        self.assertFalse(mocked_migration_modules.setdefault.called)

    @override_settings(
        DEBUG_TOOLBAR_CONFIG={"TOOLBAR_STORE_CLASS": "debug_toolbar.store.MemoryStore"}
    )
    @patch("debug_toolbar.apps.settings.MIGRATION_MODULES")
    def test_migrations_are_hidden(self, mocked_migration_modules):
        _manage_migrations_visibility("debug_toolbar")
        mocked_migration_modules.setdefault.assert_called_once_with(
            "debug_toolbar", None
        )
