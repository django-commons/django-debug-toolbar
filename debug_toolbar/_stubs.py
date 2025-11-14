from __future__ import annotations

from typing import Any, NamedTuple, Protocol

from django import template as dj_template
from django.http import HttpRequest, HttpResponse


class InspectStack(NamedTuple):
    frame: Any
    filename: str
    lineno: int
    function: str
    code_context: str
    index: int


TidyStackTrace = list[tuple[str, int, str, str, Any | None]]


class RenderContext(dj_template.context.RenderContext):
    template: dj_template.Template


class RequestContext(dj_template.RequestContext):
    template: dj_template.Template
    render_context: RenderContext


class GetResponse(Protocol):
    def __call__(self, request: HttpRequest) -> HttpResponse: ...
