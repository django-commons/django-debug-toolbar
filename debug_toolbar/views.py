from django.http import JsonResponse
from django.utils.html import escape
from django.utils.translation import gettext as _

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
