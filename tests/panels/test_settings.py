from django.test import RequestFactory, override_settings

from debug_toolbar.panels.settings import SettingsPanel

from ..base import BaseTestCase, IntegrationTestCase

rf = RequestFactory()


class SettingsPanelTestCase(BaseTestCase):
    panel_id = SettingsPanel.panel_id

    def test_panel_recording(self):
        self.request = rf.post("/", data={"foo": "bar"})
        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)

        settings = self.panel.get_stats()["settings"]
        self.assertEqual(settings["USE_THOUSAND_SEPARATOR"], "False")
        self.assertEqual(settings["ABSOLUTE_URL_OVERRIDES"], "{}")
        self.assertEqual(settings["EMAIL_HOST"], "'localhost'")
        self.assertEqual(settings["EMAIL_PORT"], "25")


@override_settings(DEBUG=True)
class SettingsIntegrationTestCase(IntegrationTestCase):
    def test_panel_title(self):
        response = self.client.get("/regular/basic/")
        # The settings module is None due to using Django's UserSettingsHolder
        # in tests.
        self.assertContains(
            response,
            """
            <li id="djdt-SettingsPanel" class="djDebugPanelButton">
            <input type="checkbox" checked title="Disable for next and successive requests" data-cookie="djdtSettingsPanel">
            <a class="SettingsPanel" href="#" title="Settings from None">Settings</a>
            </li>
            """,
            html=True,
        )
        self.assertContains(
            response,
            """
            <div id="SettingsPanel" class="djdt-panelContent djdt-hidden">
            <div class="djDebugPanelTitle">
            <h3>Settings from None</h3>
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
