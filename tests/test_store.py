import uuid

from django.test import TestCase
from django.test.utils import override_settings
from django.utils.safestring import SafeData, mark_safe

from debug_toolbar import store


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
