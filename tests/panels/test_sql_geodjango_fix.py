"""
Tests for GeoDjango binary parameter handling fix
"""

import base64
import json

from debug_toolbar.panels.sql.decoders import DebugToolbarJSONDecoder
from debug_toolbar.panels.sql.tracking import NormalCursorMixin

from ..base import BaseTestCase


class MockCursor:
    """Mock cursor for testing"""


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
        self.cursor = MockCursor()
        self.db = MockConnection()
        self.logger = MockLogger()


class GeoDjangoBinaryParameterTest(BaseTestCase):
    """Test cases for GeoDjango binary parameter handling"""

    def test_binary_parameter_encoding_decoding(self):
        """Test that binary parameters are properly encoded and decoded"""
        cursor = TestCursor()

        # Test binary data similar to GeoDjango EWKB geometry
        binary_data = b"\x01\x01\x00\x00\x20\xe6\x10\x00\x00\xff\xfe\xfd"
        encoded = cursor._decode(binary_data)

        self.assertIsInstance(encoded, dict)
        self.assertIn("__djdt_binary__", encoded)

        expected_b64 = base64.b64encode(binary_data).decode("ascii")
        self.assertEqual(encoded["__djdt_binary__"], expected_b64)

        json_params = json.dumps([encoded])
        reconstructed = json.loads(json_params, cls=DebugToolbarJSONDecoder)

        self.assertEqual(len(reconstructed), 1)
        self.assertEqual(reconstructed[0], binary_data)
        self.assertIsInstance(reconstructed[0], bytes)

    def test_mixed_parameter_types(self):
        """Test that mixed parameter types are handled correctly"""
        cursor = TestCursor()

        params = [
            "string_param",
            42,
            b"\x01\x02\x03",
            None,
            ["nested", "list"],
        ]

        encoded_params = [cursor._decode(p) for p in params]

        json_str = json.dumps(encoded_params)
        reconstructed = json.loads(json_str, cls=DebugToolbarJSONDecoder)

        self.assertEqual(reconstructed[0], "string_param")  # string unchanged
        self.assertEqual(reconstructed[1], 42)  # int unchanged
        self.assertEqual(reconstructed[2], b"\x01\x02\x03")  # binary restored
        self.assertIsNone(reconstructed[3])  # None unchanged
        self.assertEqual(reconstructed[4], ["nested", "list"])  # list unchanged

    def test_nested_binary_data(self):
        """Test binary data nested in lists and dicts"""
        cursor = TestCursor()

        nested_params = [
            [b"\x01\x02", "string", b"\x03\x04"],
            {"key": b"\x05\x06", "other": "value"},
        ]

        encoded = [cursor._decode(p) for p in nested_params]

        json_str = json.dumps(encoded)
        reconstructed = json.loads(json_str, cls=DebugToolbarJSONDecoder)

        self.assertEqual(reconstructed[0][0], b"\x01\x02")
        self.assertEqual(reconstructed[0][1], "string")
        self.assertEqual(reconstructed[0][2], b"\x03\x04")

        self.assertEqual(reconstructed[1]["key"], b"\x05\x06")
        self.assertEqual(reconstructed[1]["other"], "value")

    def test_empty_binary_data(self):
        """Test handling of empty binary data"""
        cursor = TestCursor()

        empty_bytes = b""
        encoded = cursor._decode(empty_bytes)

        self.assertIsInstance(encoded, dict)
        self.assertIn("__djdt_binary__", encoded)

        json_str = json.dumps([encoded])
        reconstructed = json.loads(json_str, cls=DebugToolbarJSONDecoder)

        self.assertEqual(reconstructed[0], empty_bytes)

    def test_bytearray_support(self):
        """Test that bytearray is also handled as binary data"""
        cursor = TestCursor()

        byte_array = bytearray(b"\x01\x02\x03\x04")
        encoded = cursor._decode(byte_array)

        self.assertIn("__djdt_binary__", encoded)

        json_str = json.dumps([encoded])
        reconstructed = json.loads(json_str, cls=DebugToolbarJSONDecoder)

        self.assertEqual(reconstructed[0], byte_array)
        self.assertIsInstance(reconstructed[0], bytes)
