"""
Test for the DatabaseStore panel loading fix
"""

from django.test import TestCase, override_settings
from django.test.signals import setting_changed

from debug_toolbar.settings import get_panels
from debug_toolbar.store import get_store
from debug_toolbar.toolbar import DebugToolbar, StoredDebugToolbar


class DatabaseStorePanelLoadingTestCase(TestCase):
    """
    Test that StoredDebugToolbar.from_store loads all configured panels,
    even those that don't have stored data.

    This fixes the KeyError issue when users dynamically add panels
    to DEBUG_TOOLBAR_PANELS after requests have been made.
    """

    def setUp(self):
        """Clear any cached data"""
        get_store().clear()
        # Clear panel classes cache
        DebugToolbar._panel_classes = None
        get_panels.cache_clear()

    def test_stored_toolbar_loads_all_configured_panels(self):
        """
        Test that StoredDebugToolbar.from_store loads all panels from
        current configuration, not just those with stored data.
        """
        from django.conf import settings

        # Save the original panels setting
        original_panels = getattr(settings, "DEBUG_TOOLBAR_PANELS", None)

        # Step 1: Start with minimal panels
        minimal_panels = [
            "debug_toolbar.panels.history.HistoryPanel",
            "debug_toolbar.panels.versions.VersionsPanel",
            "debug_toolbar.panels.timer.TimerPanel",
        ]

        full_panels = [
            "debug_toolbar.panels.history.HistoryPanel",
            "debug_toolbar.panels.versions.VersionsPanel",
            "debug_toolbar.panels.timer.TimerPanel",
            "debug_toolbar.panels.settings.SettingsPanel",
            "debug_toolbar.panels.headers.HeadersPanel",
            "debug_toolbar.panels.request.RequestPanel",
            "debug_toolbar.panels.sql.SQLPanel",
            "debug_toolbar.panels.staticfiles.StaticFilesPanel",
            "debug_toolbar.panels.templates.TemplatesPanel",
            "debug_toolbar.panels.alerts.AlertsPanel",
            "debug_toolbar.panels.cache.CachePanel",
            "debug_toolbar.panels.signals.SignalsPanel",
            "debug_toolbar.panels.redirects.RedirectsPanel",
            "debug_toolbar.panels.profiling.ProfilingPanel",
        ]

        try:
            # Step 1: Set minimal panels
            settings.DEBUG_TOOLBAR_PANELS = minimal_panels
            DebugToolbar._panel_classes = None
            get_panels.cache_clear()
            setting_changed.send(
                sender=self.__class__,
                setting="DEBUG_TOOLBAR_PANELS",
                value=minimal_panels,
                enter=True,
            )

            # Step 2: Create a toolbar and save data for minimal panels
            from django.test import RequestFactory

            factory = RequestFactory()
            request = factory.get("/")
            request.META["REMOTE_ADDR"] = "127.0.0.1"

            def dummy_response(req):
                from django.http import HttpResponse

                return HttpResponse("OK")

            toolbar = DebugToolbar(request, dummy_response)
            request_id = toolbar.request_id

            # Verify we have minimal panels
            self.assertEqual(len(toolbar._panels), 3)
            self.assertIn("HistoryPanel", toolbar._panels)
            self.assertNotIn("RequestPanel", toolbar._panels)

            # Save data for the minimal panels (simulating request processing)
            store = get_store()
            for panel_id, _panel in toolbar._panels.items():
                dummy_data = {"test": "data", "panel": panel_id}
                store.save_panel(request_id, panel_id, dummy_data)

            # Step 3: Change to full panel configuration
            settings.DEBUG_TOOLBAR_PANELS = full_panels
            DebugToolbar._panel_classes = None
            get_panels.cache_clear()
            setting_changed.send(
                sender=self.__class__,
                setting="DEBUG_TOOLBAR_PANELS",
                value=full_panels,
                enter=True,
            )

            # Verify we now have full panels configured
            self.assertEqual(len(get_panels()), 14)
            self.assertEqual(len(DebugToolbar.get_panel_classes()), 14)

            # Step 4: Load toolbar from store
            stored_toolbar = StoredDebugToolbar.from_store(request_id)

            # Step 5: Verify ALL configured panels are loaded, not just those with data
            self.assertEqual(
                len(stored_toolbar._panels),
                14,
                f"Expected 14 panels, got {len(stored_toolbar._panels)}: {list(stored_toolbar._panels.keys())}",
            )

            # Panels with stored data should be enabled
            self.assertIn("HistoryPanel", stored_toolbar._panels)
            history_panel = stored_toolbar._panels["HistoryPanel"]
            self.assertTrue(history_panel.enabled)
            self.assertTrue(bool(history_panel.get_stats()))

            # Panels without stored data should be disabled but accessible
            self.assertIn("RequestPanel", stored_toolbar._panels)
            request_panel = stored_toolbar._panels["RequestPanel"]
            self.assertFalse(request_panel.enabled)
            self.assertFalse(bool(request_panel.get_stats()))

            self.assertIn("SQLPanel", stored_toolbar._panels)
            sql_panel = stored_toolbar._panels["SQLPanel"]
            self.assertFalse(sql_panel.enabled)
            self.assertFalse(bool(sql_panel.get_stats()))

            # Step 6: Verify get_panel_by_id works for all panels (this was the original bug)
            # This should not raise KeyError
            panel = stored_toolbar.get_panel_by_id("RequestPanel")
            self.assertIsNotNone(panel)
            self.assertEqual(panel.panel_id, "RequestPanel")

            panel = stored_toolbar.get_panel_by_id("SQLPanel")
            self.assertIsNotNone(panel)
            self.assertEqual(panel.panel_id, "SQLPanel")

            panel = stored_toolbar.get_panel_by_id("HistoryPanel")
            self.assertIsNotNone(panel)
            self.assertEqual(panel.panel_id, "HistoryPanel")

        finally:
            # Restore original setting
            if original_panels is not None:
                settings.DEBUG_TOOLBAR_PANELS = original_panels
            else:
                delattr(settings, "DEBUG_TOOLBAR_PANELS")
            DebugToolbar._panel_classes = None
            get_panels.cache_clear()

    def test_stored_toolbar_from_store_preserves_from_store_flag(self):
        """
        Test that panels loaded from store have from_store=True even without data.
        This prevents the enabled property from trying to access request.COOKIES.
        """
        # Use minimal panels first, then expand
        minimal_panels = ["debug_toolbar.panels.history.HistoryPanel"]
        full_panels = [
            "debug_toolbar.panels.history.HistoryPanel",
            "debug_toolbar.panels.request.RequestPanel",
        ]

        with override_settings(DEBUG_TOOLBAR_PANELS=minimal_panels):
            DebugToolbar._panel_classes = None
            get_panels.cache_clear()
            setting_changed.send(
                sender=self.__class__,
                setting="DEBUG_TOOLBAR_PANELS",
                value=minimal_panels,
                enter=True,
            )

            from django.test import RequestFactory

            factory = RequestFactory()
            request = factory.get("/")
            request.META["REMOTE_ADDR"] = "127.0.0.1"

            def dummy_response(req):
                from django.http import HttpResponse

                return HttpResponse("OK")

            toolbar = DebugToolbar(request, dummy_response)
            request_id = toolbar.request_id

            # Save data only for HistoryPanel
            store = get_store()
            store.save_panel(request_id, "HistoryPanel", {"test": "data"})

        with override_settings(DEBUG_TOOLBAR_PANELS=full_panels):
            DebugToolbar._panel_classes = None
            get_panels.cache_clear()
            setting_changed.send(
                sender=self.__class__,
                setting="DEBUG_TOOLBAR_PANELS",
                value=full_panels,
                enter=True,
            )

            stored_toolbar = StoredDebugToolbar.from_store(request_id)

            # Both panels should have from_store=True
            history_panel = stored_toolbar._panels["HistoryPanel"]
            self.assertTrue(history_panel.from_store)

            request_panel = stored_toolbar._panels["RequestPanel"]
            self.assertTrue(request_panel.from_store)

            # This should not raise AttributeError about request.COOKIES being None
            # because from_store=True causes enabled to return bool(get_stats())
            self.assertTrue(history_panel.enabled)  # Has stats
            self.assertFalse(request_panel.enabled)  # No stats
