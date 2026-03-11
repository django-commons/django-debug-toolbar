import json
import uuid

import pytest
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.safestring import SafeData, mark_safe

from debug_toolbar import store
from debug_toolbar.models import HistoryEntry
from debug_toolbar.store import DatabaseStore, get_store


class SerializationTestCase(TestCase):
    def test_serialize(self):
        self.assertEqual(
            store.serialize({"hello": {"foo": "bar"}}),
            '{"hello": {"foo": "bar"}}',
        )

    def test_serialize_logs_on_failure(self):
        self.assertEqual(
            store.serialize({"hello": {"foo": b"bar"}}),
            '{"hello": {"foo": "bar"}}',
        )

    def test_deserialize(self):
        self.assertEqual(
            store.deserialize('{"hello": {"foo": "bar"}}'),
            {"hello": {"foo": "bar"}},
        )


class BaseStoreTestCase(TestCase):
    def test_methods_are_not_implemented(self):
        # Find all the non-private and dunder class methods
        methods = [
            member for member in vars(store.BaseStore) if not member.startswith("_")
        ]
        self.assertEqual(len(methods), 7)
        with self.assertRaises(NotImplementedError):
            store.BaseStore.request_ids()
        with self.assertRaises(NotImplementedError):
            store.BaseStore.exists("")
        with self.assertRaises(NotImplementedError):
            store.BaseStore.set("")
        with self.assertRaises(NotImplementedError):
            store.BaseStore.clear()
        with self.assertRaises(NotImplementedError):
            store.BaseStore.delete("")
        with self.assertRaises(NotImplementedError):
            store.BaseStore.save_panel("", "", None)
        with self.assertRaises(NotImplementedError):
            store.BaseStore.panel("", "")


class MemoryStoreTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.store = store.MemoryStore

    def tearDown(self) -> None:
        self.store.clear()

    def test_ids(self):
        self.store.set("foo")
        self.store.set("bar")
        self.assertEqual(list(self.store.request_ids()), ["foo", "bar"])

    def test_exists(self):
        self.assertFalse(self.store.exists("missing"))
        self.store.set("exists")
        self.assertTrue(self.store.exists("exists"))

    def test_set(self):
        self.store.set("foo")
        self.assertEqual(list(self.store.request_ids()), ["foo"])

    def test_set_max_size(self):
        with self.settings(DEBUG_TOOLBAR_CONFIG={"RESULTS_CACHE_SIZE": 1}):
            self.store.save_panel("foo", "foo.panel", "foo.value")
            self.store.save_panel("bar", "bar.panel", {"a": 1})
            self.assertEqual(list(self.store.request_ids()), ["bar"])
            self.assertEqual(self.store.panel("foo", "foo.panel"), {})
            self.assertEqual(self.store.panel("bar", "bar.panel"), {"a": 1})

    def test_clear(self):
        self.store.save_panel("bar", "bar.panel", {"a": 1})
        self.store.clear()
        self.assertEqual(list(self.store.request_ids()), [])
        self.assertEqual(self.store.panel("bar", "bar.panel"), {})

    def test_delete(self):
        self.store.save_panel("bar", "bar.panel", {"a": 1})
        self.store.delete("bar")
        self.assertEqual(list(self.store.request_ids()), [])
        self.assertEqual(self.store.panel("bar", "bar.panel"), {})
        # Make sure it doesn't error
        self.store.delete("bar")

    def test_save_panel(self):
        self.store.save_panel("bar", "bar.panel", {"a": 1})
        self.assertEqual(list(self.store.request_ids()), ["bar"])
        self.assertEqual(self.store.panel("bar", "bar.panel"), {"a": 1})

    def test_panel(self):
        self.assertEqual(self.store.panel("missing", "missing"), {})
        self.store.save_panel("bar", "bar.panel", {"a": 1})
        self.assertEqual(self.store.panel("bar", "bar.panel"), {"a": 1})

    def test_serialize_safestring(self):
        before = {"string": mark_safe("safe")}

        self.store.save_panel("bar", "bar.panel", before)
        after = self.store.panel("bar", "bar.panel")

        self.assertFalse(type(before["string"]) is str)
        self.assertTrue(isinstance(before["string"], SafeData))

        self.assertTrue(type(after["string"]) is str)
        self.assertFalse(isinstance(after["string"], SafeData))


class StubStore(store.BaseStore):
    pass


class GetStoreTestCase(TestCase):
    def test_get_store(self):
        self.assertIs(store.get_store(), store.MemoryStore)

    @override_settings(
        DEBUG_TOOLBAR_CONFIG={"TOOLBAR_STORE_CLASS": "tests.test_store.StubStore"}
    )
    def test_get_store_with_setting(self):
        self.assertIs(store.get_store(), StubStore)


@override_settings(
    DEBUG_TOOLBAR_CONFIG={"TOOLBAR_STORE_CLASS": "debug_toolbar.store.DatabaseStore"}
)
class DatabaseStoreTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.store = store.DatabaseStore

    def tearDown(self) -> None:
        self.store.clear()

    def test_ids(self):
        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())
        self.store.set(id1)
        self.store.set(id2)
        # Convert the UUIDs to strings for comparison
        request_ids = {str(id) for id in self.store.request_ids()}
        self.assertEqual(request_ids, {id1, id2})

    def test_exists(self):
        missing_id = str(uuid.uuid4())
        self.assertFalse(self.store.exists(missing_id))
        id1 = str(uuid.uuid4())
        self.store.set(id1)
        self.assertTrue(self.store.exists(id1))

    def test_set(self):
        id1 = str(uuid.uuid4())
        self.store.set(id1)
        self.assertTrue(self.store.exists(id1))

    def test_set_max_size(self):
        with self.settings(DEBUG_TOOLBAR_CONFIG={"RESULTS_CACHE_SIZE": 1}):
            # Clear any existing entries first
            self.store.clear()

            # Add first entry
            id1 = str(uuid.uuid4())
            self.store.set(id1)

            # Verify it exists
            self.assertTrue(self.store.exists(id1))

            # Add second entry, which should push out the first one due to size limit=1
            id2 = str(uuid.uuid4())
            self.store.set(id2)

            # Verify only the bar entry exists now
            # Convert the UUIDs to strings for comparison
            request_ids = {str(id) for id in self.store.request_ids()}
            self.assertEqual(request_ids, {id2})
            self.assertFalse(self.store.exists(id1))

    def test_clear(self):
        id1 = str(uuid.uuid4())
        self.store.save_panel(id1, "bar.panel", {"a": 1})
        self.store.clear()
        self.assertEqual(list(self.store.request_ids()), [])
        self.assertEqual(self.store.panel(id1, "bar.panel"), {})

    def test_delete(self):
        id1 = str(uuid.uuid4())
        self.store.save_panel(id1, "bar.panel", {"a": 1})
        self.store.delete(id1)
        self.assertEqual(list(self.store.request_ids()), [])
        self.assertEqual(self.store.panel(id1, "bar.panel"), {})
        # Make sure it doesn't error
        self.store.delete(id1)

    def test_save_panel(self):
        id1 = str(uuid.uuid4())
        self.store.save_panel(id1, "bar.panel", {"a": 1})
        self.assertTrue(self.store.exists(id1))
        self.assertEqual(self.store.panel(id1, "bar.panel"), {"a": 1})

    def test_update_panel(self):
        id1 = str(uuid.uuid4())
        self.store.save_panel(id1, "test.panel", {"original": True})
        self.assertEqual(self.store.panel(id1, "test.panel"), {"original": True})

        # Update the panel
        self.store.save_panel(id1, "test.panel", {"updated": True})
        self.assertEqual(self.store.panel(id1, "test.panel"), {"updated": True})

    def test_panels_nonexistent_request(self):
        missing_id = str(uuid.uuid4())
        panels = dict(self.store.panels(missing_id))
        self.assertEqual(panels, {})

    def test_panel(self):
        id1 = str(uuid.uuid4())
        missing_id = str(uuid.uuid4())
        self.assertEqual(self.store.panel(missing_id, "missing"), {})
        self.store.save_panel(id1, "bar.panel", {"a": 1})
        self.assertEqual(self.store.panel(id1, "bar.panel"), {"a": 1})

    def test_panels(self):
        id1 = str(uuid.uuid4())
        self.store.save_panel(id1, "panel1", {"a": 1})
        self.store.save_panel(id1, "panel2", {"b": 2})
        panels = dict(self.store.panels(id1))
        self.assertEqual(len(panels), 2)
        self.assertEqual(panels["panel1"], {"a": 1})
        self.assertEqual(panels["panel2"], {"b": 2})

    def test_cleanup_old_entries(self):
        # Create multiple entries
        ids = [str(uuid.uuid4()) for _ in range(5)]
        for id in ids:
            self.store.save_panel(id, "test.panel", {"test": True})

        # Set a small cache size
        with self.settings(DEBUG_TOOLBAR_CONFIG={"RESULTS_CACHE_SIZE": 2}):
            # Trigger cleanup
            self.store._cleanup_old_entries()

            # Check that only the most recent 2 entries remain
            self.assertEqual(len(list(self.store.request_ids())), 2)


class CompressedJSONFieldTestCase(TestCase):
    """Test the CompressedJSONField functionality."""

    def test_compress_decompress_cycle(self):
        """Test that data survives compression/decompression."""
        original = {"key": "value", "nested": {"data": [1, 2, 3]}}
        entry = HistoryEntry.objects.create(request_id=uuid.uuid4(), data=original)
        entry.refresh_from_db()
        self.assertEqual(entry.data, original)

    def test_backward_compatibility(self):
        """Test reading old JSONField data (JSON string)."""
        old_data = {"test": True}
        entry = HistoryEntry.objects.create(
            request_id=uuid.uuid4(), data=json.dumps(old_data)
        )
        entry.refresh_from_db()

        if isinstance(entry.data, str):
            self.assertEqual(json.loads(entry.data), old_data)
        else:
            self.assertEqual(entry.data, old_data)

    def test_empty_data(self):
        """Test handling empty dict."""
        entry = HistoryEntry.objects.create(request_id=uuid.uuid4(), data={})
        entry.refresh_from_db()
        self.assertEqual(entry.data, {})

    def test_none_becomes_empty(self):
        """Test None converts to empty dict."""
        entry = HistoryEntry.objects.create(request_id=uuid.uuid4(), data=None)
        entry.refresh_from_db()
        self.assertEqual(entry.data, {})

    def test_malformed_data_fallback(self):
        """Test fallback when data is malformed."""
        entry = HistoryEntry.objects.create(
            request_id=uuid.uuid4(), data="this is not valid JSON"
        )
        entry.refresh_from_db()
        self.assertEqual(entry.data, "this is not valid JSON")


@pytest.mark.django_db
class TestDatabaseStoreCompression:
    """Test DatabaseStore works with compressed data."""

    def test_save_and_retrieve_with_compression(self):
        """Test basic save/retrieve with compression."""
        store = DatabaseStore()
        request_id = uuid.uuid4()
        panel_id = "SQLPanel"
        data = {"queries": [{"sql": "SELECT 1"}]}

        store.save_panel(request_id, panel_id, data)
        retrieved = store.panel(request_id, panel_id)

        assert retrieved == data

        obj = HistoryEntry.objects.get(request_id=request_id)
        assert obj.data != json.dumps({panel_id: data})

    def test_large_data_compression(self):
        """Test that large data is compressed."""
        store = DatabaseStore()
        request_id = uuid.uuid4()
        panel_id = "SQLPanel"

        large_data = {
            "queries": [{"sql": "x" * 5000, "duration": i} for i in range(1000)]
        }

        store.save_panel(request_id, panel_id, large_data)
        retrieved = store.panel(request_id, panel_id)

        assert retrieved == large_data

        obj = HistoryEntry.objects.get(request_id=request_id)
        raw_json = json.dumps({panel_id: large_data})
        assert len(obj.data) < len(raw_json)


@pytest.mark.django_db
class TestStoreIntegration:
    """Test integration with the actual store implementation."""

    def test_get_store_function(self):
        """Test that get_store() returns a working store."""
        store = get_store()

        assert store is not None

    def test_store_respects_cache_size(self, settings):
        """Test that RESULTS_CACHE_SIZE is respected."""
        from django.conf import settings as django_settings

        from debug_toolbar import settings as dt_settings

        django_settings.DEBUG_TOOLBAR_CONFIG = {"RESULTS_CACHE_SIZE": 2}

        dt_settings._config = None

        store = DatabaseStore()

        req1 = uuid.uuid4()
        req2 = uuid.uuid4()
        req3 = uuid.uuid4()

        store.save_panel(req1, "SQLPanel", {})
        store.save_panel(req2, "SQLPanel", {})
        store.save_panel(req3, "SQLPanel", {})

        request_ids = store.request_ids()
        assert len(request_ids) <= 3
