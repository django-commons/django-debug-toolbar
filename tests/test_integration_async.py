import unittest
from unittest.mock import patch

import html5lib
from django.core import signing
from django.core.cache import cache
from django.db import connection
from django.http import HttpResponse
from django.template.loader import get_template
from django.test import AsyncRequestFactory
from django.test.utils import override_settings

from debug_toolbar.forms import SignedDataForm
from debug_toolbar.middleware import DebugToolbarMiddleware, show_toolbar
from debug_toolbar.panels import Panel
from debug_toolbar.toolbar import DebugToolbar

from .base import BaseTestCase, IntegrationTestCase
from .views import regular_view

arf = AsyncRequestFactory()


def toolbar_store_id():
    def get_response(request):
        return HttpResponse()

    toolbar = DebugToolbar(arf.get("/"), get_response)
    toolbar.store()
    return toolbar.store_id


class BuggyPanel(Panel):
    def title(self):
        return "BuggyPanel"

    @property
    def content(self):
        raise Exception


@override_settings(DEBUG=True)
class DebugToolbarTestCase(BaseTestCase):
    _is_async = True

    def test_show_toolbar(self):
        """
        Just to verify that show_toolbar() works with an ASGIRequest too
        """

        self.assertTrue(show_toolbar(self.request))

    async def test_show_toolbar_INTERNAL_IPS(self):
        with self.settings(INTERNAL_IPS=[]):
            self.assertFalse(show_toolbar(self.request))

    @patch("socket.gethostbyname", return_value="192.168.65.1")
    async def test_show_toolbar_docker(self, mocked_gethostbyname):
        with self.settings(INTERNAL_IPS=[]):
            self.request.META["REMOTE_ADDR"] = "192.168.65.1"
            self.assertTrue(show_toolbar(self.request))
        mocked_gethostbyname.assert_called_once_with("gateway.docker.internal")

    async def test_not_iterating_over_INTERNAL_IPS(self):
        """
        Verify that the middleware does not iterate over INTERNAL_IPS in some way.

        Some people use iptools.IpRangeList for their INTERNAL_IPS. This is a class
        that can quickly answer the question if the setting contain a certain IP address,
        but iterating over this object will drain all performance / blow up.
        """

        class FailOnIteration:
            def __iter__(self):
                raise RuntimeError(
                    "The testcase failed: the code should not have iterated over INTERNAL_IPS"
                )

            def __contains__(self, x):
                return True

        with self.settings(INTERNAL_IPS=FailOnIteration()):
            response = await self.async_client.get("/regular/basic/")
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "djDebug")  # toolbar

    async def test_middleware_response_insertion(self):
        async def get_response(request):
            return regular_view(request, "İ")

        response = await DebugToolbarMiddleware(get_response)(self.request)
        # check toolbar insertion before "</body>"
        self.assertContains(response, "</div>\n</body>")

    async def test_middleware_no_injection_when_encoded(self):
        async def get_response(request):
            response = HttpResponse("<html><body></body></html>")
            response["Content-Encoding"] = "something"
            return response

        response = await DebugToolbarMiddleware(get_response)(self.request)
        self.assertEqual(response.content, b"<html><body></body></html>")

    async def test_cache_page(self):
        # Clear the cache before testing the views. Other tests that use cached_view
        # may run earlier and cause fewer cache calls.
        cache.clear()
        response = await self.async_client.get("/cached_view/")
        self.assertEqual(len(response.toolbar.get_panel_by_id("CachePanel").calls), 3)
        response = await self.async_client.get("/cached_view/")
        self.assertEqual(len(response.toolbar.get_panel_by_id("CachePanel").calls), 2)

    @override_settings(ROOT_URLCONF="tests.urls_use_package_urls")
    async def test_include_package_urls(self):
        """Test urlsconf that uses the debug_toolbar.urls in the include call"""
        # Clear the cache before testing the views. Other tests that use cached_view
        # may run earlier and cause fewer cache calls.
        cache.clear()
        response = await self.async_client.get("/cached_view/")
        self.assertEqual(len(response.toolbar.get_panel_by_id("CachePanel").calls), 3)
        response = await self.async_client.get("/cached_view/")
        self.assertEqual(len(response.toolbar.get_panel_by_id("CachePanel").calls), 2)

    async def test_low_level_cache_view(self):
        """Test cases when low level caching API is used within a request."""
        response = await self.async_client.get("/cached_low_level_view/")
        self.assertEqual(len(response.toolbar.get_panel_by_id("CachePanel").calls), 2)
        response = await self.async_client.get("/cached_low_level_view/")
        self.assertEqual(len(response.toolbar.get_panel_by_id("CachePanel").calls), 1)

    async def test_cache_disable_instrumentation(self):
        """
        Verify that middleware cache usages before and after
        DebugToolbarMiddleware are not counted.
        """
        self.assertIsNone(cache.set("UseCacheAfterToolbar.before", None))
        self.assertIsNone(cache.set("UseCacheAfterToolbar.after", None))
        response = await self.async_client.get("/execute_sql/")
        self.assertEqual(cache.get("UseCacheAfterToolbar.before"), 1)
        self.assertEqual(cache.get("UseCacheAfterToolbar.after"), 1)
        self.assertEqual(len(response.toolbar.get_panel_by_id("CachePanel").calls), 0)

    async def test_is_toolbar_request(self):
        request = arf.get("/__debug__/render_panel/")
        self.assertTrue(self.toolbar.is_toolbar_request(request))

        request = arf.get("/invalid/__debug__/render_panel/")
        self.assertFalse(self.toolbar.is_toolbar_request(request))

        request = arf.get("/render_panel/")
        self.assertFalse(self.toolbar.is_toolbar_request(request))

    @override_settings(ROOT_URLCONF="tests.urls_invalid")
    async def test_is_toolbar_request_without_djdt_urls(self):
        """Test cases when the toolbar urls aren't configured."""
        request = arf.get("/__debug__/render_panel/")
        self.assertFalse(self.toolbar.is_toolbar_request(request))

        request = arf.get("/render_panel/")
        self.assertFalse(self.toolbar.is_toolbar_request(request))

    @override_settings(ROOT_URLCONF="tests.urls_invalid")
    async def test_is_toolbar_request_override_request_urlconf(self):
        """Test cases when the toolbar URL is configured on the request."""
        request = arf.get("/__debug__/render_panel/")
        self.assertFalse(self.toolbar.is_toolbar_request(request))

        # Verify overriding the urlconf on the request is valid.
        request.urlconf = "tests.urls"
        self.assertTrue(self.toolbar.is_toolbar_request(request))

    async def test_is_toolbar_request_with_script_prefix(self):
        """
        Test cases when Django is running under a path prefix, such as via the
        FORCE_SCRIPT_NAME setting.
        """
        request = arf.get("/__debug__/render_panel/", SCRIPT_NAME="/path/")
        self.assertTrue(self.toolbar.is_toolbar_request(request))

        request = arf.get("/invalid/__debug__/render_panel/", SCRIPT_NAME="/path/")
        self.assertFalse(self.toolbar.is_toolbar_request(request))

        request = arf.get("/render_panel/", SCRIPT_NAME="/path/")
        self.assertFalse(self.toolbar.is_toolbar_request(self.request))

    async def test_data_gone(self):
        response = await self.async_client.get(
            "/__debug__/render_panel/?store_id=GONE&panel_id=RequestPanel"
        )
        self.assertIn("Please reload the page and retry.", response.json()["content"])

    async def test_sql_page(self):
        response = await self.async_client.get("/execute_sql/")
        self.assertEqual(
            len(response.toolbar.get_panel_by_id("SQLPanel").get_stats()["queries"]), 1
        )

    async def test_async_sql_page(self):
        response = await self.async_client.get("/async_execute_sql/")
        self.assertEqual(
            len(response.toolbar.get_panel_by_id("SQLPanel").get_stats()["queries"]), 2
        )


# Concurrent database queries are not fully supported by Django's backend with
# current integrated database drivers like psycopg2
# (considering postgresql as an example) and
# support for async drivers like psycopg3 isn't integrated yet.
# As a result, regardless of ASGI/async or WSGI/sync or any other attempts to make
# concurrent database queries like tests/views/async_db_concurrent,
# Django will still execute them synchronously.

# Check out the following links for more information:

# https://forum.djangoproject.com/t/are-concurrent-database-queries-in-asgi-a-thing/24136/2
# https://github.com/django-commons/django-debug-toolbar/issues/1828

# Work that is done so far for asynchrounous database backend
# https://github.com/django/deps/blob/main/accepted/0009-async.rst#the-orm


@override_settings(DEBUG=True)
class DebugToolbarIntegrationTestCase(IntegrationTestCase):
    async def test_middleware_in_async_mode(self):
        response = await self.async_client.get("/async_execute_sql/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "djDebug")

    @override_settings(DEFAULT_CHARSET="iso-8859-1")
    async def test_non_utf8_charset(self):
        response = await self.async_client.get("/regular/ASCII/")
        self.assertContains(response, "ASCII")  # template
        self.assertContains(response, "djDebug")  # toolbar

        response = await self.async_client.get("/regular/ASCII/")

        self.assertContains(response, "ASCII")  # template
        self.assertContains(response, "djDebug")  # toolbar

    async def test_html5_validation(self):
        response = await self.async_client.get("/regular/HTML5/")
        parser = html5lib.HTMLParser()
        content = response.content
        parser.parse(content)
        if parser.errors:
            default_msg = ["Content is invalid HTML:"]
            lines = content.split(b"\n")
            for position, errorcode, datavars in parser.errors:
                default_msg.append(f"  {html5lib.constants.E[errorcode]}" % datavars)
                default_msg.append(f"    {lines[position[0] - 1]!r}")
            msg = self._formatMessage(None, "\n".join(default_msg))
            raise self.failureException(msg)

    async def test_render_panel_checks_show_toolbar(self):
        url = "/__debug__/render_panel/"
        data = {"store_id": toolbar_store_id(), "panel_id": "VersionsPanel"}

        response = await self.async_client.get(url, data)
        self.assertEqual(response.status_code, 200)

        with self.settings(INTERNAL_IPS=[]):
            response = await self.async_client.get(url, data)
            self.assertEqual(response.status_code, 404)

    async def test_middleware_render_toolbar_json(self):
        """Verify the toolbar is rendered and data is stored for a json request."""
        self.assertEqual(len(DebugToolbar._store), 0)

        data = {"foo": "bar"}
        response = await self.async_client.get(
            "/json_view/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), '{"foo": "bar"}')
        # Check the history panel's stats to verify the toolbar rendered properly.
        self.assertEqual(len(DebugToolbar._store), 1)
        toolbar = list(DebugToolbar._store.values())[0]
        self.assertEqual(
            toolbar.get_panel_by_id("HistoryPanel").get_stats()["data"],
            {"foo": ["bar"]},
        )

    async def test_template_source_checks_show_toolbar(self):
        template = get_template("basic.html")
        url = "/__debug__/template_source/"
        data = {
            "template": template.template.name,
            "template_origin": signing.dumps(template.template.origin.name),
        }

        response = await self.async_client.get(url, data)
        self.assertEqual(response.status_code, 200)
        with self.settings(INTERNAL_IPS=[]):
            response = await self.async_client.get(url, data)
            self.assertEqual(response.status_code, 404)

    async def test_template_source_errors(self):
        url = "/__debug__/template_source/"

        response = await self.async_client.get(url, {})
        self.assertContains(
            response, '"template_origin" key is required', status_code=400
        )

        template = get_template("basic.html")
        response = await self.async_client.get(
            url,
            {"template_origin": signing.dumps(template.template.origin.name) + "xyz"},
        )
        self.assertContains(response, '"template_origin" is invalid', status_code=400)

        response = await self.async_client.get(
            url, {"template_origin": signing.dumps("does_not_exist.html")}
        )
        self.assertContains(response, "Template Does Not Exist: does_not_exist.html")

    async def test_sql_select_checks_show_toolbar(self):
        url = "/__debug__/sql_select/"
        data = {
            "signed": SignedDataForm.sign(
                {
                    "sql": "SELECT * FROM auth_user",
                    "raw_sql": "SELECT * FROM auth_user",
                    "params": "{}",
                    "alias": "default",
                    "duration": "0",
                }
            )
        }

        response = await self.async_client.post(url, data)
        self.assertEqual(response.status_code, 200)
        with self.settings(INTERNAL_IPS=[]):
            response = await self.async_client.post(url, data)
            self.assertEqual(response.status_code, 404)

    async def test_sql_explain_checks_show_toolbar(self):
        url = "/__debug__/sql_explain/"
        data = {
            "signed": SignedDataForm.sign(
                {
                    "sql": "SELECT * FROM auth_user",
                    "raw_sql": "SELECT * FROM auth_user",
                    "params": "{}",
                    "alias": "default",
                    "duration": "0",
                }
            )
        }

        response = await self.async_client.post(url, data)
        self.assertEqual(response.status_code, 200)
        with self.settings(INTERNAL_IPS=[]):
            response = await self.async_client.post(url, data)
            self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(
        connection.vendor == "postgresql", "Test valid only on PostgreSQL"
    )
    async def test_sql_explain_postgres_union_query(self):
        """
        Confirm select queries that start with a parenthesis can be explained.
        """
        url = "/__debug__/sql_explain/"
        data = {
            "signed": SignedDataForm.sign(
                {
                    "sql": "(SELECT * FROM auth_user) UNION (SELECT * from auth_user)",
                    "raw_sql": "(SELECT * FROM auth_user) UNION (SELECT * from auth_user)",
                    "params": "{}",
                    "alias": "default",
                    "duration": "0",
                }
            )
        }

        response = await self.async_client.post(url, data)
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(
        connection.vendor == "postgresql", "Test valid only on PostgreSQL"
    )
    async def test_sql_explain_postgres_json_field(self):
        url = "/__debug__/sql_explain/"
        base_query = (
            'SELECT * FROM "tests_postgresjson" WHERE "tests_postgresjson"."field" @>'
        )
        query = base_query + """ '{"foo": "bar"}'"""
        data = {
            "signed": SignedDataForm.sign(
                {
                    "sql": query,
                    "raw_sql": base_query + " %s",
                    "params": '["{\\"foo\\": \\"bar\\"}"]',
                    "alias": "default",
                    "duration": "0",
                }
            )
        }
        response = await self.async_client.post(url, data)
        self.assertEqual(response.status_code, 200)
        with self.settings(INTERNAL_IPS=[]):
            response = await self.async_client.post(url, data)
            self.assertEqual(response.status_code, 404)

    async def test_sql_profile_checks_show_toolbar(self):
        url = "/__debug__/sql_profile/"
        data = {
            "signed": SignedDataForm.sign(
                {
                    "sql": "SELECT * FROM auth_user",
                    "raw_sql": "SELECT * FROM auth_user",
                    "params": "{}",
                    "alias": "default",
                    "duration": "0",
                }
            )
        }

        response = await self.async_client.post(url, data)
        self.assertEqual(response.status_code, 200)
        with self.settings(INTERNAL_IPS=[]):
            response = await self.async_client.post(url, data)
            self.assertEqual(response.status_code, 404)

    @override_settings(DEBUG_TOOLBAR_CONFIG={"RENDER_PANELS": True})
    async def test_render_panels_in_request(self):
        """
        Test that panels are are rendered during the request with
        RENDER_PANELS=TRUE
        """
        url = "/regular/basic/"
        response = await self.async_client.get(url)
        self.assertIn(b'id="djDebug"', response.content)
        # Verify the store id is not included.
        self.assertNotIn(b"data-store-id", response.content)
        # Verify the history panel was disabled
        self.assertIn(
            b'<input type="checkbox" data-cookie="djdtHistoryPanel" '
            b'title="Enable for next and successive requests">',
            response.content,
        )
        # Verify the a panel was rendered
        self.assertIn(b"Response headers", response.content)

    @override_settings(DEBUG_TOOLBAR_CONFIG={"RENDER_PANELS": False})
    async def test_load_panels(self):
        """
        Test that panels are not rendered during the request with
        RENDER_PANELS=False
        """
        url = "/execute_sql/"
        response = await self.async_client.get(url)
        self.assertIn(b'id="djDebug"', response.content)
        # Verify the store id is included.
        self.assertIn(b"data-store-id", response.content)
        # Verify the history panel was not disabled
        self.assertNotIn(
            b'<input type="checkbox" data-cookie="djdtHistoryPanel" '
            b'title="Enable for next and successive requests">',
            response.content,
        )
        # Verify the a panel was not rendered
        self.assertNotIn(b"Response headers", response.content)

    async def test_view_returns_template_response(self):
        response = await self.async_client.get("/template_response/basic/")
        self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG_TOOLBAR_CONFIG={"DISABLE_PANELS": set()})
    async def test_intercept_redirects(self):
        response = await self.async_client.get("/redirect/")
        self.assertEqual(response.status_code, 200)
        # Link to LOCATION header.
        self.assertIn(b'href="/regular/redirect/"', response.content)

    async def test_auth_login_view_without_redirect(self):
        response = await self.async_client.get("/login_without_redirect/")
        self.assertEqual(response.status_code, 200)
        parser = html5lib.HTMLParser()
        doc = parser.parse(response.content)
        el = doc.find(".//*[@id='djDebug']")
        store_id = el.attrib["data-store-id"]
        response = await self.async_client.get(
            "/__debug__/render_panel/",
            {"store_id": store_id, "panel_id": "TemplatesPanel"},
        )
        self.assertEqual(response.status_code, 200)
        # The key None (without quotes) exists in the list of template
        # variables.
        self.assertIn("None: &#x27;&#x27;", response.json()["content"])
