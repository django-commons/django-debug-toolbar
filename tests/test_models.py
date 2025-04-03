import uuid

from django.test import TestCase

from debug_toolbar.models import DebugToolbarEntry


class DebugToolbarEntryTestCase(TestCase):
    def test_str_method(self):
        test_uuid = uuid.uuid4()
        entry = DebugToolbarEntry(request_id=test_uuid)
        self.assertEqual(str(entry), str(test_uuid))

    def test_data_field_default(self):
        """Test that the data field defaults to an empty dict"""
        entry = DebugToolbarEntry(request_id=uuid.uuid4())
        self.assertEqual(entry.data, {})

    def test_model_persistence(self):
        """Test saving and retrieving a model instance"""
        test_uuid = uuid.uuid4()
        entry = DebugToolbarEntry(request_id=test_uuid, data={"test": True})
        entry.save()

        # Retrieve from database and verify
        saved_entry = DebugToolbarEntry.objects.get(request_id=test_uuid)
        self.assertEqual(saved_entry.data, {"test": True})
        self.assertEqual(str(saved_entry), str(test_uuid))
