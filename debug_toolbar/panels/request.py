from django.http import Http404
from django.utils.translation import gettext_lazy as _

from debug_toolbar.panels import Panel
from debug_toolbar.utils import (
    get_view_path_metadata,
    sanitize_and_sort_request_vars,
)


class RequestPanel(Panel):
    """
    A panel to display request variables (POST/GET, session, cookies).
    """

    template = "debug_toolbar/panels/request.html"

    title = _("Request")

    @property
    def nav_subtitle(self):
        """
        Show abbreviated name of view function as subtitle
        """
        view_func = self.get_stats().get("view_func", "")
        return view_func.rsplit(".", 1)[-1]

    def generate_stats(self, request, response):
        self.record_stats(
            {
                "get": sanitize_and_sort_request_vars(request.GET),
                "post": sanitize_and_sort_request_vars(request.POST),
                "cookies": sanitize_and_sort_request_vars(request.COOKIES),
            }
        )

        try:
            view_metadata = get_view_path_metadata(request)
        except Http404:
            view_info = {
                "view_func": _("<no view>"),
                "view_args": "None",
                "view_kwargs": "None",
                "view_urlname": "None",
            }
        else:
            view_info = {
                "view_func": view_metadata.view_func,
                "view_args": view_metadata.view_args,
                "view_kwargs": view_metadata.view_kwargs,
                "view_urlname": view_metadata.url_name,
            }
        self.record_stats(view_info)

        if hasattr(request, "session"):
            session_data = dict(request.session)
            self.record_stats({"session": sanitize_and_sort_request_vars(session_data)})
