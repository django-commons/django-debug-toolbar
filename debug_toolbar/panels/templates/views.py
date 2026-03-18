from django.core import signing
from django.http import HttpResponseBadRequest, JsonResponse
from django.template import Origin, TemplateDoesNotExist
from django.template.engine import Engine
from django.template.loader import render_to_string
from django.utils.html import format_html, mark_safe

from debug_toolbar._compat import login_not_required
from debug_toolbar.decorators import render_with_toolbar_language, require_show_toolbar


@login_not_required
@require_show_toolbar
@render_with_toolbar_language
def template_source(request):
    """
    Return the source of a template, syntax-highlighted by Pygments if
    it's available.
    """
    template_origin_name = request.GET.get("template_origin")
    if template_origin_name is None:
        return HttpResponseBadRequest('"template_origin" key is required')
    try:
        template_origin_name = signing.loads(template_origin_name)
    except Exception:
        return HttpResponseBadRequest('"template_origin" is invalid')
    template_name = request.GET.get("template", template_origin_name)

    final_loaders = []
    loaders = list(Engine.get_default().template_loaders)

    while loaders:
        loader = loaders.pop(0)

        if loader is not None:
            # Recursively unwrap loaders until we get to loaders which do not
            # themselves wrap other loaders. This adds support for
            # django.template.loaders.cached.Loader and the
            # django-template-partials loader (possibly among others)
            if hasattr(loader, "loaders"):
                loaders.extend(loader.loaders)
            else:
                final_loaders.append(loader)

    for loader in final_loaders:
        origin = Origin(template_origin_name)
        try:
            source = loader.get_contents(origin)
            break
        except TemplateDoesNotExist:
            pass
    else:
        source = f"Template Does Not Exist: {template_origin_name}"

    try:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import HtmlDjangoLexer
    except ModuleNotFoundError:
        source = format_html("<code>{}</code>", source)
    else:
        source = highlight(source, HtmlDjangoLexer(), HtmlFormatter(wrapcode=True))
        source = mark_safe(source)

    content = render_to_string(
        "debug_toolbar/panels/template_source.html",
        {"source": source, "template_name": template_name},
    )
    return JsonResponse({"content": content})
