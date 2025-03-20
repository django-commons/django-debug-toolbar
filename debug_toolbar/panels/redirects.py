from inspect import iscoroutine

from django.template.response import SimpleTemplateResponse
from django.utils.translation import gettext_lazy as _

from debug_toolbar.panels import Panel


class RedirectsPanel(Panel):
    """
    Panel that intercepts redirects and displays a page with debug info.
    """

    has_content = False

    is_async = True

    nav_title = _("Intercept redirects")

    def _process_response(self, response):
        """
        Common response processing logic.
        """
        if 300 <= response.status_code < 400:
            if redirect_to := response.get("Location"):
                response = self.get_interception_response(response, redirect_to)
                response.render()
        return response

    async def aprocess_request(self, request, response_coroutine):
        """
        Async version of process_request. used for accessing the response
        by awaiting it when running in ASGI.
        """

        response = await response_coroutine
        return self._process_response(response)

    def process_request(self, request):
        response = super().process_request(request)
        if iscoroutine(response):
            return self.aprocess_request(request, response)
        return self._process_response(response)

    def get_interception_response(self, response, redirect_to):
        """
        Hook method to allow subclasses to customize the interception response.
        """
        status_line = f"{response.status_code} {response.reason_phrase}"
        cookies = response.cookies
        original_response = response
        context = {
            "redirect_to": redirect_to,
            "status_line": status_line,
            "toolbar": self.toolbar,
            "original_response": original_response,
        }
        # Using SimpleTemplateResponse avoids running global context processors.
        response = SimpleTemplateResponse("debug_toolbar/redirect.html", context)
        response.cookies = cookies
        response.original_response = original_response
        return response
