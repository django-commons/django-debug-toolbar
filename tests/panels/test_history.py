import copy
import html

from django.test import RequestFactory, override_settings
from django.urls import resolve, reverse

from debug_toolbar.panels.history import HistoryPanel
from debug_toolbar.store import get_store
from debug_toolbar.toolbar import DebugToolbar

from ..base import BaseTestCase, IntegrationTestCase

rf = RequestFactory()


class HistoryPanelTestCase(BaseTestCase):
    panel_id = HistoryPanel.panel_id

    def test_disabled(self):
        config = {"DISABLE_PANELS": {"debug_toolbar.panels.history.HistoryPanel"}}
        self.assertTrue(self.panel.enabled)
        with self.settings(DEBUG_TOOLBAR_CONFIG=config):
            self.assertFalse(self.panel.enabled)

    def test_post(self):
        self.request = rf.post("/", data={"foo": "bar"})
        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)
        data = self.panel.get_stats()["data"]
        self.assertEqual(data["foo"], "bar")

    def test_post_json(self):
        for data, expected_stats_data in (
            ({"foo": "bar"}, {"foo": "bar"}),
            ("", {}),  # Empty JSON
            ("'", {}),  # Invalid JSON
        ):
            with self.subTest(data=data):
                self.request = rf.post(
                    "/",
                    data=data,
                    content_type="application/json",
                    CONTENT_TYPE="application/json",  # Force django test client to add the content-type even if no data
                )
                response = self.panel.process_request(self.request)
                self.panel.generate_stats(self.request, response)
                data = self.panel.get_stats()["data"]
                self.assertDictEqual(data, expected_stats_data)

    def test_urls(self):
        self.assertEqual(
            reverse("djdt:history_sidebar"),
            "/__debug__/history_sidebar/",
        )
        self.assertEqual(
            resolve("/__debug__/history_sidebar/").url_name,
            "history_sidebar",
        )
        self.assertEqual(
            reverse("djdt:history_refresh"),
            "/__debug__/history_refresh/",
        )
        self.assertEqual(
            resolve("/__debug__/history_refresh/").url_name,
            "history_refresh",
        )


@override_settings(DEBUG=True)
class HistoryViewsTestCase(IntegrationTestCase):
    PANEL_KEYS = {
        "VersionsPanel",
        "TimerPanel",
        "SettingsPanel",
        "HeadersPanel",
        "RequestPanel",
        "SQLPanel",
        "StaticFilesPanel",
        "TemplatesPanel",
        "AlertsPanel",
        "CachePanel",
        "SignalsPanel",
    }

    def test_history_panel_integration_content(self):
        """Verify the history panel's content renders properly.."""
        store = get_store()
        self.assertEqual(len(list(store.request_ids())), 0)

        data = {"foo": "bar"}
        self.client.get("/json_view/", data, content_type="application/json")

        # Check the history panel's stats to verify the toolbar rendered properly.
        request_ids = list(store.request_ids())
        self.assertEqual(len(request_ids), 1)
        toolbar = DebugToolbar.fetch(request_ids[0])
        content = toolbar.get_panel_by_id(HistoryPanel.panel_id).content
        self.assertIn("bar", content)
        self.assertIn('name="exclude_history" value="True"', content)

    def test_history_sidebar_invalid(self):
        response = self.client.get(reverse("djdt:history_sidebar"))
        self.assertEqual(response.status_code, 400)

    def test_history_headers(self):
        """Validate the headers injected from the history panel."""
        DebugToolbar.get_observe_request.cache_clear()
        response = self.client.get("/json_view/")
        request_id = list(get_store().request_ids())[0]
        self.assertEqual(response.headers["djdt-request-id"], request_id)

    def test_history_headers_unobserved(self):
        """Validate the headers aren't injected from the history panel."""
        with self.settings(
            DEBUG_TOOLBAR_CONFIG={"OBSERVE_REQUEST_CALLBACK": lambda request: False}
        ):
            DebugToolbar.get_observe_request.cache_clear()
            response = self.client.get("/json_view/")
            self.assertNotIn("djdt-request-id", response.headers)
        # Clear it again to avoid conflicting with another test
        # Specifically, DebugToolbarLiveTestCase.test_ajax_refresh
        DebugToolbar.get_observe_request.cache_clear()

    def test_history_sidebar(self):
        """Validate the history sidebar view."""
        self.client.get("/json_view/")
        request_id = list(get_store().request_ids())[0]
        data = {"request_id": request_id, "exclude_history": True}
        response = self.client.get(reverse("djdt:history_sidebar"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.json()),
            self.PANEL_KEYS,
        )

    def test_history_sidebar_includes_history(self):
        """Validate the history sidebar view."""
        self.client.get("/json_view/")
        panel_keys = copy.copy(self.PANEL_KEYS)
        panel_keys.add(HistoryPanel.panel_id)
        request_id = list(get_store().request_ids())[0]
        data = {"request_id": request_id}
        response = self.client.get(reverse("djdt:history_sidebar"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.json()),
            panel_keys,
        )

    @override_settings(
        DEBUG_TOOLBAR_CONFIG={"RENDER_PANELS": False, "RESULTS_CACHE_SIZE": 1}
    )
    def test_history_sidebar_expired_request_id(self):
        """Validate the history sidebar view."""
        self.client.get("/json_view/")
        request_id = list(get_store().request_ids())[0]
        data = {"request_id": request_id, "exclude_history": True}
        response = self.client.get(reverse("djdt:history_sidebar"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.json()),
            self.PANEL_KEYS,
        )
        # Make enough requests to unset the original
        self.client.get("/json_view/")

        # Querying old request_id should return in empty response
        data = {"request_id": request_id, "exclude_history": True}
        response = self.client.get(reverse("djdt:history_sidebar"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

        # Querying with latest request_id
        latest_request_id = list(get_store().request_ids())[0]
        data = {"request_id": latest_request_id, "exclude_history": True}
        response = self.client.get(reverse("djdt:history_sidebar"), data=data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            set(response.json()),
            self.PANEL_KEYS,
        )

    def test_history_refresh(self):
        """Verify refresh history response has request variables."""
        self.client.get("/json_view/", {"foo": "bar"}, content_type="application/json")
        self.client.get(
            "/json_view/", {"spam": "eggs"}, content_type="application/json"
        )

        response = self.client.get(
            reverse("djdt:history_refresh"), data={"request_id": "foo"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["requests"]), 2)

        request_ids = list(get_store().request_ids())
        self.assertIn(html.escape(request_ids[0]), data["requests"][0]["content"])
        self.assertIn(html.escape(request_ids[1]), data["requests"][1]["content"])

        for val in ["foo", "bar"]:
            self.assertIn(val, data["requests"][0]["content"])

        for val in ["spam", "eggs"]:
            self.assertIn(val, data["requests"][1]["content"])
