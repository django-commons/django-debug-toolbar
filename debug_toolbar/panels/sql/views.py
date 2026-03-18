from django.http import HttpResponseBadRequest, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from debug_toolbar._compat import login_not_required
from debug_toolbar.decorators import render_with_toolbar_language, require_show_toolbar
from debug_toolbar.forms import SignedDataForm
from debug_toolbar.panels.sql.forms import SQLSelectForm
from debug_toolbar.panels.sql.utils import reformat_sql


def get_signed_data(request):
    """Unpack a signed data form, if invalid returns None"""
    data = request.GET if request.method == "GET" else request.POST
    signed_form = SignedDataForm(data)
    if signed_form.is_valid():
        return signed_form.verified_data()
    return None


@csrf_exempt
@login_not_required
@require_show_toolbar
@render_with_toolbar_language
def sql_select(request):
    """Returns the output of the SQL SELECT statement"""
    verified_data = get_signed_data(request)
    if not verified_data:
        return HttpResponseBadRequest("Invalid signature")
    form = SQLSelectForm(verified_data)

    if form.is_valid():
        query = form.cleaned_data["query"]
        result, headers = form.select()
        context = {
            "result": result,
            "sql": reformat_sql(query["sql"], with_toggle=False),
            "duration": query["duration"],
            "headers": headers,
            "alias": query["alias"],
        }
        content = render_to_string("debug_toolbar/panels/sql_select.html", context)
        return JsonResponse({"content": content})
    return HttpResponseBadRequest("Form errors")


@csrf_exempt
@login_not_required
@require_show_toolbar
@render_with_toolbar_language
def sql_explain(request):
    """Returns the output of the SQL EXPLAIN on the given query"""
    verified_data = get_signed_data(request)
    if not verified_data:
        return HttpResponseBadRequest("Invalid signature")
    form = SQLSelectForm(verified_data)

    if form.is_valid():
        query = form.cleaned_data["query"]
        result, headers = form.explain()
        context = {
            "result": result,
            "sql": reformat_sql(query["sql"], with_toggle=False),
            "duration": query["duration"],
            "headers": headers,
            "alias": query["alias"],
        }
        content = render_to_string("debug_toolbar/panels/sql_explain.html", context)
        return JsonResponse({"content": content})
    return HttpResponseBadRequest("Form errors")


@csrf_exempt
@login_not_required
@require_show_toolbar
@render_with_toolbar_language
def sql_profile(request):
    """Returns the output of running the SQL and getting the profiling statistics"""
    verified_data = get_signed_data(request)
    if not verified_data:
        return HttpResponseBadRequest("Invalid signature")
    form = SQLSelectForm(verified_data)

    if form.is_valid():
        query = form.cleaned_data["query"]
        result = None
        headers = None
        result_error = None
        try:
            result, headers = form.profile()
        except Exception:
            result_error = (
                "Profiling is either not available or not supported by your database."
            )

        context = {
            "result": result,
            "result_error": result_error,
            "sql": form.reformat_sql(),
            "duration": query["duration"],
            "headers": headers,
            "alias": query["alias"],
        }
        content = render_to_string("debug_toolbar/panels/sql_profile.html", context)
        return JsonResponse({"content": content})
    return HttpResponseBadRequest("Form errors")
