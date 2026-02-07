import pathlib

from django.core import signing
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
    if not (root := dt_settings.get_config()["PROFILER_PROFILE_ROOT"]):
        raise Http404()

    if not (file_path := request.GET.get("path")):
        raise Http404()

    try:
        filename = signing.loads(file_path)
    except signing.BadSignature:
        raise Http404() from None

    root_path = pathlib.Path(root).resolve()
    resolved_path = (root_path / filename).resolve()
    if not resolved_path.is_relative_to(root_path) or not resolved_path.exists():
        raise Http404()

    return FileResponse(
        open(resolved_path, "rb"),
        as_attachment=True,
        filename=resolved_path.name,
        content_type="application/octet-stream",
    )
