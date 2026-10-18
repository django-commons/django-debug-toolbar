import importlib
import uuid

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings

import debug_toolbar.models
from debug_toolbar.models import HistoryEntry


class HistoryEntryTestCase(TestCase):
    def test_str_method(self):
        test_uuid = uuid.uuid4()
        entry = HistoryEntry(request_id=test_uuid)
        self.assertEqual(str(entry), str(test_uuid))

    def test_data_field_default(self):
        """Test that the data field defaults to an empty dict"""
        entry = HistoryEntry(request_id=uuid.uuid4())
        self.assertEqual(entry.data, {})

    def test_model_persistence(self):
        """Test saving and retrieving a model instance"""
        test_uuid = uuid.uuid4()
        entry = HistoryEntry(request_id=test_uuid, data={"test": True})
        entry.save()

        # Retrieve from database and verify
        saved_entry = HistoryEntry.objects.get(request_id=test_uuid)
        self.assertEqual(saved_entry.data, {"test": True})
        self.assertEqual(str(saved_entry), str(test_uuid))

    def test_default_ordering(self):
        """Test that the default ordering is by created_at in descending order"""
        self.assertEqual(HistoryEntry._meta.ordering, ["-created_at"])


class NotInstalledTestCase(SimpleTestCase):
    @override_settings(
        INSTALLED_APPS=[
            app for app in settings.INSTALLED_APPS if app != "debug_toolbar"
        ]
    )
    def test_import_without_app_installed_names_the_setting(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured, "requires 'debug_toolbar' in INSTALLED_APPS"
        ):
            importlib.reload(debug_toolbar.models)
