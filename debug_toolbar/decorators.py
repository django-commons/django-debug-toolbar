import functools

from asgiref.sync import iscoroutinefunction
from django.http import Http404
from django.utils.translation import get_language, override as language_override

from debug_toolbar import settings as dt_settings


def require_show_toolbar(view):
    """
    Async compatible decorator to restrict access to a view
    based on the Debug Toolbar's visibility settings.
    """
    from debug_toolbar.middleware import get_show_toolbar

    if iscoroutinefunction(view):

        @functools.wraps(view)
        async def inner(request, *args, **kwargs):
            show_toolbar = get_show_toolbar(async_mode=True)
            if not await show_toolbar(request):
                raise Http404

            return await view(request, *args, **kwargs)
    else:

        @functools.wraps(view)
        def inner(request, *args, **kwargs):
            show_toolbar = get_show_toolbar(async_mode=False)
            if not show_toolbar(request):
                raise Http404

            return view(request, *args, **kwargs)

    return inner


def render_with_toolbar_language(view):
    """Force any rendering within the view to use the toolbar's language."""

    @functools.wraps(view)
    def inner(request, *args, **kwargs):
        lang = dt_settings.get_config()["TOOLBAR_LANGUAGE"] or get_language()
        with language_override(lang):
            return view(request, *args, **kwargs)

    return inner
