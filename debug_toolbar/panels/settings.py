from pprint import pformat

from django.utils.translation import gettext_lazy as _
from django.views.debug import get_default_exception_reporter_filter

from debug_toolbar.panels import Panel

get_safe_settings = get_default_exception_reporter_filter().get_safe_settings


def safe_pformat(obj):
    try:
        return pformat(obj)
    except Exception as e:
        return f"<unformattable {type(obj).__name__}: {e!r}>"


class SettingsPanel(Panel):
    """
    A panel to display all variables in django.conf.settings
    """

    template = "debug_toolbar/panels/settings.html"

    is_async = True

    nav_title = _("Settings")

    def title(self):
        return _("Settings from %s") % self.get_stats()["settings"].get(
            "SETTINGS_MODULE"
        )

    def generate_stats(self, request, response):
        self.record_stats(
            {
                "settings": {
                    key: safe_pformat(value)
                    for key, value in sorted(get_safe_settings().items())
                }
            }
        )
