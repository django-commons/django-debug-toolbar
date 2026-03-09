import json
import zlib
import base64
from django.db import models
from django.utils.translation import gettext_lazy as _


class HistoryEntry(models.Model):
    request_id = models.UUIDField(primary_key=True)
    # Change from JSONField to TextField
    data = models.TextField(default="")  # Empty string default for new entries
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("history entry")
        verbose_name_plural = _("history entries")
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.request_id)
    
    def set_data(self, data_dict):
        """
        Compress and store panel data.
        
        Args:
            data_dict: Dictionary containing panel data
        """
        if not data_dict:
            self.data = ""
            return
            
        # Convert dict to JSON string
        json_str = json.dumps(data_dict)
        
        # Compress with zlib (level 6 is good balance of speed/ratio)
        compressed = zlib.compress(json_str.encode('utf-8'), level=6)
        
        # Encode to base64 for safe text storage
        self.data = base64.b64encode(compressed).decode('ascii')
    
    def get_data(self):
        """
        Retrieve and decompress panel data.
        
        Returns:
            Dictionary containing panel data
        """
        if not self.data:
            return {}
            
        try:
            # Try new compressed format first
            compressed = base64.b64decode(self.data.encode('ascii'))
            json_str = zlib.decompress(compressed).decode('utf-8')
            return json.loads(json_str)
        except (zlib.error, base64.binascii.Error, UnicodeDecodeError, json.JSONDecodeError):
            # Fallback for backward compatibility with old JSONField data
            try:
                # Try parsing as JSON (old format)
                if isinstance(self.data, str) and self.data.startswith(('{', '[')):
                    return json.loads(self.data)
                # If it's already a dict (from old JSONField)
                return self.data
            except (json.JSONDecodeError, TypeError):
                # If all else fails, return empty dict
                return {}
    
    def save(self, *args, **kwargs):
        # Handle case where we have raw data to compress
        if hasattr(self, '_raw_data'):
            self.set_data(self._raw_data)
            delattr(self, '_raw_data')
        super().save(*args, **kwargs)