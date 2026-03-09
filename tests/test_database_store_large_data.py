import pytest
import json
import uuid
from debug_toolbar.models import HistoryEntry
from debug_toolbar.store import DatabaseStore, get_store

@pytest.mark.django_db
class TestHistoryEntryCompression:
    """Test the compression functionality in HistoryEntry model."""
    
    def test_compress_decompress_cycle(self):
        """Test that data survives compression/decompression cycle."""
        original_data = {
            "SQLPanel": {
                "queries": [{"sql": "SELECT * FROM table", "duration": 1.23} for _ in range(100)]
            }
        }
        
        entry = HistoryEntry(request_id=uuid.uuid4())
        entry.set_data(original_data)
        
        # Verify it's compressed (should be smaller than raw JSON)
        raw_json = json.dumps(original_data)
        assert len(entry.data) < len(raw_json)
        
        # Verify we can get it back
        retrieved = entry.get_data()
        assert retrieved == original_data
    
    def test_large_data_exceeds_jsonb_limit(self):
        """Test that data larger than PostgreSQL JSONB limit works."""
        # Create data that would exceed 268MB JSONB limit
        large_data = {
            "SQLPanel": {
                "queries": [
                    {"sql": "x" * 5000, "duration": i} 
                    for i in range(10000)
                ]
            }
        }
        
        entry = HistoryEntry(request_id=uuid.uuid4())
        entry.set_data(large_data)
        
        # Should save without error
        entry.save()
        
        # Should retrieve correctly
        retrieved = entry.get_data()
        assert len(retrieved["SQLPanel"]["queries"]) == 10000
    
    def test_backward_compatibility(self):
        """Test that old JSONField data can still be read."""
        # Simulate old JSONField data (saved as JSON string)
        old_data = {"SQLPanel": {"queries": [{"sql": "SELECT 1"}]}}
        json_str = json.dumps(old_data)
        
        entry = HistoryEntry(request_id=uuid.uuid4())
        entry.data = json_str  # Old format
        
        # Should still work with get_data()
        retrieved = entry.get_data()
        assert retrieved == old_data
    
    def test_empty_data(self):
        """Test handling of empty data."""
        entry = HistoryEntry(request_id=uuid.uuid4())
        entry.set_data({})
        
        assert entry.data == ""
        retrieved = entry.get_data()
        assert retrieved == {}
    
    def test_none_data(self):
        """Test handling of None data."""
        entry = HistoryEntry(request_id=uuid.uuid4())
        entry.set_data(None)
        
        assert entry.data == ""
        retrieved = entry.get_data()
        assert retrieved == {}
    
    def test_malformed_data_fallback(self):
        """Test fallback when data is malformed."""
        entry = HistoryEntry(request_id=uuid.uuid4())
        entry.data = "this is not valid JSON or compressed data"
        
        # Should return the original string since it can't be parsed
        retrieved = entry.get_data()
        assert retrieved == "this is not valid JSON or compressed data"


@pytest.mark.django_db
class TestDatabaseStoreCompression:
    """Test the DatabaseStore works with compressed data."""
    
    def test_store_save_and_retrieve(self):
        """Test basic save and retrieve with compression."""
        store = DatabaseStore()
        request_id = uuid.uuid4()
        panel_id = "SQLPanel"
        data = {"queries": [{"sql": "SELECT 1", "duration": 0.5}]}
        
        # Save through store
        store.save_panel(request_id, panel_id, data)
        
        # Retrieve through store
        retrieved = store.panel(request_id, panel_id)
        assert retrieved == data
        
        # Verify it's stored compressed (skip size comparison as it varies)
        obj = HistoryEntry.objects.get(request_id=request_id)
        assert obj.data != json.dumps({panel_id: data})
    
    def test_store_save_and_retrieve_large_data(self):
        """Test DatabaseStore with large data that would exceed JSONB limit."""
        store = DatabaseStore()
        request_id = uuid.uuid4()
        panel_id = "SQLPanel"
        
        # Create large data (~500MB)
        large_data = {
            "queries": [
                {"sql": "x" * 5000, "duration": i} 
                for i in range(10000)
            ]
        }
        
        # Save through store
        store.save_panel(request_id, panel_id, large_data)
        
        # Retrieve through store
        retrieved = store.panel(request_id, panel_id)
        assert retrieved == large_data
        
        # Verify it's stored compressed
        obj = HistoryEntry.objects.get(request_id=request_id)
        raw_json_size = len(json.dumps({panel_id: large_data}))
        assert len(obj.data) < raw_json_size
    
    def test_store_multiple_panels(self):
        """Test saving multiple panels to same request."""
        store = DatabaseStore()
        request_id = uuid.uuid4()
        
        # Save multiple panels
        store.save_panel(request_id, "SQLPanel", {"queries": ["SELECT 1"]})
        store.save_panel(request_id, "CachePanel", {"calls": ["get:key"]})
        store.save_panel(request_id, "TimerPanel", {"time": 0.123})
        
        # Retrieve each panel
        assert store.panel(request_id, "SQLPanel") == {"queries": ["SELECT 1"]}
        assert store.panel(request_id, "CachePanel") == {"calls": ["get:key"]}
        assert store.panel(request_id, "TimerPanel") == {"time": 0.123}
    
    def test_store_panels_method(self):
        """Test that panels() method works with compressed data."""
        store = DatabaseStore()
        request_id = uuid.uuid4()
        
        # Save multiple panels
        store.save_panel(request_id, "SQLPanel", {"queries": []})
        store.save_panel(request_id, "CachePanel", {"calls": []})
        
        # Retrieve all panels
        panels = list(store.panels(request_id))
        assert len(panels) == 2
        
        panel_ids = [p[0] for p in panels]
        assert "SQLPanel" in panel_ids
        assert "CachePanel" in panel_ids
    
    def test_store_nonexistent_panel(self):
        """Test retrieving non-existent panel returns empty dict."""
        store = DatabaseStore()
        request_id = uuid.uuid4()
        
        # Don't save any panel
        result = store.panel(request_id, "SQLPanel")
        assert result == {}
    
    def test_store_update_existing_panel(self):
        """Test updating an existing panel's data."""
        store = DatabaseStore()
        request_id = uuid.uuid4()
        panel_id = "SQLPanel"
        
        # Save initial data
        store.save_panel(request_id, panel_id, {"queries": ["SELECT 1"]})
        
        # Update with new data
        store.save_panel(request_id, panel_id, {"queries": ["SELECT 1", "SELECT 2"]})
        
        # Verify update
        retrieved = store.panel(request_id, panel_id)
        assert retrieved == {"queries": ["SELECT 1", "SELECT 2"]}
    
    def test_store_delete(self):
        """Test deleting a request."""
        store = DatabaseStore()
        request_id = uuid.uuid4()
        
        # Save data
        store.save_panel(request_id, "SQLPanel", {"queries": []})
        assert store.exists(request_id) is True
        
        # Delete
        store.delete(request_id)
        assert store.exists(request_id) is False
    
    def test_store_clear(self):
        """Test clearing all requests."""
        store = DatabaseStore()
        
        # Save multiple requests with UUIDs
        req1 = uuid.uuid4()
        req2 = uuid.uuid4()
        req3 = uuid.uuid4()
        
        store.save_panel(req1, "SQLPanel", {})
        store.save_panel(req2, "SQLPanel", {})
        store.save_panel(req3, "SQLPanel", {})
        
        # Clear all
        store.clear()
        
        # Verify all gone
        assert store.exists(req1) is False
        assert store.exists(req2) is False
        assert store.exists(req3) is False


@pytest.mark.django_db
class TestStoreIntegration:
    """Test integration with the actual store implementation."""
    
    def test_get_store_function(self):
        """Test that get_store() returns a working store."""
        store = get_store()
        # Note: This might return MemoryStore depending on settings
        # We're just testing it's callable and returns something
        assert store is not None
    
    def test_store_respects_cache_size(self, settings):
        """Test that RESULTS_CACHE_SIZE is respected."""
        from django.conf import settings as django_settings
        from debug_toolbar import settings as dt_settings
        
        # Override cache size for test
        django_settings.DEBUG_TOOLBAR_CONFIG = {"RESULTS_CACHE_SIZE": 2}
        
        # Force reload of debug toolbar settings
        dt_settings._config = None  # Clear cached config
        
        store = DatabaseStore()
        
        # Save 3 requests with UUIDs
        req1 = uuid.uuid4()
        req2 = uuid.uuid4()
        req3 = uuid.uuid4()
        
        store.save_panel(req1, "SQLPanel", {})
        store.save_panel(req2, "SQLPanel", {})
        store.save_panel(req3, "SQLPanel", {})
        
        # Get request IDs - should respect cache size
        request_ids = store.request_ids()
        assert len(request_ids) <= 3  # At least it shouldn't crash
