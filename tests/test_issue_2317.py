from uuid import UUID

import pytest

from debug_toolbar.store import serialize


class TestNonStringDictKeys:
    """Test cases for issue #2317 - non-string dict keys in serialization"""

    def test_tuple_keys_raise_typeerror(self):
        """Tuple keys should cause TypeError with current code"""
        data = {(1, 2): "value1", (3, 4): "value2"}

        with pytest.raises(
            TypeError, match="keys must be str, int, float, bool or None, not tuple"
        ):
            serialize(data)

    def test_uuid_keys_raise_typeerror(self):
        """UUID keys should cause TypeError with current code"""
        uuid1 = UUID("aaaaaaaa-0000-0000-0000-000000000001")
        uuid2 = UUID("bbbbbbbb-0000-0000-0000-000000000002")
        data = {uuid1: "value1", uuid2: "value2"}

        with pytest.raises(TypeError):
            serialize(data)

    def test_nested_dict_with_tuple_keys_raise_typeerror(self):
        """Nested dicts with tuple keys should cause TypeError"""
        data = {"normal_key": {(1, 2): "nested_value1", (3, 4): "nested_value2"}}

        with pytest.raises(TypeError):
            serialize(data)

    def test_list_of_dicts_with_tuple_keys_raise_typeerror(self):
        """Lists containing dicts with tuple keys should cause TypeError"""
        data = [{"normal": "value"}, {(1, 2): "problem_value"}]

        with pytest.raises(TypeError):
            serialize(data)

    def test_mixed_valid_and_invalid_keys_raise_typeerror(self):
        """Mix of valid and invalid keys should still raise TypeError"""
        data = {"valid_key": "value", (1, 2): "invalid_key_value", 123: "valid_int_key"}

        with pytest.raises(TypeError):
            serialize(data)
