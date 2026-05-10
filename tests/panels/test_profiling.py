import sys
import unittest

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.test.utils import override_settings

from debug_toolbar.panels.profiling import ProfilingPanel
from debug_toolbar.store import get_store

from ..base import BaseTestCase, IntegrationTestCase
from ..views import listcomp_view, regular_view


@override_settings(
    DEBUG_TOOLBAR_PANELS=["debug_toolbar.panels.profiling.ProfilingPanel"]
)
class ProfilingPanelTestCase(BaseTestCase):
    panel_id = ProfilingPanel.panel_id

    def test_regular_view(self):
        self._get_response = lambda request: regular_view(request, "profiling")
        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)
        self.assertIn("func_list", self.panel.get_stats())
        self.assertIn("regular_view", self.panel.content)

    def test_insert_content(self):
        """
        Test that the panel only inserts content after generate_stats and
        not the process_request.
        """
        self._get_response = lambda request: regular_view(request, "profiling")
        response = self.panel.process_request(self.request)
        # ensure the panel does not have content yet.
        self.assertNotIn("regular_view", self.panel.content)
        self.panel.generate_stats(self.request, response)
        self.reload_stats()
        # ensure the panel renders correctly.
        content = self.panel.content
        self.assertIn("regular_view", content)
        self.assertIn("render", content)
        self.assertValidHTML(content)
        # ensure traces aren't escaped
        self.assertIn('<span class="djdt-path">', content)

    @override_settings(DEBUG_TOOLBAR_CONFIG={"PROFILER_THRESHOLD_RATIO": 1})
    def test_cum_time_threshold(self):
        """
        Test that cumulative time threshold excludes calls
        """
        self._get_response = lambda request: regular_view(request, "profiling")
        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)
        # ensure the panel renders but doesn't include our function.
        content = self.panel.content
        self.assertIn("regular_view", content)
        self.assertNotIn("render", content)
        self.assertValidHTML(content)

    @unittest.skipUnless(
        sys.version_info < (3, 12, 0),
        "Python 3.12 no longer contains a frame for list comprehensions.",
    )
    def test_listcomp_escaped(self):
        self._get_response = lambda request: listcomp_view(request)
        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)
        content = self.panel.content
        self.assertNotIn('<span class="djdt-func"><listcomp></span>', content)
        self.assertIn('<span class="djdt-func">&lt;listcomp&gt;</span>', content)

    def test_generate_stats_no_profiler(self):
        """
        Test generating stats with no profiler.
        """
        response = HttpResponse()
        self.assertIsNone(self.panel.generate_stats(self.request, response))

    def test_generate_stats_no_root_func(self):
        """
        Test generating stats using profiler without root function.
        """
        response = self.panel.process_request(self.request)
        self.panel.profiler.clear()
        self.panel.profiler.enable()
        self.panel.profiler.disable()
        self.panel.generate_stats(self.request, response)
        self.assertNotIn("func_list", self.panel.get_stats())

    def test_content_includes_download_form(self):
        content = self.panel.content
        self.assertIn('name="request_id"', content)
        self.assertIn(self.toolbar.request_id, content)


@override_settings(
    DEBUG=True, DEBUG_TOOLBAR_PANELS=["debug_toolbar.panels.profiling.ProfilingPanel"]
)
class ProfilingPanelIntegrationTestCase(IntegrationTestCase):
    def test_view_executed_once(self):
        self.assertEqual(User.objects.count(), 0)

        response = self.client.get("/new_user/")
        self.assertContains(response, "Profiling")
        self.assertEqual(User.objects.count(), 1)

        with self.assertRaises(IntegrityError), transaction.atomic():
            response = self.client.get("/new_user/")
        self.assertEqual(User.objects.count(), 1)

    def test_profiling_download_missing_request_id(self):
        response = self.client.get("/__debug__/profiling_download/")
        self.assertEqual(response.status_code, 400)

    def test_profiling_download_toolbar_not_found(self):
        response = self.client.get(
            "/__debug__/profiling_download/", {"request_id": "nonexistent-id"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"Request is no longer available.")

    def test_profiling_download(self):
        # The profiling panel needs to be actively enabled.
        self.client.cookies["djdtProfilingPanel"] = "on"
        self.client.get("/regular/basic/")
        request_ids = list(get_store().request_ids())
        request_id = request_ids[-1]
        response = self.client.get(
            "/__debug__/profiling_download/", {"request_id": request_id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertRegex(
            response.filename,
            r"<unavailable>-.*\.prof",
        )
        content = b"".join(response.streaming_content)
        self.assertIn(
            b"   ncalls  tottime  percall  cumtime  percall filename:lineno(function)",
            content,
        )

    def test_profiling_download_lacks_data(self):
        # The profiling panel needs to be actively enabled.
        self.client.cookies["djdtProfilingPanel"] = "on"
        self.client.get("/regular/basic/")
        store = get_store()
        request_ids = list(store.request_ids())
        request_id = request_ids[-1]
        # Clear the Profiling panel's data to treat it as if the profiling
        # didn't get generated as expected.
        store.save_panel(request_id, ProfilingPanel.panel_id, {})
        response = self.client.get(
            "/__debug__/profiling_download/", {"request_id": request_id}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.content, b"No profiling data exists for this request."
        )
