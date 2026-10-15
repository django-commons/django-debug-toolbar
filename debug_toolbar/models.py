from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import gettext_lazy as _

# Importing the middleware imports this module. Without the app installed,
# Django's own error is about this model's app_label, not about the setting.
if not apps.is_installed("debug_toolbar"):
    raise ImproperlyConfigured(
        "The debug toolbar requires 'debug_toolbar' in INSTALLED_APPS."
    )


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
