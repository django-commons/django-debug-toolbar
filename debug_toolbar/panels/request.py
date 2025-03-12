from django.http import Http404
from django.urls import resolve
from django.utils.translation import gettext_lazy as _

from debug_toolbar.panels import Panel
from debug_toolbar.utils import (
    get_name_from_obj,
    get_sorted_request_variable,
    sanitize_value,
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
        from debug_toolbar import settings as dt_settings

        self.record_stats(
            {
                "get": get_sorted_request_variable(request.GET),
                "post": get_sorted_request_variable(request.POST),
                "cookies": get_sorted_request_variable(request.COOKIES),
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

        # Handle session data with sanitization
        if hasattr(request, "session"):
            sanitize_request_data = dt_settings.get_config().get(
                "SANITIZE_REQUEST_DATA", True
            )

            try:
                if sanitize_request_data:
                    session_list = []
                    for k in sorted(request.session.keys()):
                        v = request.session.get(k)
                        sanitized_v = sanitize_value(k, v)
                        session_list.append((k, sanitized_v))
                else:
                    session_list = [
                        (k, request.session.get(k))
                        for k in sorted(request.session.keys())
                    ]
            except TypeError:
                # Handle non-dict session objects
                if sanitize_request_data:
                    session_list = []
                    for k in request.session.keys():
                        v = request.session.get(k)
                        sanitized_v = sanitize_value(k, v)
                        session_list.append((k, sanitized_v))
                else:
                    session_list = [
                        (k, request.session.get(k)) for k in request.session.keys()
                    ]

            self.record_stats({"session": {"list": session_list}})
