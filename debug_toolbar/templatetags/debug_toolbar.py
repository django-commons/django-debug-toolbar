from functools import cache

from django import template
from django.contrib.staticfiles import finders
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@cache
def _svg_contents(path):
    absolute = finders.find(path)
    if absolute is None:
        return ""
    with open(absolute, encoding="utf-8") as handle:
        return handle.read().strip()


@register.simple_tag
def inline_svg(path, css_class="", label=""):
    """
    Inline a static SVG file instead of linking to it, avoiding a network
    request per icon. ``label`` names the icon for assistive tech; without one
    the icon is treated as decorative.
    """
    svg = _svg_contents(path)
    if not svg.startswith("<svg "):
        return ""
    if label:
        attrs = format_html('role="img" aria-label="{}"', label)
    else:
        attrs = mark_safe('aria-hidden="true" focusable="false"')
    if css_class:
        attrs = format_html('class="{}" {}', css_class, attrs)
    return mark_safe(svg.replace("<svg ", format_html("<svg {} ", attrs), 1))
