from django.http import HttpRequest, JsonResponse
from django.utils.html import escape
from django.utils.translation import gettext as _

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
