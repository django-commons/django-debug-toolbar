import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from debug_toolbar.panels.profiling import ProfilingPanel

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


@override_settings(DEBUG=True)
class ProfilingDownloadViewTestCase(TestCase):
    def test_missing_request_id(self):
        url = reverse("djdt:profiling_download")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_toolbar_not_found(self):
        url = reverse("djdt:profiling_download")
        response = self.client.get(url, {"request_id": "nonexistent-id"})
        self.assertEqual(response.status_code, 400)

    @mock.patch("debug_toolbar.panels.profiling.DebugToolbar.fetch")
    def test_valid_download(self, mock_fetch):
        mock_panel = mock.MagicMock()
        mock_panel.get_stats.return_value = {
            "func_list": [
                {
                    "count": 1,
                    "primitive_count": 1,
                    "tottime": 0.001,
                    "tottime_per_call": 0.001,
                    "cumtime": 0.005,
                    "cumtime_per_call": 0.005,
                    "func_key": "/path/to/file.py:42(view)",
                },
                {
                    "count": 5,
                    "primitive_count": 3,
                    "tottime": 0.002,
                    "tottime_per_call": 0.0004,
                    "cumtime": 0.003,
                    "cumtime_per_call": 0.001,
                    "func_key": "/path/to/other.py:10(helper)",
                },
            ]
        }
        mock_toolbar = mock.MagicMock()
        mock_toolbar.get_panel_by_id.return_value = mock_panel
        mock_fetch.return_value = mock_toolbar

        url = reverse("djdt:profiling_download")
        response = self.client.get(url, {"request_id": "test-id"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertIn(
            'attachment; filename="request-test-id.prof"',
            response["Content-Disposition"],
        )
        content = response.content.decode()
        self.assertIn(
            "   ncalls  tottime  percall  cumtime  percall filename:lineno(function)",
            content,
        )
        self.assertIn("/path/to/file.py:42(view)", content)
        self.assertIn("5/3", content)

    @mock.patch("debug_toolbar.panels.profiling.DebugToolbar.fetch")
    def test_empty_func_list(self, mock_fetch):
        mock_panel = mock.MagicMock()
        mock_panel.get_stats.return_value = {}
        mock_toolbar = mock.MagicMock()
        mock_toolbar.get_panel_by_id.return_value = mock_panel
        mock_fetch.return_value = mock_toolbar

        url = reverse("djdt:profiling_download")
        response = self.client.get(url, {"request_id": "test-id"})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn(
            "   ncalls  tottime  percall  cumtime  percall filename:lineno(function)",
            content,
        )
