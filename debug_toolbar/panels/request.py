from django.http import Http404
from django.urls import resolve
from django.utils.translation import gettext_lazy as _

from debug_toolbar.panels import Panel
from debug_toolbar.utils import get_name_from_obj, sanitize_and_sort_request_vars


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

        view_info = {
            "view_func": _("<no view>"),
            "view_args": "None",
            "view_kwargs": "None",
            "view_urlname": "None",
        }
        try:
            match = resolve(request.path_info)
            func, args, kwargs = match
            view_info["view_func"] = get_name_from_obj(func)
            view_info["view_args"] = args
            view_info["view_kwargs"] = kwargs

            if getattr(match, "url_name", False):
                url_name = match.url_name
                if match.namespaces:
                    url_name = ":".join([*match.namespaces, url_name])
            else:
                url_name = _("<unavailable>")

            view_info["view_urlname"] = url_name

        except Http404:
            pass
        self.record_stats(view_info)

        if hasattr(request, "session"):
            session_data = dict(request.session)
            self.record_stats({"session": sanitize_and_sort_request_vars(session_data)})
