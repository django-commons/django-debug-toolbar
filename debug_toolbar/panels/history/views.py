from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from django.template.loader import render_to_string

from debug_toolbar._compat import login_not_required
from debug_toolbar.decorators import render_with_toolbar_language, require_show_toolbar
from debug_toolbar.panels.history.forms import HistoryStoreForm
from debug_toolbar.store import get_store
from debug_toolbar.toolbar import DebugToolbar


@login_not_required
@require_show_toolbar
@render_with_toolbar_language
def history_sidebar(
    request: HttpRequest,
) -> HttpResponseBadRequest | JsonResponse:
    """Returns the selected debug toolbar history snapshot."""
    form = HistoryStoreForm(request.GET)

    if form.is_valid():
        request_id: str = form.cleaned_data["request_id"]
        toolbar: DebugToolbar | None = DebugToolbar.fetch(request_id)
        exclude_history = form.cleaned_data["exclude_history"]
        context: dict[str, dict[str, str]] = {}
        if toolbar is None:
            # When the request_id has been popped already due to
            # RESULTS_CACHE_SIZE
            return JsonResponse(context)
        for panel in toolbar.panels:
            if exclude_history and not panel.is_historical:
                continue
            panel_context = {"panel": panel}
            context[panel.panel_id] = {
                "button": render_to_string(
                    "debug_toolbar/includes/panel_button.html", panel_context
                ),
                "content": render_to_string(
                    "debug_toolbar/includes/panel_content.html", panel_context
                ),
            }
        return JsonResponse(context)
    return HttpResponseBadRequest(f"Form errors: {form.errors}")


@login_not_required
@require_show_toolbar
@render_with_toolbar_language
def history_refresh(
    request: HttpRequest,
) -> HttpResponseBadRequest | JsonResponse:
    """Returns the refreshed list of table rows for the History Panel."""
    form = HistoryStoreForm(request.GET)

    if form.is_valid():
        requests: list[dict[str, str]] = []
        # Convert to list to handle mutations happening in parallel
        for request_id in get_store().request_ids():
            toolbar = DebugToolbar.fetch(request_id)
            requests.append(
                {
                    "id": request_id,
                    "content": render_to_string(
                        "debug_toolbar/panels/history_tr.html",
                        {
                            "request_id": request_id,
                            "history_context": {
                                "history_stats": toolbar.store.panel(
                                    request_id, "HistoryPanel"
                                ),
                                "form": HistoryStoreForm(
                                    initial={
                                        "request_id": request_id,
                                        "exclude_history": True,
                                    }
                                ),
                            },
                        },
                    ),
                }
            )

        return JsonResponse({"requests": requests})
    return HttpResponseBadRequest("Form errors")
