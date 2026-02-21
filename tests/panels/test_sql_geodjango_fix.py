"""
Tests for GeoDjango binary parameter handling fix

These tests verify that binary data (such as GeoDjango EWKB geometry data)
is properly encoded and decoded through the Store's serialize/deserialize
functions using DebugToolbarJSONEncoder and DebugToolbarJSONDecoder.
"""

from debug_toolbar.store import deserialize, serialize

from ..base import BaseTestCase


class GeoDjangoBinaryParameterTest(BaseTestCase):
    """Test cases for GeoDjango binary parameter handling"""

    def test_binary_parameter_encoding_decoding(self):
        """Test that binary parameters are properly encoded and decoded through the store"""
        # Test binary data similar to GeoDjango EWKB geometry
        binary_data = b"\x01\x01\x00\x00\x20\xe6\x10\x00\x00\xff\xfe\xfd"
        params = {"geometry": binary_data, "name": "Point A"}

        # Serialize through the store (simulating storage)
        serialized = serialize(params)

        # Deserialize through the store (simulating retrieval)
        reconstructed = deserialize(serialized)

        # Verify the binary data is reconstructed correctly
        self.assertEqual(reconstructed["geometry"], binary_data)
        self.assertIsInstance(reconstructed["geometry"], bytes)
        self.assertEqual(reconstructed["name"], "Point A")

    def test_mixed_parameter_types(self):
        """Test that mixed parameter types are handled correctly through the store"""
        params = {
            "text": "string_param",
            "count": 42,
            "geometry": b"\x01\x02\x03",
            "optional": None,
            "tags": ["tag1", "tag2"],
        }

        # Serialize and deserialize through the store
        serialized = serialize(params)
        reconstructed = deserialize(serialized)

        # Verify all types are preserved correctly
        self.assertEqual(reconstructed["text"], "string_param")
        self.assertEqual(reconstructed["count"], 42)
        self.assertEqual(reconstructed["geometry"], b"\x01\x02\x03")
        self.assertIsNone(reconstructed["optional"])
        self.assertEqual(reconstructed["tags"], ["tag1", "tag2"])

    def test_nested_binary_data(self):
        """Test binary data nested in lists and dicts through the store"""
        params = {
            "geometries": [b"\x01\x02", b"\x03\x04"],
            "metadata": {"shape": b"\x05\x06", "description": "Polygon"},
        }

        # Serialize and deserialize through the store
        serialized = serialize(params)
        reconstructed = deserialize(serialized)

        # Verify nested binary data is reconstructed correctly
        self.assertEqual(reconstructed["geometries"][0], b"\x01\x02")
        self.assertEqual(reconstructed["geometries"][1], b"\x03\x04")
        self.assertEqual(reconstructed["metadata"]["shape"], b"\x05\x06")
        self.assertEqual(reconstructed["metadata"]["description"], "Polygon")

    def test_empty_binary_data(self):
        """Test handling of empty binary data through the store"""
        params = {"empty_geometry": b"", "name": "Empty"}

        # Serialize and deserialize through the store
        serialized = serialize(params)
        reconstructed = deserialize(serialized)

        # Verify empty binary data is handled correctly
        self.assertEqual(reconstructed["empty_geometry"], b"")
        self.assertIsInstance(reconstructed["empty_geometry"], bytes)
        self.assertEqual(reconstructed["name"], "Empty")

    def test_bytearray_support(self):
        """Test that bytearray is also handled as binary data through the store"""
        byte_array = bytearray(b"\x01\x02\x03\x04")
        params = {"data": byte_array, "type": "bytearray"}

        # Serialize and deserialize through the store
        serialized = serialize(params)
        reconstructed = deserialize(serialized)

        # Verify bytearray is reconstructed (as bytes, since JSON doesn't distinguish)
        self.assertEqual(reconstructed["data"], bytes(byte_array))
        self.assertIsInstance(reconstructed["data"], bytes)
        self.assertEqual(reconstructed["type"], "bytearray")
