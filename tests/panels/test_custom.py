from django.test import override_settings

from debug_toolbar.panels import Panel

from ..base import IntegrationTestCase


class CustomPanel(Panel):
    def title(self):
        return "Title with special chars &\"'<>"


@override_settings(
    DEBUG=True, DEBUG_TOOLBAR_PANELS=["tests.panels.test_custom.CustomPanel"]
)
class CustomPanelTestCase(IntegrationTestCase):
    def test_escapes_panel_title(self):
        response = self.client.get("/regular/basic/")
        self.assertContains(
            response,
            """
            <li id="djdt-CustomPanel" class="djDebugPanelButton">
            <input type="checkbox" checked title="Disable for next and successive requests" data-cookie="djdtCustomPanel">
            <a class="CustomPanel" href="#" title="Title with special chars &amp;&quot;&#39;&lt;&gt;">
            Title with special chars &amp;&quot;&#39;&lt;&gt;
            </a>
            </li>
            """,
            html=True,
        )
        self.assertContains(
            response,
            """
            <div id="CustomPanel" class="djdt-panelContent djdt-hidden">
            <div class="djDebugPanelTitle">
            <h3>Title with special chars &amp;&quot;&#39;&lt;&gt;</h3>
            <button type="button" class="djDebugClose">×</button>
            </div>
            <div class="djDebugPanelContent">
            <div class="djdt-loader"></div>
            <div class="djdt-scroll"></div>
            </div>
            </div>
            """,
            html=True,
        )
