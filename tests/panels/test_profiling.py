import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from django.contrib.auth.models import User
from django.core import signing
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

    def test_generate_stats_signed_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.settings(DEBUG_TOOLBAR_CONFIG={"PROFILER_PROFILE_ROOT": tmpdir}):
                response = self.panel.process_request(self.request)
                self.panel.generate_stats(self.request, response)
                path = self.panel.prof_file_path
                self.assertTrue(path)
                # Check that it's a valid signature
                filename = signing.loads(path)
                self.assertTrue(filename.endswith(".prof"))

    def test_generate_stats_no_root(self):
        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)
        # Should not have a path if root is not set
        self.assertFalse(hasattr(self.panel, "prof_file_path"))

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

    @mock.patch("cProfile.Profile.dump_stats")
    def test_generate_stats_oserror(self, mock_dump_stats):
        mock_dump_stats.side_effect = OSError
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.settings(DEBUG_TOOLBAR_CONFIG={"PROFILER_PROFILE_ROOT": tmpdir}):
                response = self.panel.process_request(self.request)
                with self.assertLogs(
                    "debug_toolbar.panels.profiling", level="ERROR"
                ) as cm:
                    self.panel.generate_stats(self.request, response)
                self.assertIn("Failed to dump profiling stats", cm.output[0])
                # Ensure prof_file_path is not set/updated if dump fails
                self.assertFalse(hasattr(self.panel, "prof_file_path"))


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


class ProfilingDownloadViewTestCase(TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.filename = "test.prof"
        self.filepath = os.path.join(self.root, self.filename)
        with open(self.filepath, "wb") as f:
            f.write(b"data")
        self.signed_path = signing.dumps(self.filename)

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_download_no_root_configured(self):
        response = self.client.get(reverse("djdt:debug_toolbar_download_prof_file"))
        self.assertEqual(response.status_code, 404)

    def test_download_valid(self):
        with override_settings(
            DEBUG_TOOLBAR_CONFIG={"PROFILER_PROFILE_ROOT": self.root}
        ):
            url = reverse("djdt:debug_toolbar_download_prof_file")
            response = self.client.get(url, {"path": self.signed_path})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(list(response.streaming_content), [b"data"])

    def test_download_invalid_signature(self):
        with override_settings(
            DEBUG_TOOLBAR_CONFIG={"PROFILER_PROFILE_ROOT": self.root}
        ):
            url = reverse("djdt:debug_toolbar_download_prof_file")
            # Tamper with the signature
            response = self.client.get(url, {"path": self.signed_path + "bad"})
            self.assertEqual(response.status_code, 404)

    def test_download_missing_file(self):
        with override_settings(
            DEBUG_TOOLBAR_CONFIG={"PROFILER_PROFILE_ROOT": self.root}
        ):
            url = reverse("djdt:debug_toolbar_download_prof_file")
            # Sign a filename that doesn't exist
            path = signing.dumps("missing.prof")
            response = self.client.get(url, {"path": path})
            self.assertEqual(response.status_code, 404)

    def test_download_path_traversal(self):
        with override_settings(
            DEBUG_TOOLBAR_CONFIG={"PROFILER_PROFILE_ROOT": self.root}
        ):
            url = reverse("djdt:debug_toolbar_download_prof_file")
            # Sign a filename that traverses safely out of the root
            path = signing.dumps("../passwd")
            response = self.client.get(url, {"path": path})
            self.assertEqual(response.status_code, 404)

    def test_download_absolute_path(self):
        with override_settings(
            DEBUG_TOOLBAR_CONFIG={"PROFILER_PROFILE_ROOT": self.root}
        ):
            url = reverse("djdt:debug_toolbar_download_prof_file")
            # Create a file outside the root and try to access it via absolute path
            with tempfile.NamedTemporaryFile() as tmp:
                path = signing.dumps(tmp.name)
                response = self.client.get(url, {"path": path})
                self.assertEqual(response.status_code, 404)

    def test_download_recursive_traversal(self):
        with override_settings(
            DEBUG_TOOLBAR_CONFIG={"PROFILER_PROFILE_ROOT": self.root}
        ):
            url = reverse("djdt:debug_toolbar_download_prof_file")
            # Try a convoluted path that resolves outside
            # e.g. root/subdir/../../outside_root
            path = signing.dumps(os.path.join("subdir", "..", "..", "passwd"))
            response = self.client.get(url, {"path": path})
            self.assertEqual(response.status_code, 404)
