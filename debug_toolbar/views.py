import os

from django.http import FileResponse, Http404, JsonResponse
from django.utils.html import escape
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET

from debug_toolbar._compat import login_not_required
from debug_toolbar.decorators import render_with_toolbar_language, require_show_toolbar
from debug_toolbar.toolbar import DebugToolbar


@login_not_required
@require_show_toolbar
@render_with_toolbar_language
def render_panel(request):
    """Render the contents of a panel"""
    toolbar = DebugToolbar.fetch(request.GET["request_id"], request.GET["panel_id"])
    if toolbar is None:
        content = _(
            "Data for this panel isn't available anymore. "
            "Please reload the page and retry."
        )
        content = f"<p>{escape(content)}</p>"
        scripts = []
    else:
        panel = toolbar.get_panel_by_id(request.GET["panel_id"])
        content = panel.content
        scripts = panel.scripts
    return JsonResponse({"content": content, "scripts": scripts})


@require_GET
def download_prof_file(request):
    file_path = request.GET.get("path")
    print("Serving .prof file:", file_path)
    if not file_path or not os.path.exists(file_path):
        print("File does not exist:", file_path)
        raise Http404("File not found.")

    response = FileResponse(
        open(file_path, "rb"), content_type="application/octet-stream"
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{os.path.basename(file_path)}"'
    )
    return response
