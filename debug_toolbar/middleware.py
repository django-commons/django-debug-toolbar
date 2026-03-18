"""
Debug Toolbar middleware
"""

import re
import socket
from collections.abc import Callable
from functools import cache

from asgiref.sync import (
    async_to_sync,
    iscoroutinefunction,
    markcoroutinefunction,
    sync_to_async,
)
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.module_loading import import_string

from debug_toolbar import settings as dt_settings
from debug_toolbar._stubs import GetResponse
from debug_toolbar.panels import Panel
from debug_toolbar.toolbar import DebugToolbar
from debug_toolbar.utils import clear_stack_trace_caches, is_processable_html_response

_HTML_TYPES = ("text/html", "application/xhtml+xml")


def show_toolbar(request: HttpRequest) -> bool:
    """
    Default function to determine whether to show the toolbar on a given page.
    """
    if not settings.DEBUG:
        return False

    # Test: settings
    if request.META.get("REMOTE_ADDR") in settings.INTERNAL_IPS:
        return True

    # No test passed
    return False


def show_toolbar_with_docker(request: HttpRequest) -> bool:
    """
    Default function to determine whether to show the toolbar on a given page.
    """
    if not settings.DEBUG:
        return False

    # Test: settings
    if request.META.get("REMOTE_ADDR") in settings.INTERNAL_IPS:
        return True

    # Test: Docker
    try:
        # This is a hack for docker installations. It attempts to look
        # up the IP address of the docker host.
        # This is not guaranteed to work.
        docker_ip = (
            # Convert the last segment of the IP address to be .1
            ".".join(socket.gethostbyname("host.docker.internal").rsplit(".")[:-1])
            + ".1"
        )
        if request.META.get("REMOTE_ADDR") == docker_ip:
            return True
    except socket.gaierror:
        # It's fine if the lookup errored since they may not be using docker
        pass

    # No test passed
    return False


@cache
def show_toolbar_func_or_path() -> Callable:
    """
    Fetch the show toolbar callback from settings

    Cached to avoid importing multiple times.
    """
    # If SHOW_TOOLBAR_CALLBACK is a string, which is the recommended
    # setup, resolve it to the corresponding callable.
    func_or_path = dt_settings.get_config()["SHOW_TOOLBAR_CALLBACK"]
    if isinstance(func_or_path, str):
        return import_string(func_or_path)
    else:
        return func_or_path


def get_show_toolbar(async_mode) -> Callable:
    """
    Get the callback function to show the toolbar.

    Will wrap the function with sync_to_async or
    async_to_sync depending on the status of async_mode
    and whether the underlying function is a coroutine.
    """
    show_toolbar = show_toolbar_func_or_path()
    is_coroutine = iscoroutinefunction(show_toolbar)
    if is_coroutine and not async_mode:
        show_toolbar = async_to_sync(show_toolbar)
    elif not is_coroutine and async_mode:
        show_toolbar = sync_to_async(show_toolbar)
    return show_toolbar


class DebugToolbarMiddleware:
    """
    Middleware to set up Debug Toolbar on incoming request and render toolbar
    on outgoing response.
    """

    sync_capable = True
    async_capable = True

    def __init__(self, get_response: GetResponse):
        self.get_response = get_response
        # If get_response is a coroutine function, turns us into async mode so
        # a thread is not consumed during a whole request.
        self.async_mode = iscoroutinefunction(self.get_response)

        if self.async_mode:
            # Mark the class as async-capable, but do the actual switch inside
            # __call__ to avoid swapping out dunder methods.
            markcoroutinefunction(self)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if self.async_mode:
            return self.__acall__(request)

        # Decide whether the toolbar is active for this request.
        show_toolbar = get_show_toolbar(async_mode=self.async_mode)

        if not show_toolbar(request) or DebugToolbar.is_toolbar_request(request):
            return self.get_response(request)
        toolbar = DebugToolbar(request, self.get_response)
        # Activate instrumentation ie. monkey-patch.
        for panel in toolbar.enabled_panels:
            panel.enable_instrumentation()
        try:
            # Run panels like Django middleware.
            response = toolbar.process_request(request)
        finally:
            clear_stack_trace_caches()
            # Deactivate instrumentation ie. monkey-unpatch. This must run
            # regardless of the response. Keep 'return' clauses below.
            for panel in reversed(toolbar.enabled_panels):
                panel.disable_instrumentation()

        return self._postprocess(request, response, toolbar)

    async def __acall__(self, request: HttpRequest) -> HttpResponse:
        # Decide whether the toolbar is active for this request.
        show_toolbar = get_show_toolbar(async_mode=self.async_mode)

        if not await show_toolbar(request) or DebugToolbar.is_toolbar_request(request):
            response = await self.get_response(request)
            return response

        toolbar = DebugToolbar(request, self.get_response)

        # Activate instrumentation ie. monkey-patch.
        for panel in toolbar.enabled_panels:
            if hasattr(panel, "aenable_instrumentation"):
                await panel.aenable_instrumentation()
            else:
                panel.enable_instrumentation()
        try:
            # Run panels like Django middleware.
            response = await toolbar.process_request(request)
        finally:
            clear_stack_trace_caches()
            # Deactivate instrumentation ie. monkey-unpatch. This must run
            # regardless of the response. Keep 'return' clauses below.
            for panel in reversed(toolbar.enabled_panels):
                panel.disable_instrumentation()

        return self._postprocess(request, response, toolbar)

    def _postprocess(
        self, request: HttpRequest, response: HttpResponse, toolbar: DebugToolbar
    ) -> HttpResponse:
        """
        Post-process the response.
        """
        # Generate the stats for all requests when the toolbar is being shown,
        # but not necessarily inserted.
        for panel in reversed(toolbar.enabled_panels):
            panel.generate_stats(request, response)
            panel.generate_server_timing(request, response)

        # Always render the toolbar for the history panel, even if it is not
        # included in the response.
        rendered = toolbar.render_toolbar()

        for header, value in self.get_headers(request, toolbar.enabled_panels).items():
            response.headers[header] = value

        # Check for responses where the toolbar can't be inserted.
        if not is_processable_html_response(response):
            return response

        # Insert the toolbar in the response.
        content = response.content.decode(response.charset)
        insert_before = dt_settings.get_config()["INSERT_BEFORE"]
        pattern = re.escape(insert_before)
        bits = re.split(pattern, content, flags=re.IGNORECASE)
        if len(bits) > 1:
            bits[-2] += rendered
            response.content = insert_before.join(bits)
            if "Content-Length" in response:
                response["Content-Length"] = len(response.content)
        return response

    @staticmethod
    def get_headers(request: HttpRequest, panels: list[Panel]) -> dict[str, str]:
        headers = {}
        for panel in panels:
            for header, value in panel.get_headers(request).items():
                if header in headers:
                    headers[header] += f", {value}"
                else:
                    headers[header] = value
        return headers
