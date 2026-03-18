import contextvars

import html5lib
from asgiref.local import Local
from django.http import HttpResponse
from django.test import (
    AsyncClient,
    AsyncRequestFactory,
    Client,
    RequestFactory,
    TestCase,
    TransactionTestCase,
)

from debug_toolbar.panels import Panel
from debug_toolbar.store import get_store
from debug_toolbar.toolbar import DebugToolbar

data_contextvar = contextvars.ContextVar("djdt_toolbar_test_client")


class ToolbarTestClient(Client):
    def request(self, **request):
        # Use a thread/async task context-local variable to guard against a
        # concurrent _created signal from a different thread/task.
        data = Local()
        data.toolbar = None

        def handle_toolbar_created(sender, toolbar=None, **kwargs):
            data.toolbar = toolbar

        DebugToolbar._created.connect(handle_toolbar_created)
        try:
            response = super().request(**request)
        finally:
            DebugToolbar._created.disconnect(handle_toolbar_created)
        response.toolbar = data.toolbar

        return response


class AsyncToolbarTestClient(AsyncClient):
    async def request(self, **request):
        # Use a thread/async task context-local variable to guard against a
        # concurrent _created signal from a different thread/task.
        # In cases testsuite will have both regular and async tests or
        # multiple async tests running in an eventloop making async_client calls.
        data_contextvar.set(None)

        def handle_toolbar_created(sender, toolbar=None, **kwargs):
            data_contextvar.set(toolbar)

        DebugToolbar._created.connect(handle_toolbar_created)
        try:
            response = await super().request(**request)
        finally:
            DebugToolbar._created.disconnect(handle_toolbar_created)
        response.toolbar = data_contextvar.get()

        return response


rf = RequestFactory()
arf = AsyncRequestFactory()


class BaseMixin:
    _is_async = False
    client_class = ToolbarTestClient
    async_client_class = AsyncToolbarTestClient

    panel: Panel | None = None
    panel_id = None

    def setUp(self):
        super().setUp()
        self._get_response = lambda request: HttpResponse()
        self.request = rf.get("/")
        if self._is_async:
            self.request = arf.get("/")
            self.toolbar = DebugToolbar(self.request, self.get_response_async)
        else:
            self.toolbar = DebugToolbar(self.request, self.get_response)
        self.toolbar.stats = {}

        if self.panel_id:
            self.panel = self.toolbar.get_panel_by_id(self.panel_id)
            self.panel.enable_instrumentation()
        else:
            self.panel = None

    def tearDown(self):
        if self.panel:
            self.panel.disable_instrumentation()
        super().tearDown()

    def get_response(self, request):
        return self._get_response(request)

    async def get_response_async(self, request):
        return self._get_response(request)

    def assertValidHTML(self, content):
        parser = html5lib.HTMLParser()
        parser.parseFragment(content)
        if parser.errors:
            msg_parts = ["Invalid HTML:"]
            lines = content.split("\n")
            for position, errorcode, datavars in parser.errors:
                msg_parts.append(f"  {html5lib.constants.E[errorcode]}" % datavars)
                msg_parts.append(f"    {lines[position[0] - 1]}")
            raise self.failureException("\n".join(msg_parts))

    def reload_stats(self):
        data = self.toolbar.store.panel(self.toolbar.request_id, self.panel_id)
        self.panel.load_stats_from_store(data)


class BaseTestCase(BaseMixin, TestCase):
    pass


class BaseMultiDBTestCase(BaseMixin, TransactionTestCase):
    databases = {"default", "replica"}


class IntegrationTestCase(TestCase):
    """Base TestCase for tests involving clients making requests."""

    def setUp(self):
        # The HistoryPanel keeps track of previous stores in memory.
        # This bleeds into other tests and violates their idempotency.
        # Clear the store before each test.
        get_store().clear()
        super().setUp()
