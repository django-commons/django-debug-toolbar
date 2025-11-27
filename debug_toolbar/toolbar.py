"""
The main DebugToolbar class that loads and renders the Toolbar.
"""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Callable
from functools import cache

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.dispatch import Signal
from django.http import HttpRequest
from django.template import TemplateSyntaxError
from django.template.loader import render_to_string
from django.urls import URLPattern, URLResolver, include, path, re_path, resolve
from django.urls.exceptions import Resolver404
from django.utils.module_loading import import_string
from django.utils.translation import get_language, override as lang_override

from debug_toolbar import APP_NAME, settings as dt_settings
from debug_toolbar._stubs import GetResponse
from debug_toolbar.store import BaseStore, get_store

from .panels import Panel
from .utils import get_csp_nonce

logger = logging.getLogger(__name__)


class DebugToolbar:
    # for internal testing use only
    _created = Signal()
    store: BaseStore = None

    def __init__(
        self,
        request: HttpRequest,
        get_response: GetResponse,
        request_id: str | None = None,
    ):
        self.request = request
        self.config = dt_settings.get_config().copy()
        panels = []
        for panel_class in reversed(self.get_panel_classes()):
            panel = panel_class(self, get_response)
            panels.append(panel)
            if panel.enabled:
                get_response = panel.process_request
        self.process_request = get_response
        self._panels = {panel.panel_id: panel for panel in reversed(panels)}
        self.stats = {}
        self.server_timing_stats = {}
        self.request_id = request_id
        self.init_store()
        self._created.send(request, toolbar=self)

    # Manage panels

    @property
    def panels(self) -> list[Panel]:
        """
        Get a list of all available panels.
        """
        return list(self._panels.values())

    @property
    def enabled_panels(self) -> list[Panel]:
        """
        Get a list of panels enabled for the current request.
        """
        return [panel for panel in self._panels.values() if panel.enabled]

    @property
    def csp_nonce(self) -> str | None:
        """
        Look up the Content Security Policy nonce if there is one.
        """
        return get_csp_nonce(self.request)

    def get_panel_by_id(self, panel_id: str) -> Panel:
        """
        Get the panel with the given id, which is the class name by default.
        """
        return self._panels[panel_id]

    # Handle rendering the toolbar in HTML

    def render_toolbar(self) -> str:
        """
        Renders the overall Toolbar with panels inside.
        """
        if not self.should_render_panels():
            self.init_store()
        try:
            context = {"toolbar": self}
            lang = self.config["TOOLBAR_LANGUAGE"] or get_language()
            with lang_override(lang):
                return render_to_string("debug_toolbar/base.html", context)
        except TemplateSyntaxError:
            if not apps.is_installed("django.contrib.staticfiles"):
                raise ImproperlyConfigured(
                    "The debug toolbar requires the staticfiles contrib app. "
                    "Add 'django.contrib.staticfiles' to INSTALLED_APPS and "
                    "define STATIC_URL in your settings."
                ) from None
            else:
                raise

    def should_render_panels(self) -> bool:
        """Determine whether the panels should be rendered during the request

        If False, the panels will be loaded via Ajax.
        """
        return self.config["RENDER_PANELS"] or False

    # Handle storing toolbars in memory and fetching them later on

    def init_store(self):
        # Store already initialized.
        if self.store is None:
            self.store = get_store()

        if self.request_id:
            return
        self.request_id = uuid.uuid4().hex
        self.store.set(self.request_id)

    @classmethod
    def fetch(
        cls, request_id: str, panel_id: str | None = None
    ) -> StoredDebugToolbar | None:
        if get_store().exists(request_id):
            return StoredDebugToolbar.from_store(request_id, panel_id=panel_id)

    # Manually implement class-level caching of panel classes and url patterns
    # because it's more obvious than going through an abstraction.

    _panel_classes: list[Panel] | None = None

    @classmethod
    def get_panel_classes(cls) -> list[type[Panel]] | None:
        if cls._panel_classes is None:
            # Load panels in a temporary variable for thread safety.
            panel_classes = [
                import_string(panel_path) for panel_path in dt_settings.get_panels()
            ]
            cls._panel_classes = panel_classes
        return cls._panel_classes

    _urlpatterns: list[URLPattern | URLResolver] | None = None

    @classmethod
    def get_urls(cls) -> list[URLPattern | URLResolver]:
        if cls._urlpatterns is None:
            from . import views

            # Load URLs in a temporary variable for thread safety.
            # Global URLs
            urlpatterns = [
                path("render_panel/", views.render_panel, name="render_panel"),
            ]
            # Per-panel URLs
            for panel_class in cls.get_panel_classes():
                urlpatterns += panel_class.get_urls()
            cls._urlpatterns = urlpatterns
        return cls._urlpatterns

    @classmethod
    def is_toolbar_request(cls, request: HttpRequest) -> bool:
        """
        Determine if the request is for a DebugToolbar view.
        """
        # The primary caller of this function is in the middleware which may
        # not have resolver_match set.
        try:
            resolver_match = request.resolver_match or resolve(
                request.path_info, getattr(request, "urlconf", None)
            )
        except Resolver404:
            return False
        return (
            bool(resolver_match.namespaces)
            and resolver_match.namespaces[-1] == APP_NAME
        )

    @staticmethod
    @cache
    def get_observe_request() -> Callable:
        # If OBSERVE_REQUEST_CALLBACK is a string, which is the recommended
        # setup, resolve it to the corresponding callable.
        func_or_path = dt_settings.get_config()["OBSERVE_REQUEST_CALLBACK"]
        if isinstance(func_or_path, str):
            return import_string(func_or_path)
        else:
            return func_or_path


def observe_request(request: HttpRequest) -> bool:
    """
    Determine whether to update the toolbar from a client side request.
    """
    return True


def from_store_get_response(request: HttpRequest | None) -> None:
    logger.warning(
        "get_response was called for debug toolbar after being loaded from the store. No request exists in this scenario as the request is not stored, only the panel's data."
    )
    return None


class StoredDebugToolbar(DebugToolbar):
    def __init__(
        self,
        request: HttpRequest | None,
        get_response: GetResponse,
        request_id: str | None = None,
    ):
        self.request = None
        self.config = dt_settings.get_config().copy()
        self.process_request = get_response
        self.stats = {}
        self.server_timing_stats = {}
        self.request_id = request_id
        self.init_store()

    @classmethod
    def from_store(
        cls, request_id: str, panel_id: str | None = None
    ) -> StoredDebugToolbar:
        toolbar = StoredDebugToolbar(
            None, from_store_get_response, request_id=request_id
        )
        toolbar._panels = {}

        for panel_class in reversed(cls.get_panel_classes()):
            panel = panel_class(toolbar, from_store_get_response)
            if panel_id and panel.panel_id != panel_id:
                continue
            data = toolbar.store.panel(toolbar.request_id, panel.panel_id)
            panel.load_stats_from_store(data)
            toolbar._panels[panel.panel_id] = panel
        return toolbar


def debug_toolbar_urls(prefix: str = "__debug__") -> list[URLPattern | URLResolver]:
    """
    Return a URL pattern for serving toolbar in debug mode.

    from django.conf import settings
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns = [
        # ... the rest of your URLconf goes here ...
    ] + debug_toolbar_urls()
    """
    if not prefix:
        raise ImproperlyConfigured("Empty urls prefix not permitted")
    elif not settings.DEBUG:
        # No-op if not in debug mode.
        return []
    return [
        re_path(
            r"^{}/".format(re.escape(prefix.lstrip("/"))),
            include("debug_toolbar.urls"),
        ),
    ]
