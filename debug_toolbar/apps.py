import inspect
import mimetypes

from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Error, Warning, register
from django.middleware.gzip import GZipMiddleware
from django.urls import NoReverseMatch, reverse
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from debug_toolbar import APP_NAME, settings as dt_settings
from debug_toolbar.settings import CONFIG_DEFAULTS


class DebugToolbarConfig(AppConfig):
    name = "debug_toolbar"
    verbose_name = _("Debug Toolbar")

    def ready(self):
        from debug_toolbar.toolbar import DebugToolbar

        # Import the panels when the app is ready and call their ready() methods.  This
        # allows panels like CachePanel to enable their instrumentation immediately.
        for cls in DebugToolbar.get_panel_classes():
            cls.ready()
        _manage_migrations_visibility(self.name)

    def import_models(self):
        """
        Override import models to avoid allowing users to dynamically fetch a model
        that doesn't have a table behind it unless they are using the DatabaseStore.
        This also prevents the command `migrate --run-syncdb` from creating tables
        for the models.
        """
        dt_config = dt_settings.get_config()
        if dt_config["TOOLBAR_STORE_CLASS"] == "debug_toolbar.store.DatabaseStore":
            return super().import_models()
        # Not using the database store, don't import the models
        self.models = {}


def _manage_migrations_visibility(app_name):
    """
    Adjust the toolbar's migration visibility by manipulating the
    project's settings.

    This is a hack since it's manipulating settings.
    """
    if (
        dt_settings.get_config()["TOOLBAR_STORE_CLASS"]
        != "debug_toolbar.store.DatabaseStore"
    ):
        # This effectively hides the migrations by telling Django they don't exist.
        settings.MIGRATION_MODULES.setdefault(app_name, None)


def check_template_config(config):
    """
    Checks if a template configuration is valid.

    The toolbar requires either the toolbars to be unspecified or
    ``django.template.loaders.app_directories.Loader`` to be
    included in the loaders.
    If custom loaders are specified, then APP_DIRS must be True.
    """

    def flat_loaders(loaders):
        """
        Recursively flatten the settings list of template loaders.

        Check for (loader, [child_loaders]) tuples.
        Django's default cached loader uses this pattern.
        """
        for loader in loaders:
            if isinstance(loader, tuple):
                yield loader[0]
                yield from flat_loaders(loader[1])
            else:
                yield loader

    app_dirs = config.get("APP_DIRS", False)
    loaders = config.get("OPTIONS", {}).get("loaders", None)
    if loaders:
        loaders = list(flat_loaders(loaders))

    # By default the app loader is included.
    has_app_loaders = (
        loaders is None or "django.template.loaders.app_directories.Loader" in loaders
    )
    return has_app_loaders or app_dirs


@register
def check_middleware(app_configs, **kwargs):
    from debug_toolbar.middleware import DebugToolbarMiddleware

    errors = []
    gzip_index = None
    debug_toolbar_indexes = []

    if all(not check_template_config(config) for config in settings.TEMPLATES):
        errors.append(
            Warning(
                "At least one DjangoTemplates TEMPLATES configuration needs "
                "to use django.template.loaders.app_directories.Loader or "
                "have APP_DIRS set to True.",
                hint=(
                    "Include django.template.loaders.app_directories.Loader "
                    'in ["OPTIONS"]["loaders"]. Alternatively use '
                    "APP_DIRS=True for at least one "
                    "django.template.backends.django.DjangoTemplates "
                    "backend configuration."
                ),
                id="debug_toolbar.W006",
            )
        )

    # If old style MIDDLEWARE_CLASSES is being used, report an error.
    if settings.is_overridden("MIDDLEWARE_CLASSES"):
        errors.append(
            Warning(
                "debug_toolbar is incompatible with MIDDLEWARE_CLASSES setting.",
                hint="Use MIDDLEWARE instead of MIDDLEWARE_CLASSES",
                id="debug_toolbar.W004",
            )
        )
        return errors

    # Determine the indexes which gzip and/or the toolbar are installed at
    for i, middleware in enumerate(settings.MIDDLEWARE):
        if is_middleware_class(GZipMiddleware, middleware):
            gzip_index = i
        elif is_middleware_class(DebugToolbarMiddleware, middleware):
            debug_toolbar_indexes.append(i)

    if not debug_toolbar_indexes:
        # If the toolbar does not appear, report an error.
        errors.append(
            Warning(
                "debug_toolbar.middleware.DebugToolbarMiddleware is missing "
                "from MIDDLEWARE.",
                hint="Add debug_toolbar.middleware.DebugToolbarMiddleware to "
                "MIDDLEWARE.",
                id="debug_toolbar.W001",
            )
        )
    elif len(debug_toolbar_indexes) != 1:
        # If the toolbar appears multiple times, report an error.
        errors.append(
            Warning(
                "debug_toolbar.middleware.DebugToolbarMiddleware occurs "
                "multiple times in MIDDLEWARE.",
                hint="Load debug_toolbar.middleware.DebugToolbarMiddleware only "
                "once in MIDDLEWARE.",
                id="debug_toolbar.W002",
            )
        )
    elif gzip_index is not None and debug_toolbar_indexes[0] < gzip_index:
        # If the toolbar appears before the gzip index, report an error.
        errors.append(
            Warning(
                "debug_toolbar.middleware.DebugToolbarMiddleware occurs before "
                "django.middleware.gzip.GZipMiddleware in MIDDLEWARE.",
                hint="Move debug_toolbar.middleware.DebugToolbarMiddleware to "
                "after django.middleware.gzip.GZipMiddleware in MIDDLEWARE.",
                id="debug_toolbar.W003",
            )
        )
    return errors


@register
def check_panel_configs(app_configs, **kwargs):
    """Allow each panel to check the toolbar's integration for their its own purposes."""
    from debug_toolbar.toolbar import DebugToolbar

    errors = []
    for panel_class in DebugToolbar.get_panel_classes():
        for check_message in panel_class.run_checks():
            errors.append(check_message)
    return errors


def is_middleware_class(middleware_class, middleware_path):
    try:
        middleware_cls = import_string(middleware_path)
    except ImportError:
        return
    return inspect.isclass(middleware_cls) and issubclass(
        middleware_cls, middleware_class
    )


@register
def check_panels(app_configs, **kwargs):
    errors = []
    panels = dt_settings.get_panels()
    if not panels:
        errors.append(
            Warning(
                "Setting DEBUG_TOOLBAR_PANELS is empty.",
                hint="Set DEBUG_TOOLBAR_PANELS to a non-empty list in your "
                "settings.py.",
                id="debug_toolbar.W005",
            )
        )
    return errors


@register
def js_mimetype_check(app_configs, **kwargs):
    """
    Check that JavaScript files are resolving to the correct content type.
    """
    # Ideally application/javascript is returned, but text/javascript is
    # acceptable.
    javascript_types = {"application/javascript", "text/javascript"}
    check_failed = not set(mimetypes.guess_type("toolbar.js")).intersection(
        javascript_types
    )
    if check_failed:
        return [
            Warning(
                "JavaScript files are resolving to the wrong content type.",
                hint="The Django Debug Toolbar may not load properly while mimetypes are misconfigured. "
                "See the Django documentation for an explanation of why this occurs.\n"
                "https://docs.djangoproject.com/en/stable/ref/contrib/staticfiles/#static-file-development-view\n"
                "\n"
                "This typically occurs on Windows machines. The suggested solution is to modify "
                "HKEY_CLASSES_ROOT in the registry to specify the content type for JavaScript "
                "files.\n"
                "\n"
                "[HKEY_CLASSES_ROOT\\.js]\n"
                '"Content Type"="application/javascript"',
                id="debug_toolbar.W007",
            )
        ]
    return []


@register
def debug_toolbar_installed_when_running_tests_check(app_configs, **kwargs):
    """
    Check that the toolbar is not being used when tests are running
    """
    # Check if show toolbar callback has changed
    show_toolbar_changed = (
        dt_settings.get_config()["SHOW_TOOLBAR_CALLBACK"]
        != CONFIG_DEFAULTS["SHOW_TOOLBAR_CALLBACK"]
    )
    try:
        # Check if the toolbar's urls are installed
        reverse(f"{APP_NAME}:render_panel")
        toolbar_urls_installed = True
    except NoReverseMatch:
        toolbar_urls_installed = False

    # If the user is using the default SHOW_TOOLBAR_CALLBACK,
    # then the middleware will respect the change to settings.DEBUG.
    # However, if the user has changed the callback to:
    # DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG}
    # where DEBUG is not settings.DEBUG, then it won't pick up that Django'
    # test runner has changed the value for settings.DEBUG, and the middleware
    # will inject the toolbar, while the URLs aren't configured leading to a
    # NoReverseMatch error.
    likely_error_setup = show_toolbar_changed and not toolbar_urls_installed

    if (
        not settings.DEBUG
        and dt_settings.get_config()["IS_RUNNING_TESTS"]
        and likely_error_setup
    ):
        return [
            Error(
                "The Django Debug Toolbar can't be used with tests",
                hint="Django changes the DEBUG setting to False when running "
                "tests. By default the Django Debug Toolbar is installed because "
                "DEBUG is set to True. For most cases, you need to avoid installing "
                "the toolbar when running tests. If you feel this check is in error, "
                "you can set `DEBUG_TOOLBAR_CONFIG['IS_RUNNING_TESTS'] = False` to "
                "bypass this check.",
                id="debug_toolbar.E001",
            )
        ]
    else:
        return []


@register
def check_settings(app_configs, **kwargs):
    errors = []
    USER_CONFIG = getattr(settings, "DEBUG_TOOLBAR_CONFIG", {})
    if "OBSERVE_REQUEST_CALLBACK" in USER_CONFIG:
        errors.append(
            Warning(
                "The deprecated OBSERVE_REQUEST_CALLBACK setting is present in DEBUG_TOOLBAR_CONFIG.",
                hint="Use the UPDATE_ON_FETCH and/or SHOW_TOOLBAR_CALLBACK settings instead.",
                id="debug_toolbar.W008",
            )
        )
    return errors
