from django.db import models


class DebugToolbarEntry(models.Model):
    request_id = models.UUIDField(primary_key=True)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Debug Toolbar Entry"
        verbose_name_plural = "Debug Toolbar Entries"
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.request_id)
