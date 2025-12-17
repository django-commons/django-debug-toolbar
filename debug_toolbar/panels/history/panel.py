import contextlib
import json

from django.http.request import RawPostDataException
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from debug_toolbar.panels import Panel
from debug_toolbar.panels.history import views
from debug_toolbar.panels.history.forms import HistoryStoreForm


class HistoryPanel(Panel):
    """A panel to display History"""

    is_async = True
    title = _("History")
    nav_title = _("History")
    template = "debug_toolbar/panels/history.html"

    def get_headers(self, request):
        headers = super().get_headers(request)
        observe_request = self.toolbar.get_observe_request()
        request_id = self.toolbar.request_id
        if request_id and observe_request(request):
            headers["djdt-request-id"] = request_id
        return headers

    @property
    def enabled(self):
        # Do not show the history panel if the panels are rendered on request
        # rather than loaded via ajax.
        return super().enabled and not self.toolbar.should_render_panels()

    @property
    def is_historical(self):
        """The HistoryPanel should not be included in the historical panels."""
        return False

    @classmethod
    def get_urls(cls):
        return [
            path("history_sidebar/", views.history_sidebar, name="history_sidebar"),
            path("history_refresh/", views.history_refresh, name="history_refresh"),
        ]

    @property
    def nav_subtitle(self):
        return self.get_stats().get("request_url", "")

    def generate_stats(self, request, response):
        try:
            if request.method == "GET":
                data = request.GET.copy()
            else:
                data = request.POST.copy()
            # GraphQL tends to not be populated in POST. If the request seems
            # empty, check if it's a JSON request.
            if (
                not data
                and request.body
                and request.headers.get("content-type") == "application/json"
            ):
                with contextlib.suppress(ValueError):
                    data = json.loads(request.body)

        except RawPostDataException:
            # It is not guaranteed that we may read the request data (again).
            data = None

        self.record_stats(
            {
                "request_url": request.get_full_path(),
                "request_method": request.method,
                "status_code": response.status_code,
                "data": data,
                "time": timezone.now(),
            }
        )

    @property
    def content(self):
        """Content of the panel when it's displayed in full screen.

        Fetch every store for the toolbar and include it in the template.
        """
        toolbar_history = {}
        for request_id in reversed(self.toolbar.store.request_ids()):
            toolbar_history[request_id] = {
                "history_stats": self.toolbar.store.panel(
                    request_id, HistoryPanel.panel_id
                ),
                "form": HistoryStoreForm(
                    initial={"request_id": request_id, "exclude_history": True}
                ),
            }

        return render_to_string(
            self.template,
            {
                "current_request_id": self.toolbar.request_id,
                "toolbar_history": toolbar_history,
                "refresh_form": HistoryStoreForm(
                    initial={
                        "request_id": self.toolbar.request_id,
                        "exclude_history": True,
                    }
                ),
            },
        )

    @property
    def scripts(self):
        scripts = super().scripts
        scripts.append(static("debug_toolbar/js/history.js"))
        return scripts
