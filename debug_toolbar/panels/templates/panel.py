from contextlib import contextmanager
from importlib.util import find_spec
from os.path import normpath
from pprint import pformat, saferepr

from django import http
from django.core import signing
from django.db.models.query import QuerySet, RawQuerySet
from django.template import RequestContext, Template
from django.test.signals import template_rendered
from django.test.utils import instrumented_test_render
from django.urls import path
from django.utils.translation import gettext_lazy as _

from debug_toolbar.panels import Panel
from debug_toolbar.panels.sql.tracking import SQLQueryTriggered, allow_sql
from debug_toolbar.panels.templates import views
from debug_toolbar.sanitize import force_str

if find_spec("jinja2"):
    from debug_toolbar.panels.templates.jinja2 import patch_jinja_render

    patch_jinja_render()

# Monkey-patch to enable the template_rendered signal. The receiver returns
# immediately when the panel is disabled to keep the overhead small.

# Code taken and adapted from Simon Willison and Django Snippets:
# https://www.djangosnippets.org/snippets/766/

if Template._render != instrumented_test_render:
    Template.original_render = Template._render
    Template._render = instrumented_test_render

# Monkey-patch to store items added by template context processors. The
# overhead is sufficiently small to justify enabling it unconditionally.


@contextmanager
def _request_context_bind_template(self, template):
    if self.template is not None:
        raise RuntimeError("Context is already bound to a template")

    self.template = template
    # Set context processors according to the template engine's settings.
    processors = template.engine.template_context_processors + self._processors
    self.context_processors = {}
    updates = {}
    for processor in processors:
        name = f"{processor.__module__}.{processor.__name__}"
        context = processor(self.request)
        self.context_processors[name] = context
        updates.update(context)
    self.dicts[self._processors_index] = updates

    try:
        yield
    finally:
        self.template = None
        # Unset context processors.
        self.dicts[self._processors_index] = {}


RequestContext.bind_template = _request_context_bind_template


class TemplatesPanel(Panel):
    """
    A panel that lists all templates used during processing of a response.
    """

    is_async = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.templates = []
        # An associated list of dictionaries and their prettified
        # representation.
        self.pformat_layers = []

    def _store_template_info(self, sender, **kwargs):
        template, context = kwargs["template"], kwargs["context"]

        # Skip templates that we are generating through the debug toolbar.
        is_debug_toolbar_template = isinstance(template.name, str) and (
            template.name.startswith("debug_toolbar/")
            or template.name.startswith(
                tuple(self.toolbar.config["SKIP_TEMPLATE_PREFIXES"])
            )
        )
        if is_debug_toolbar_template:
            return

        kwargs["context"] = [
            context_layer
            for context_layer in context.dicts
            if hasattr(context_layer, "items") and context_layer
        ]
        kwargs["context_processors"] = getattr(context, "context_processors", None)
        self.templates.append(kwargs)

    # Implement the Panel API

    nav_title = _("Templates")

    @property
    def title(self):
        num_templates = len(self.get_stats()["templates"])
        return _("Templates (%(num_templates)s rendered)") % {
            "num_templates": num_templates
        }

    @property
    def nav_subtitle(self):
        templates = self.get_stats()["templates"]
        if templates:
            return templates[0]["template"]["name"]
        return ""

    template = "debug_toolbar/panels/templates.html"

    @classmethod
    def get_urls(cls):
        return [path("template_source/", views.template_source, name="template_source")]

    def enable_instrumentation(self):
        template_rendered.connect(self._store_template_info)

    def disable_instrumentation(self):
        template_rendered.disconnect(self._store_template_info)

    def process_context_list(self, context_layers):
        context_list = []
        for context_layer in context_layers:
            # Check if the layer is in the cache.
            pformatted = None
            for key_values, _pformatted in self.pformat_layers:
                if key_values == context_layer:
                    pformatted = _pformatted
                    break

            if pformatted is None:
                temp_layer = {}
                for key, value in context_layer.items():
                    # Do not force evaluating LazyObject
                    if hasattr(value, "_wrapped"):
                        # SimpleLazyObject has __repr__ which includes actual value
                        # if it has been already evaluated
                        temp_layer[key] = repr(value)
                    # Replace any request elements - they have a large
                    # Unicode representation and the request data is
                    # already made available from the Request panel.
                    elif isinstance(value, http.HttpRequest):
                        temp_layer[key] = "<<request>>"
                    # Replace the debugging sql_queries element. The SQL
                    # data is already made available from the SQL panel.
                    elif key == "sql_queries" and isinstance(value, list):
                        temp_layer[key] = "<<sql_queries>>"
                    # Replace LANGUAGES, which is available in i18n context
                    # processor
                    elif key == "LANGUAGES" and isinstance(value, tuple):
                        temp_layer[key] = "<<languages>>"
                    # QuerySet would trigger the database: user can run the
                    # query from SQL Panel
                    elif isinstance(value, (QuerySet, RawQuerySet)):
                        temp_layer[key] = (
                            f"<<{value.__class__.__name__.lower()} of {value.model._meta.label}>>"
                        )
                    else:
                        token = allow_sql.set(False)
                        try:
                            saferepr(value)  # this MAY trigger a db query
                        except SQLQueryTriggered:
                            temp_layer[key] = "<<triggers database query>>"
                        except UnicodeEncodeError:
                            temp_layer[key] = "<<Unicode encode error>>"
                        except Exception:
                            temp_layer[key] = "<<unhandled exception>>"
                        else:
                            temp_layer[key] = value
                        finally:
                            allow_sql.reset(token)
                pformatted = pformat(temp_layer)
                self.pformat_layers.append((context_layer, pformatted))
            context_list.append(pformatted)

        return context_list

    def generate_stats(self, request, response):
        template_context = []
        for template_data in self.templates:
            info = {}
            # Clean up some info about templates
            template = template_data["template"]
            if hasattr(template, "origin") and template.origin and template.origin.name:
                template.origin_name = template.origin.name
                template.origin_hash = signing.dumps(template.origin.name)
            else:
                template.origin_name = _("No origin")
                template.origin_hash = ""
            info["template"] = {
                "name": template.name,
                "origin_name": template.origin_name,
                "origin_hash": template.origin_hash,
            }
            # Clean up context for better readability
            if self.toolbar.config["SHOW_TEMPLATE_CONTEXT"]:
                if "context_list" not in template_data:
                    template_data["context_list"] = self.process_context_list(
                        template_data.get("context", [])
                    )
                info["context"] = "\n".join(template_data["context_list"])
            template_context.append(info)

        # Fetch context_processors/template_dirs from any template
        if self.templates:
            context_processors = (
                {
                    key: force_str(value)
                    for key, value in self.templates[0]["context_processors"].items()
                }
                if self.templates[0]["context_processors"]
                else None
            )
            template = self.templates[0]["template"]
            # django templates have the 'engine' attribute, while jinja
            # templates use 'backend'
            engine_backend = getattr(template, "engine", None) or template.backend
            template_dirs = engine_backend.dirs
        else:
            context_processors = None
            template_dirs = []

        self.record_stats(
            {
                "templates": template_context,
                "template_dirs": [normpath(x) for x in template_dirs],
                "context_processors": context_processors,
            }
        )
