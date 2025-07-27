"""
Tests for GeoDjango binary parameter handling fix
"""
import json
import base64
import unittest

from debug_toolbar.panels.sql.forms import _reconstruct_params
from debug_toolbar.panels.sql.tracking import NormalCursorMixin

from ..base import BaseTestCase


class MockCursor:
    """Mock cursor for testing"""
    pass


class MockConnection:
    """Mock database connection for testing"""
    vendor = "postgresql"
    alias = "default"


class MockLogger:
    """Mock logger for testing"""
    def record(self, **kwargs):
        pass


class TestCursor(NormalCursorMixin):
    """Test cursor that can be instantiated"""
    def __init__(self):
        # Initialize with mock objects
        self.cursor = MockCursor()
        self.db = MockConnection()
        self.logger = MockLogger()


class GeoDjangoBinaryParameterTest(BaseTestCase):
    """Test cases for GeoDjango binary parameter handling"""

    def test_binary_parameter_encoding_decoding(self):
        """Test that binary parameters are properly encoded and decoded"""
        # Create a test cursor with the _decode method
        cursor = TestCursor()
        
        # Test binary data similar to GeoDjango EWKB geometry
        binary_data = b'\x01\x01\x00\x00\x20\xe6\x10\x00\x00\xff\xfe\xfd'
        
        # Test encoding (what happens when query is logged)
        encoded = cursor._decode(binary_data)
        
        # Should be marked as binary data
        self.assertIsInstance(encoded, dict)
        self.assertIn("__djdt_binary__", encoded)
        
        # Should be base64 encoded
        expected_b64 = base64.b64encode(binary_data).decode('ascii')
        self.assertEqual(encoded["__djdt_binary__"], expected_b64)
        
        # Test JSON serialization (what happens in tracking.py)
        json_params = json.dumps([encoded])
        
        # Test parsing back from JSON
        parsed = json.loads(json_params)
        
        # Test reconstruction (what happens in forms.py)
        reconstructed = _reconstruct_params(parsed)
        
        # Should recover original binary data
        self.assertEqual(len(reconstructed), 1)
        self.assertEqual(reconstructed[0], binary_data)
        self.assertIsInstance(reconstructed[0], bytes)

    def test_mixed_parameter_types(self):
        """Test that mixed parameter types are handled correctly"""
        cursor = TestCursor()
        
        # Test with mixed types including binary data
        params = [
            "string_param",
            42,
            b'\x01\x02\x03',  # binary data
            None,
            ["nested", "list"],
        ]
        
        # Encode each parameter
        encoded_params = [cursor._decode(p) for p in params]
        
        # Serialize to JSON
        json_str = json.dumps(encoded_params)
        
        # Parse and reconstruct
        parsed = json.loads(json_str)
        reconstructed = _reconstruct_params(parsed)
        
        # Check each parameter
        self.assertEqual(reconstructed[0], "string_param")  # string unchanged
        self.assertEqual(reconstructed[1], 42)  # int unchanged
        self.assertEqual(reconstructed[2], b'\x01\x02\x03')  # binary restored
        self.assertIsNone(reconstructed[3])  # None unchanged
        self.assertEqual(reconstructed[4], ["nested", "list"])  # list unchanged

    def test_nested_binary_data(self):
        """Test binary data nested in lists and dicts"""
        cursor = TestCursor()
        
        # Test nested structures with binary data
        nested_params = [
            [b'\x01\x02', "string", b'\x03\x04'],
            {"key": b'\x05\x06', "other": "value"},
        ]
        
        # Encode
        encoded = [cursor._decode(p) for p in nested_params]
        
        # Serialize and parse
        json_str = json.dumps(encoded)
        parsed = json.loads(json_str)
        reconstructed = _reconstruct_params(parsed)
        
        # Check nested list
        self.assertEqual(reconstructed[0][0], b'\x01\x02')
        self.assertEqual(reconstructed[0][1], "string")
        self.assertEqual(reconstructed[0][2], b'\x03\x04')
        
        # Check nested dict
        self.assertEqual(reconstructed[1]["key"], b'\x05\x06')
        self.assertEqual(reconstructed[1]["other"], "value")

    def test_empty_binary_data(self):
        """Test handling of empty binary data"""
        cursor = TestCursor()
        
        # Test empty bytes
        empty_bytes = b''
        encoded = cursor._decode(empty_bytes)
        
        # Should still be marked as binary
        self.assertIsInstance(encoded, dict)
        self.assertIn("__djdt_binary__", encoded)
        
        # Reconstruct
        json_str = json.dumps([encoded])
        parsed = json.loads(json_str)
        reconstructed = _reconstruct_params(parsed)
        
        self.assertEqual(reconstructed[0], empty_bytes)

    def test_bytearray_support(self):
        """Test that bytearray is also handled as binary data"""
        cursor = TestCursor()
        
        # Test bytearray
        byte_array = bytearray(b'\x01\x02\x03\x04')
        encoded = cursor._decode(byte_array)
        
        # Should be marked as binary
        self.assertIn("__djdt_binary__", encoded)
        
        # Reconstruct (should become bytes, not bytearray)
        json_str = json.dumps([encoded])
        parsed = json.loads(json_str)
        reconstructed = _reconstruct_params(parsed)
        
        # Should be equal in content (bytes vs bytearray comparison works)
        self.assertEqual(reconstructed[0], byte_array)
        # Should be bytes type after reconstruction
        self.assertIsInstance(reconstructed[0], bytes)