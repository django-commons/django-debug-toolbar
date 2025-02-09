from __future__ import annotations

from typing import cast
from xml.etree.ElementTree import Element

from django.conf import settings
from django.http.response import HttpResponse
from django.test.utils import override_settings
from html5lib.constants import E
from html5lib.html5parser import HTMLParser

from debug_toolbar.store import get_store
from debug_toolbar.toolbar import DebugToolbar

from .base import IntegrationTestCase


def get_namespaces(element: Element) -> dict[str, str]:
    """
    Return the default `xmlns`. See
    https://docs.python.org/3/library/xml.etree.elementtree.html#parsing-xml-with-namespaces
    """
    if not element.tag.startswith("{"):
        return {}
    return {"": element.tag[1:].split("}", maxsplit=1)[0]}


@override_settings(DEBUG=True)
class CspRenderingTestCase(IntegrationTestCase):
    """Testing if `csp-nonce` renders."""

    def setUp(self):
        super().setUp()
        self.parser = HTMLParser()

    def _fail_if_missing(
        self, root: Element, path: str, namespaces: dict[str, str], nonce: str
    ):
        """
        Search elements, fail if a `nonce` attribute is missing on them.
        """
        elements = root.findall(path=path, namespaces=namespaces)
        for item in elements:
            if item.attrib.get("nonce") != nonce:
                raise self.failureException(f"{item} has no nonce attribute.")

    def _fail_if_found(self, root: Element, path: str, namespaces: dict[str, str]):
        """
        Search elements, fail if a `nonce` attribute is found on them.
        """
        elements = root.findall(path=path, namespaces=namespaces)
        for item in elements:
            if "nonce" in item.attrib:
                raise self.failureException(f"{item} has a nonce attribute.")

    def _fail_on_invalid_html(self, content: bytes, parser: HTMLParser):
        """Fail if the passed HTML is invalid."""
        if parser.errors:
            default_msg = ["Content is invalid HTML:"]
            lines = content.split(b"\n")
            for position, error_code, data_vars in parser.errors:
                default_msg.append(f"  {E[error_code]}" % data_vars)
                default_msg.append(f"    {lines[position[0] - 1]!r}")
            msg = self._formatMessage(None, "\n".join(default_msg))
            raise self.failureException(msg)

    @override_settings(
        MIDDLEWARE=settings.MIDDLEWARE + ["csp.middleware.CSPMiddleware"]
    )
    def test_exists(self):
        """A `nonce` should exist when using the `CSPMiddleware`."""
        response = cast(HttpResponse, self.client.get(path="/regular/basic/"))
        self.assertEqual(response.status_code, 200)

        html_root: Element = self.parser.parse(stream=response.content)
        self._fail_on_invalid_html(content=response.content, parser=self.parser)
        self.assertContains(response, "djDebug")

        namespaces = get_namespaces(element=html_root)
        nonce = response.context["request"].csp_nonce
        self._fail_if_missing(
            root=html_root, path=".//link", namespaces=namespaces, nonce=nonce
        )
        self._fail_if_missing(
            root=html_root, path=".//script", namespaces=namespaces, nonce=nonce
        )

    @override_settings(
        DEBUG_TOOLBAR_CONFIG={"DISABLE_PANELS": set()},
        MIDDLEWARE=settings.MIDDLEWARE + ["csp.middleware.CSPMiddleware"],
    )
    def test_redirects_exists(self):
        response = cast(HttpResponse, self.client.get(path="/regular/basic/"))
        self.assertEqual(response.status_code, 200)

        html_root: Element = self.parser.parse(stream=response.content)
        self._fail_on_invalid_html(content=response.content, parser=self.parser)
        self.assertContains(response, "djDebug")

        namespaces = get_namespaces(element=html_root)
        nonce = response.context["request"].csp_nonce
        self._fail_if_missing(
            root=html_root, path=".//link", namespaces=namespaces, nonce=nonce
        )
        self._fail_if_missing(
            root=html_root, path=".//script", namespaces=namespaces, nonce=nonce
        )

    @override_settings(
        MIDDLEWARE=settings.MIDDLEWARE + ["csp.middleware.CSPMiddleware"]
    )
    def test_panel_content_nonce_exists(self):
        store = get_store()
        response = cast(HttpResponse, self.client.get(path="/regular/basic/"))
        self.assertEqual(response.status_code, 200)
        nonce = response.context["request"].csp_nonce

        request_ids = list(store.request_ids())
        toolbar = DebugToolbar.fetch(request_ids[0])
        panels_to_check = ["HistoryPanel", "TimerPanel"]
        for panel in panels_to_check:
            content = toolbar.get_panel_by_id(panel).content
            html_root: Element = self.parser.parse(stream=content)
            namespaces = get_namespaces(element=html_root)
            self._fail_if_missing(
                root=html_root, path=".//link", namespaces=namespaces, nonce=nonce
            )
            self._fail_if_missing(
                root=html_root, path=".//script", namespaces=namespaces, nonce=nonce
            )

    def test_missing(self):
        """A `nonce` should not exist when not using the `CSPMiddleware`."""
        response = cast(HttpResponse, self.client.get(path="/regular/basic/"))
        self.assertEqual(response.status_code, 200)

        html_root: Element = self.parser.parse(stream=response.content)
        self._fail_on_invalid_html(content=response.content, parser=self.parser)
        self.assertContains(response, "djDebug")

        namespaces = get_namespaces(element=html_root)
        self._fail_if_found(root=html_root, path=".//link", namespaces=namespaces)
        self._fail_if_found(root=html_root, path=".//script", namespaces=namespaces)
