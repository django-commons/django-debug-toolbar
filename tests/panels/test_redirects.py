import copy

from django.conf import settings
from django.http import HttpResponse
from django.test import AsyncRequestFactory

from ..base import BaseTestCase


class RedirectsPanelTestCase(BaseTestCase):
    panel_id = "RedirectsPanel"

    def test_regular_response(self):
        not_redirect = HttpResponse()
        self._get_response = lambda request: not_redirect
        response = self.panel.process_request(self.request)
        self.assertTrue(response is not_redirect)

    def test_not_a_redirect(self):
        redirect = HttpResponse(status=304)
        self._get_response = lambda request: redirect
        response = self.panel.process_request(self.request)
        self.assertTrue(response is redirect)

    def test_redirect(self):
        redirect = HttpResponse(status=302)
        redirect["Location"] = "http://somewhere/else/"
        self._get_response = lambda request: redirect
        response = self.panel.process_request(self.request)
        self.assertFalse(response is redirect)
        self.assertContains(response, "302 Found")
        self.assertContains(response, "http://somewhere/else/")

    def test_redirect_with_broken_context_processor(self):
        TEMPLATES = copy.deepcopy(settings.TEMPLATES)
        TEMPLATES[1]["OPTIONS"]["context_processors"] = [
            "tests.context_processors.broken"
        ]

        with self.settings(TEMPLATES=TEMPLATES):
            redirect = HttpResponse(status=302)
            redirect["Location"] = "http://somewhere/else/"
            self._get_response = lambda request: redirect
            response = self.panel.process_request(self.request)
            self.assertFalse(response is redirect)
            self.assertContains(response, "302 Found")
            self.assertContains(response, "http://somewhere/else/")

    def test_unknown_status_code(self):
        redirect = HttpResponse(status=369)
        redirect["Location"] = "http://somewhere/else/"
        self._get_response = lambda request: redirect
        response = self.panel.process_request(self.request)
        self.assertContains(response, "369 Unknown Status Code")

    def test_unknown_status_code_with_reason(self):
        redirect = HttpResponse(status=369, reason="Look Ma!")
        redirect["Location"] = "http://somewhere/else/"
        self._get_response = lambda request: redirect
        response = self.panel.process_request(self.request)
        self.assertContains(response, "369 Look Ma!")

    def test_insert_content(self):
        """
        Test that the panel only inserts content after generate_stats and
        not the process_request.
        """
        redirect = HttpResponse(status=304)
        self._get_response = lambda request: redirect
        response = self.panel.process_request(self.request)
        self.assertIsNotNone(response)
        response = self.panel.generate_stats(self.request, redirect)
        self.assertIsNone(response)

    async def test_async_compatibility(self):
        redirect = HttpResponse(status=302)

        async def get_response(request):
            return redirect

        await_response = await get_response(self.request)
        self._get_response = get_response

        self.request = AsyncRequestFactory().get("/")
        response = await self.panel.process_request(self.request)
        self.assertIsInstance(response, HttpResponse)
        self.assertTrue(response is await_response)

    def test_original_response_preserved(self):
        redirect = HttpResponse(status=302)
        redirect["Location"] = "http://somewhere/else/"
        self._get_response = lambda request: redirect
        response = self.panel.process_request(self.request)
        self.assertFalse(response is redirect)
        self.assertTrue(hasattr(response, "original_response"))
        self.assertTrue(response.original_response is redirect)
        self.assertIsNone(response.get("Location"))
        self.assertEqual(
            response.original_response.get("Location"), "http://somewhere/else/"
        )
