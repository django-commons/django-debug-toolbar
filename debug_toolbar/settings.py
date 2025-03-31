import sys
import warnings
from functools import cache

from django.conf import settings
from django.dispatch import receiver
from django.test.signals import setting_changed

CONFIG_DEFAULTS = {
    # Toolbar options
    "DISABLE_PANELS": {
        "debug_toolbar.panels.profiling.ProfilingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
    },
    "INSERT_BEFORE": "</body>",
    "RENDER_PANELS": None,
    "RESULTS_CACHE_SIZE": 25,
    "ROOT_TAG_EXTRA_ATTRS": "",
    "SHOW_COLLAPSED": False,
    "SHOW_TOOLBAR_CALLBACK": "debug_toolbar.middleware.show_toolbar",
    # Panel options
    "EXTRA_SIGNALS": [],
    "ENABLE_STACKTRACES": True,
    "ENABLE_STACKTRACES_LOCALS": False,
    "HIDE_IN_STACKTRACES": (
        "socketserver",
        "threading",
        "wsgiref",
        "debug_toolbar",
        "django.db",
        "django.core.handlers",
        "django.core.servers",
        "django.utils.decorators",
        "django.utils.deprecation",
        "django.utils.functional",
    ),
    "PRETTIFY_SQL": True,
    "PROFILER_CAPTURE_PROJECT_CODE": True,
    "PROFILER_MAX_DEPTH": 10,
    "PROFILER_THRESHOLD_RATIO": 8,
    "SHOW_TEMPLATE_CONTEXT": True,
    "SKIP_TEMPLATE_PREFIXES": ("django/forms/widgets/", "admin/widgets/"),
    "SQL_WARNING_THRESHOLD": 500,  # milliseconds
    "OBSERVE_REQUEST_CALLBACK": "debug_toolbar.toolbar.observe_request",
    "TOOLBAR_LANGUAGE": None,
    "IS_RUNNING_TESTS": "test" in sys.argv,
    "UPDATE_ON_FETCH": False,
}


@cache
def get_config():
    USER_CONFIG = getattr(settings, "DEBUG_TOOLBAR_CONFIG", {})
    CONFIG = CONFIG_DEFAULTS.copy()
    CONFIG.update(USER_CONFIG)
    return CONFIG


PANELS_DEFAULTS = [
    "debug_toolbar.panels.history.HistoryPanel",
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.alerts.AlertsPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
]


@cache
def get_panels():
    try:
        PANELS = list(settings.DEBUG_TOOLBAR_PANELS)
    except AttributeError:
        PANELS = PANELS_DEFAULTS

    logging_panel = "debug_toolbar.panels.logging.LoggingPanel"
    if logging_panel in PANELS:
        PANELS = [panel for panel in PANELS if panel != logging_panel]
        warnings.warn(
            f"Please remove {logging_panel} from your DEBUG_TOOLBAR_PANELS setting.",
            DeprecationWarning,
            stacklevel=1,
        )
    return PANELS


@receiver(setting_changed)
def update_toolbar_config(*, setting, **kwargs):
    """
    Refresh configuration when overriding settings.
    """
    if setting == "DEBUG_TOOLBAR_CONFIG":
        get_config.cache_clear()
    elif setting == "DEBUG_TOOLBAR_PANELS":
        from debug_toolbar.toolbar import DebugToolbar

        get_panels.cache_clear()
        DebugToolbar._panel_classes = None
        # Not implemented: invalidate debug_toolbar.urls.
