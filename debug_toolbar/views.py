from django.core.files.storage import FileSystemStorage
from django.http import FileResponse, Http404, HttpRequest, JsonResponse
from django.utils.html import escape
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET

from debug_toolbar import settings as dt_settings
from debug_toolbar._compat import login_not_required
from debug_toolbar.decorators import render_with_toolbar_language, require_show_toolbar
from debug_toolbar.panels import Panel
from debug_toolbar.toolbar import DebugToolbar, StoredDebugToolbar


@login_not_required
@require_show_toolbar
@render_with_toolbar_language
def render_panel(request: HttpRequest) -> JsonResponse:
    """Render the contents of a panel"""
    toolbar: StoredDebugToolbar | None = DebugToolbar.fetch(
        request.GET["request_id"], request.GET["panel_id"]
    )
    if toolbar is None:
        content = _(
            "Data for this panel isn't available anymore. "
            "Please reload the page and retry."
        )
        content = f"<p>{escape(content)}</p>"
        scripts = []
    else:
        panel: Panel = toolbar.get_panel_by_id(request.GET["panel_id"])
        content = panel.content
        scripts = panel.scripts
    return JsonResponse({"content": content, "scripts": scripts})


@require_GET
@login_not_required
def download_prof_file(request):
    root = dt_settings.get_config()["PROFILER_PROFILE_ROOT"]
    # If root is None, FileSystemStorage defaults to MEDIA_ROOT
    storage = FileSystemStorage(location=root)

    if not (filename := request.GET.get("path")):
        raise Http404()

    try:
        return FileResponse(
            storage.open(filename),
            as_attachment=True,
            filename=filename,
            content_type="application/octet-stream",
        )
    except FileNotFoundError:
        raise Http404() from None
