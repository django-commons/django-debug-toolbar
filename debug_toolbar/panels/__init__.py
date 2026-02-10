from django.core.handlers.asgi import ASGIRequest
from django.template.loader import render_to_string
from django.utils.functional import classproperty

from debug_toolbar import settings as dt_settings
from debug_toolbar._stubs import GetResponse
from debug_toolbar.utils import get_name_from_obj


class Panel:
    """
    Base class for panels.
    """

    is_async = False

    def __init__(self, toolbar, get_response: GetResponse):
        self.toolbar = toolbar
        self.get_response = get_response
        self.from_store = False

    # Private panel properties

    @classproperty
    def panel_id(cls) -> str:
        return cls.__name__

    @property
    def enabled(self) -> bool:
        # Check if the panel is async compatible
        if not self.is_async and isinstance(self.toolbar.request, ASGIRequest):
            return False

        if self.from_store:
            # If the toolbar was loaded from the store the existence of
            # recorded data indicates whether it was enabled or not.
            # We can't use the remainder of the logic since we don't have
            # a request to work off of.
            return bool(self.get_stats())

        # The user's cookies should override the default value
        cookie_value = self.toolbar.request.COOKIES.get("djdt" + self.panel_id)
        if cookie_value is not None:
            return cookie_value == "on"

        # Check to see if settings has a default value for it
        disabled_panels = dt_settings.get_config()["DISABLE_PANELS"]
        panel_path = get_name_from_obj(self)
        # Some panels such as the SQLPanel and TemplatesPanel exist in a
        # panel module, but can be disabled without panel in the path.
        # For that reason, replace .panel. in the path and check for that
        # value in the disabled panels as well.
        return (
            panel_path not in disabled_panels
            and panel_path.replace(".panel.", ".") not in disabled_panels
        )

    # Titles and content

    @property
    def nav_title(self):
        """
        Title shown in the side bar. Defaults to :attr:`title`.
        """
        return self.title

    @property
    def nav_subtitle(self):
        """
        Subtitle shown in the side bar. Defaults to the empty string.
        """
        return ""

    @property
    def has_content(self):
        """
        ``True`` if the panel can be displayed in full screen, ``False`` if
        it's only shown in the side bar. Defaults to ``True``.
        """
        return True

    @property
    def is_historical(self):
        """
        Panel supports rendering historical values.

        Defaults to :attr:`has_content`.
        """
        return self.has_content

    @property
    def title(self):
        """
        Title shown in the panel when it's displayed in full screen.

        Mandatory, unless the panel sets :attr:`has_content` to ``False``.
        """
        raise NotImplementedError

    @property
    def template(self):
        """
        Template used to render :attr:`content`.

        Mandatory, unless the panel sets :attr:`has_content` to ``False`` or
        overrides :attr:`content`.
        """
        raise NotImplementedError

    @property
    def content(self):
        """
        Content of the panel when it's displayed in full screen.

        By default this renders the template defined by :attr:`template`.
        Statistics stored with :meth:`record_stats` are available in the
        template's context.
        """
        if self.has_content:
            return render_to_string(self.template, self.get_stats())

    @property
    def scripts(self):
        """
        Scripts used by the HTML content of the panel when it's displayed.

        When a panel is rendered on the frontend, the ``djdt.panel.render``
        JavaScript event will be dispatched. The scripts can listen for
        this event to support dynamic functionality.
        """
        return []

    # Panel early initialization

    @classmethod
    def ready(cls):
        """
        Perform early initialization for the panel.

        This should only include initialization or instrumentation that needs to
        be done unconditionally for the panel regardless of whether it is
        enabled for a particular request.  It should be idempotent.
        """

    # URLs for panel-specific views

    @classmethod
    def get_urls(cls):
        """
        Return URLpatterns, if the panel has its own views.
        """
        return []

    # Enable and disable (expensive) instrumentation, must be idempotent

    def enable_instrumentation(self):
        """
        Enable instrumentation to gather data for this panel.

        This usually means monkey-patching (!) or registering signal
        receivers. Any instrumentation with a non-negligible effect on
        performance should be installed by this method rather than at import
        time.

        Unless the toolbar or this panel is disabled, this method will be
        called early in ``DebugToolbarMiddleware``. It should be idempotent.

        Add the ``aenable_instrumentation``  method to a panel subclass
        to support async logic for instrumentation.
        """

    def disable_instrumentation(self):
        """
        Disable instrumentation to gather data for this panel.

        This is the opposite of :meth:`enable_instrumentation`.

        Unless the toolbar or this panel is disabled, this method will be
        called late in the middleware. It should be idempotent.
        """

    # Store and retrieve stats (shared between panels for no good reason)

    def record_stats(self, stats):
        """
        Store data gathered by the panel. ``stats`` is a :class:`dict`.

        Each call to ``record_stats`` updates the store's data for
        the panel.

        To support backwards compatibility, it will also update the
        panel's statistics dictionary.
        """
        self.toolbar.stats.setdefault(self.panel_id, {}).update(stats)
        self.toolbar.store.save_panel(
            self.toolbar.request_id, self.panel_id, self.toolbar.stats[self.panel_id]
        )

    def get_stats(self):
        """
        Access data stored by the panel. Returns a :class:`dict`.
        """
        return self.toolbar.stats.get(self.panel_id, {})

    def record_server_timing(self, key, title, value):
        """
        Store data gathered by the panel. ``stats`` is a :class:`dict`.

        Each call to ``record_stats`` updates the statistics dictionary.
        """
        data = {key: {"title": title, "value": value}}
        self.toolbar.server_timing_stats.setdefault(self.panel_id, {}).update(data)

    def get_server_timing_stats(self):
        """
        Access data stored by the panel. Returns a :class:`dict`.
        """
        return self.toolbar.server_timing_stats.get(self.panel_id, {})

    # Standard middleware methods

    def process_request(self, request):
        """
        Like __call__ in Django's middleware.

        Write panel logic related to the request there. Save data with
        :meth:`record_stats`.

        Return the existing response or overwrite it.
        """
        return self.get_response(request)

    def get_headers(self, request):
        """
        Get headers the panel needs to set.

        Called after :meth:`process_request
        <debug_toolbar.panels.Panel.generate_stats>` and
        :meth:`process_request<debug_toolbar.panels.Panel.generate_stats>`

        Header values will be appended if multiple panels need to set it.

        By default it sets the Server-Timing header.

        Return dict of headers to be appended.
        """
        headers = {}
        stats = self.get_server_timing_stats()
        if stats:
            headers["Server-Timing"] = ", ".join(
                # example: `SQLPanel_sql_time;dur=0;desc="SQL 0 queries"`
                '{}_{};dur={};desc="{}"'.format(
                    self.panel_id, key, record.get("value"), record.get("title")
                )
                for key, record in stats.items()
            )
        return headers

    def generate_stats(self, request, response):
        """
        Write panel logic related to the response there. Post-process data
        gathered while the view executed. Save data with :meth:`record_stats`.

        Called after :meth:`process_request
        <debug_toolbar.panels.Panel.process_request>`.


        Does not return a value.
        """

    def generate_server_timing(self, request, response):
        """
        Similar to :meth:`generate_stats
        <debug_toolbar.panels.Panel.generate_stats>`,

        Generate stats for Server Timing https://w3c.github.io/server-timing/

        Does not return a value.
        """

    def load_stats_from_store(self, data):
        """
        Instantiate the panel from serialized data.

        Return the panel instance.
        """
        self.toolbar.stats.setdefault(self.panel_id, {}).update(data)
        self.from_store = True

    @classmethod
    def run_checks(cls):
        """
        Check that the integration is configured correctly for the panel.

        This will be called as a part of the Django checks system when the
        application is being setup.

        Return a list of :class:`django.core.checks.CheckMessage` instances.
        """
        return []
