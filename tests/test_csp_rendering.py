from __future__ import annotations

from django.conf import settings
from django.test.utils import override_settings
from html5lib.constants import E
from html5lib.html5parser import HTMLParser

from debug_toolbar.toolbar import DebugToolbar

from .base import IntegrationTestCase

MIDDLEWARE_CSP_BEFORE = settings.MIDDLEWARE.copy()
MIDDLEWARE_CSP_BEFORE.insert(
    MIDDLEWARE_CSP_BEFORE.index("debug_toolbar.middleware.DebugToolbarMiddleware"),
    "csp.middleware.CSPMiddleware",
)
MIDDLEWARE_CSP_LAST = settings.MIDDLEWARE + ["csp.middleware.CSPMiddleware"]


def get_namespaces(element):
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

    def _fail_if_missing(self, root, path, namespaces, nonce):
        """
        Search elements, fail if a `nonce` attribute is missing on them.
        """
        elements = root.findall(path=path, namespaces=namespaces)
        for item in elements:
            if item.attrib.get("nonce") != nonce:
                raise self.failureException(f"{item} has no nonce attribute.")

    def _fail_if_found(self, root, path, namespaces):
        """
        Search elements, fail if a `nonce` attribute is found on them.
        """
        elements = root.findall(path=path, namespaces=namespaces)
        for item in elements:
            if "nonce" in item.attrib:
                raise self.failureException(f"{item} has a nonce attribute.")

    def _fail_on_invalid_html(self, content, parser):
        """Fail if the passed HTML is invalid."""
        if parser.errors:
            default_msg = ["Content is invalid HTML:"]
            lines = content.split(b"\n")
            for position, error_code, data_vars in parser.errors:
                default_msg.append(f"  {E[error_code]}" % data_vars)
                default_msg.append(f"    {lines[position[0] - 1]!r}")
            msg = self._formatMessage(None, "\n".join(default_msg))
            raise self.failureException(msg)

    def test_exists(self):
        """A `nonce` should exist when using the `CSPMiddleware`."""
        for middleware in [MIDDLEWARE_CSP_BEFORE, MIDDLEWARE_CSP_LAST]:
            with self.settings(MIDDLEWARE=middleware):
                response = self.client.get(path="/csp_view/")
                self.assertEqual(response.status_code, 200)

                html_root = self.parser.parse(stream=response.content)
                self._fail_on_invalid_html(content=response.content, parser=self.parser)
                self.assertContains(response, "djDebug")

                namespaces = get_namespaces(element=html_root)
                toolbar = list(DebugToolbar._store.values())[-1]
                nonce = str(toolbar.csp_nonce)
                self._fail_if_missing(
                    root=html_root, path=".//link", namespaces=namespaces, nonce=nonce
                )
                self._fail_if_missing(
                    root=html_root, path=".//script", namespaces=namespaces, nonce=nonce
                )

    def test_does_not_exist_nonce_wasnt_used(self):
        """
        A `nonce` should not exist even when using the `CSPMiddleware`
        if the view didn't access the request.csp_nonce attribute.
        """
        for middleware in [MIDDLEWARE_CSP_BEFORE, MIDDLEWARE_CSP_LAST]:
            with self.settings(MIDDLEWARE=middleware):
                response = self.client.get(path="/regular/basic/")
                self.assertEqual(response.status_code, 200)

                html_root = self.parser.parse(stream=response.content)
                self._fail_on_invalid_html(content=response.content, parser=self.parser)
                self.assertContains(response, "djDebug")

                namespaces = get_namespaces(element=html_root)
                self._fail_if_found(
                    root=html_root, path=".//link", namespaces=namespaces
                )
                self._fail_if_found(
                    root=html_root, path=".//script", namespaces=namespaces
                )

    @override_settings(
        DEBUG_TOOLBAR_CONFIG={"DISABLE_PANELS": set()},
    )
    def test_redirects_exists(self):
        for middleware in [MIDDLEWARE_CSP_BEFORE, MIDDLEWARE_CSP_LAST]:
            with self.settings(MIDDLEWARE=middleware):
                response = self.client.get(path="/csp_view/")
                self.assertEqual(response.status_code, 200)

                html_root = self.parser.parse(stream=response.content)
                self._fail_on_invalid_html(content=response.content, parser=self.parser)
                self.assertContains(response, "djDebug")

                namespaces = get_namespaces(element=html_root)
                context = response.context
                nonce = str(context["toolbar"].csp_nonce)
                self._fail_if_missing(
                    root=html_root, path=".//link", namespaces=namespaces, nonce=nonce
                )
                self._fail_if_missing(
                    root=html_root, path=".//script", namespaces=namespaces, nonce=nonce
                )

    def test_panel_content_nonce_exists(self):
        for middleware in [MIDDLEWARE_CSP_BEFORE, MIDDLEWARE_CSP_LAST]:
            with self.settings(MIDDLEWARE=middleware):
                response = self.client.get(path="/csp_view/")
                self.assertEqual(response.status_code, 200)

                toolbar = list(DebugToolbar._store.values())[-1]
                panels_to_check = ["HistoryPanel", "TimerPanel"]
                for panel in panels_to_check:
                    content = toolbar.get_panel_by_id(panel).content
                    html_root = self.parser.parse(stream=content)
                    namespaces = get_namespaces(element=html_root)
                    nonce = str(toolbar.csp_nonce)
                    self._fail_if_missing(
                        root=html_root,
                        path=".//link",
                        namespaces=namespaces,
                        nonce=nonce,
                    )
                    self._fail_if_missing(
                        root=html_root,
                        path=".//script",
                        namespaces=namespaces,
                        nonce=nonce,
                    )

    def test_missing(self):
        """A `nonce` should not exist when not using the `CSPMiddleware`."""
        response = self.client.get(path="/regular/basic/")
        self.assertEqual(response.status_code, 200)

        html_root = self.parser.parse(stream=response.content)
        self._fail_on_invalid_html(content=response.content, parser=self.parser)
        self.assertContains(response, "djDebug")

        namespaces = get_namespaces(element=html_root)
        self._fail_if_found(root=html_root, path=".//link", namespaces=namespaces)
        self._fail_if_found(root=html_root, path=".//script", namespaces=namespaces)
