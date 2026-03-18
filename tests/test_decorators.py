from unittest.mock import patch

from django.http import Http404, HttpResponse
from django.test import AsyncRequestFactory, RequestFactory, TestCase
from django.test.utils import override_settings

from debug_toolbar.decorators import render_with_toolbar_language, require_show_toolbar


@render_with_toolbar_language
def stub_view(request):
    return HttpResponse(200)


@require_show_toolbar
def stub_require_toolbar_view(request):
    return HttpResponse(200)


@require_show_toolbar
async def stub_require_toolbar_async_view(request):
    return HttpResponse(200)


class TestRequireToolbar(TestCase):
    """
    Tests require_toolbar functionality and async compatibility.
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.async_factory = AsyncRequestFactory()

    @override_settings(DEBUG=True)
    def test_require_toolbar_debug_true(self):
        response = stub_require_toolbar_view(self.factory.get("/"))
        self.assertEqual(response.status_code, 200)

    def test_require_toolbar_debug_false(self):
        with self.assertRaises(Http404):
            stub_require_toolbar_view(self.factory.get("/"))

    # Following tests additionally tests async compatibility
    # of require_toolbar decorator
    @override_settings(DEBUG=True)
    async def test_require_toolbar_async_debug_true(self):
        response = await stub_require_toolbar_async_view(self.async_factory.get("/"))
        self.assertEqual(response.status_code, 200)

    async def test_require_toolbar_async_debug_false(self):
        with self.assertRaises(Http404):
            await stub_require_toolbar_async_view(self.async_factory.get("/"))


@override_settings(DEBUG=True, LANGUAGE_CODE="fr")
class RenderWithToolbarLanguageTestCase(TestCase):
    @override_settings(DEBUG_TOOLBAR_CONFIG={"TOOLBAR_LANGUAGE": "de"})
    @patch("debug_toolbar.decorators.language_override")
    def test_uses_toolbar_language(self, mock_language_override):
        stub_view(RequestFactory().get("/"))
        mock_language_override.assert_called_once_with("de")

    @patch("debug_toolbar.decorators.language_override")
    def test_defaults_to_django_language_code(self, mock_language_override):
        stub_view(RequestFactory().get("/"))
        mock_language_override.assert_called_once_with("fr")
