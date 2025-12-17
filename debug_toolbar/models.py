from django.db import models
from django.utils.translation import gettext_lazy as _


class HistoryEntry(models.Model):
    request_id = models.UUIDField(primary_key=True)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("history entry")
        verbose_name_plural = _("history entries")
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.request_id)
