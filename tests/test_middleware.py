import sys
from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import AsyncRequestFactory, RequestFactory, TestCase, override_settings

from debug_toolbar.middleware import DebugToolbarMiddleware

if sys.version_info >= (3, 12):
    from inspect import iscoroutinefunction
else:
    from asyncio import iscoroutinefunction


def show_toolbar_if_staff(request):
    # Hit the database, but always return True
    return User.objects.exists() or True


async def ashow_toolbar_if_staff(request):
    # Hit the database, but always return True
    has_users = await User.objects.afirst()
    return has_users or True


class MiddlewareSyncAsyncCompatibilityTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.async_factory = AsyncRequestFactory()

    @override_settings(DEBUG=True)
    def test_sync_mode(self):
        """
        test middleware switches to sync (__call__) based on get_response type
        """

        request = self.factory.get("/")
        middleware = DebugToolbarMiddleware(
            lambda x: HttpResponse("<html><body>Test app</body></html>")
        )

        self.assertFalse(iscoroutinefunction(middleware))

        response = middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"djdt", response.content)

    @override_settings(DEBUG=True)
    async def test_async_mode(self):
        """
        test middleware switches to async (__acall__) based on get_response type
        and returns a coroutine
        """

        async def get_response(request):
            return HttpResponse("<html><body>Test app</body></html>")

        middleware = DebugToolbarMiddleware(get_response)
        request = self.async_factory.get("/")

        self.assertTrue(iscoroutinefunction(middleware))

        response = await middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"djdt", response.content)

    @override_settings(DEBUG=True)
    @patch(
        "debug_toolbar.middleware.show_toolbar_func_or_path",
        return_value=ashow_toolbar_if_staff,
    )
    def test_async_show_toolbar_callback_sync_middleware(self, mocked_show):
        def get_response(request):
            return HttpResponse("<html><body>Hello world</body></html>")

        middleware = DebugToolbarMiddleware(get_response)

        request = self.factory.get("/")
        response = middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"djdt", response.content)

    @override_settings(DEBUG=True)
    @patch(
        "debug_toolbar.middleware.show_toolbar_func_or_path",
        return_value=show_toolbar_if_staff,
    )
    async def test_sync_show_toolbar_callback_async_middleware(self, mocked_show):
        async def get_response(request):
            return HttpResponse("<html><body>Hello world</body></html>")

        middleware = DebugToolbarMiddleware(get_response)

        request = self.async_factory.get("/")
        response = await middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"djdt", response.content)
