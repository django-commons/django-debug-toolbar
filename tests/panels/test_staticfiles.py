from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders, storage
from django.shortcuts import render
from django.test import AsyncRequestFactory, RequestFactory

from debug_toolbar.panels.staticfiles import StaticFilesPanel, URLMixin

from ..base import BaseTestCase


class StaticFilesPanelTestCase(BaseTestCase):
    panel_id = StaticFilesPanel.panel_id

    def test_default_case(self):
        response = self.panel.process_request(self.request)
        self.panel.generate_stats(self.request, response)
        content = self.panel.content
        self.assertIn(
            "django.contrib.staticfiles.finders.AppDirectoriesFinder", content
        )
        self.assertIn(
            "django.contrib.staticfiles.finders.FileSystemFinder (2 files)", content
        )
        self.assertEqual(self.panel.get_stats()["num_used"], 0)
        self.assertNotEqual(self.panel.num_found, 0)
        expected_apps = ["django.contrib.admin", "debug_toolbar"]
        if settings.USE_GIS:
            expected_apps = ["django.contrib.gis"] + expected_apps
        self.assertEqual(self.panel.get_staticfiles_apps(), expected_apps)
        self.assertEqual(
            self.panel.get_staticfiles_dirs(), finders.FileSystemFinder().locations
        )

    async def test_store_staticfiles_with_async_context(self):
        async def get_response(request):
            # template contains one static file
            return render(request, "staticfiles/async_static.html")

        self._get_response = get_response
        async_request = AsyncRequestFactory().get("/")
        response = await self.panel.process_request(async_request)
        self.panel.generate_stats(self.request, response)
        self.assertEqual(self.panel.get_stats()["num_used"], 1)

    def test_insert_content(self):
        """
        Test that the panel only inserts content after generate_stats and
        not the process_request.
        """
        response = self.panel.process_request(self.request)
        # ensure the panel does not have content yet.
        self.assertNotIn(
            "django.contrib.staticfiles.finders.AppDirectoriesFinder",
            self.panel.content,
        )
        self.panel.generate_stats(self.request, response)
        # ensure the panel renders correctly.
        content = self.panel.content
        self.assertIn(
            "django.contrib.staticfiles.finders.AppDirectoriesFinder", content
        )
        self.assertValidHTML(content)

    def test_path(self):
        def get_response(request):
            return render(
                request,
                "staticfiles/path.html",
                {
                    "paths": [
                        Path("additional_static/base.css"),
                        "additional_static/base.css",
                        "additional_static/base2.css",
                    ]
                },
            )

        self._get_response = get_response
        request = RequestFactory().get("/")
        response = self.panel.process_request(request)
        self.panel.generate_stats(self.request, response)
        self.assertEqual(self.panel.get_stats()["num_used"], 2)
        self.assertIn(
            'href="/static/additional_static/base.css"', self.panel.content, 1
        )
        self.assertIn(
            'href="/static/additional_static/base2.css"', self.panel.content, 1
        )

    def test_storage_state_preservation(self):
        """Ensure the URLMixin doesn't affect storage state"""
        original_storage = storage.staticfiles_storage
        original_attrs = dict(original_storage.__dict__)

        # Trigger mixin injection
        self.panel.ready()

        # Verify all original attributes are preserved
        self.assertEqual(original_attrs, dict(original_storage.__dict__))

    def test_context_variable_lifecycle(self):
        """Test the request_id context variable lifecycle"""
        from debug_toolbar.panels.staticfiles import request_id_context_var

        # Should not raise when context not set
        url = storage.staticfiles_storage.url("test.css")
        self.assertTrue(url.startswith("/static/"))

        # Should track when context is set
        token = request_id_context_var.set("test-request-id")
        try:
            url = storage.staticfiles_storage.url("test.css")
            self.assertTrue(url.startswith("/static/"))
            # Verify file was tracked
            self.assertIn("test.css", [f[0] for f in self.panel.used_paths])
        finally:
            request_id_context_var.reset(token)

    def test_multiple_initialization(self):
        """Ensure multiple panel initializations don't stack URLMixin"""
        storage_class = storage.staticfiles_storage.__class__

        # Initialize panel multiple times
        for _ in range(3):
            self.panel.ready()

        # Verify URLMixin appears exactly once in bases
        mixin_count = sum(1 for base in storage_class.__bases__ if base == URLMixin)
        self.assertEqual(mixin_count, 1)
