import json
import zlib

from django.db import models


class CompressedJSONField(models.BinaryField):
    """
    Custom BinaryField that automatically compresses JSON data.

    Stores data as compressed binary instead of text to save space
    and avoid PostgreSQL JSONB size limitations.
    """

    description = "Compressed JSON data"

    def from_db_value(self, value, expression, connection):
        """Convert from database value to Python object."""
        if value is None:
            return {}

        try:
            json_str = zlib.decompress(value).decode("utf-8")
            return json.loads(json_str)
        except (zlib.error, UnicodeDecodeError, json.JSONDecodeError):
            try:
                if isinstance(value, bytes):
                    return json.loads(value.decode("utf-8"))
                return {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return {}

    def get_prep_value(self, value):
        """Convert Python object to database value."""
        if value is None:
            value = {}

        json_str = json.dumps(value)
        return zlib.compress(json_str.encode("utf-8"), level=6)

    def value_to_string(self, obj):
        """Convert to string for serialization."""
        value = self.value_from_object(obj)
        return self.get_prep_value(value)
