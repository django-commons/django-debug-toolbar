from unittest import expectedFailure

import django
from django.contrib.auth.models import User
from django.template import Context, RequestContext, Template
from django.test import override_settings
from django.utils.functional import SimpleLazyObject

from debug_toolbar.panels.sql import SQLPanel
from debug_toolbar.panels.templates import TemplatesPanel

from ..base import BaseTestCase, IntegrationTestCase
from ..forms import TemplateReprForm
from ..models import NonAsciiRepr


class TemplatesPanelTestCase(BaseTestCase):
    panel_id = TemplatesPanel.panel_id

    def setUp(self):
        super().setUp()
        self.sql_panel = self.toolbar.get_panel_by_id(SQLPanel.panel_id)
        self.sql_panel.enable_instrumentation()

    def tearDown(self):
        self.sql_panel.disable_instrumentation()
        super().tearDown()

    def test_queryset_hook(self):
        response = self.panel.process_request(self.request)
        t = Template("No context variables here!")
        c = Context(
            {
                "queryset": User.objects.all(),
                "deep_queryset": {"queryset": User.objects.all()},
            }
        )
        t.render(c)
        self.panel.generate_stats(self.request, response)

        # ensure the query was NOT logged
        self.assertEqual(len(self.sql_panel._queries), 0)

        self.assertEqual(
            self.panel.templates[0]["context_list"],
            [
                "{'False': False, 'None': None, 'True': True}",
                "{'deep_queryset': '<<triggers database query>>',\n"
                " 'queryset': '<<queryset of auth.User>>'}",
            ],
        )

    def test_template_repr(self):
        # Force widget templates to be included
        self.toolbar.config["SKIP_TEMPLATE_PREFIXES"] = ()

        User.objects.create(username="admin")
        bad_repr = TemplateReprForm()
        if django.VERSION < (5,):
            t = Template("<table>{{ bad_repr }}</table>")
        else:
            t = Template("{{ bad_repr }}")
        c = Context({"bad_repr": bad_repr})
        html = t.render(c)
        self.assertIsNotNone(html)
        self.assertValidHTML(html)

    def test_object_with_non_ascii_repr_in_context(self):
        response = self.panel.process_request(self.request)
        t = Template("{{ object }}")
        c = Context({"object": NonAsciiRepr()})
        t.render(c)
        self.panel.generate_stats(self.request, response)
        self.assertIn("nôt åscíì", self.panel.content)

    def test_insert_content(self):
        """
        Test that the panel only inserts content after generate_stats and
        not the process_request.
        """
        t = Template("{{ object }}")
        c = Context({"object": NonAsciiRepr()})
        t.render(c)
        response = self.panel.process_request(self.request)
        # ensure the panel does not have content yet.
        self.assertNotIn("nôt åscíì", self.panel.content)
        self.panel.generate_stats(self.request, response)
        # ensure the panel renders correctly.
        content = self.panel.content
        self.assertIn("nôt åscíì", content)
        self.assertValidHTML(content)

    def test_custom_context_processor(self):
        response = self.panel.process_request(self.request)
        t = Template("{{ content }}")
        c = RequestContext(self.request, processors=[context_processor])
        t.render(c)
        self.panel.generate_stats(self.request, response)
        self.assertIn(
            "tests.panels.test_template.context_processor", self.panel.content
        )

    def test_disabled(self):
        config = {"DISABLE_PANELS": {"debug_toolbar.panels.templates.TemplatesPanel"}}
        self.assertTrue(self.panel.enabled)
        with self.settings(DEBUG_TOOLBAR_CONFIG=config):
            self.assertFalse(self.panel.enabled)

    def test_empty_context(self):
        response = self.panel.process_request(self.request)
        t = Template("")
        c = Context({})
        t.render(c)
        self.panel.generate_stats(self.request, response)

        # Includes the builtin context but not the empty one.
        self.assertEqual(
            self.panel.templates[0]["context_list"],
            ["{'False': False, 'None': None, 'True': True}"],
        )

    def test_lazyobject(self):
        response = self.panel.process_request(self.request)
        t = Template("")
        c = Context({"lazy": SimpleLazyObject(lambda: "lazy_value")})
        t.render(c)
        self.panel.generate_stats(self.request, response)
        self.assertNotIn("lazy_value", self.panel.content)

    def test_lazyobject_eval(self):
        response = self.panel.process_request(self.request)
        t = Template("{{lazy}}")
        c = Context({"lazy": SimpleLazyObject(lambda: "lazy_value")})
        self.assertEqual(t.render(c), "lazy_value")
        self.panel.generate_stats(self.request, response)
        self.assertIn("lazy_value", self.panel.content)

    @override_settings(
        DEBUG=True,
        DEBUG_TOOLBAR_PANELS=["debug_toolbar.panels.templates.TemplatesPanel"],
    )
    def test_template_source(self):
        from django.core import signing
        from django.template.loader import get_template

        template = get_template("basic.html")
        url = "/__debug__/template_source/"
        data = {
            "template": template.template.name,
            "template_origin": signing.dumps(template.template.origin.name),
        }

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)


@override_settings(
    DEBUG=True, DEBUG_TOOLBAR_PANELS=["debug_toolbar.panels.templates.TemplatesPanel"]
)
class JinjaTemplateTestCase(IntegrationTestCase):
    def test_django_jinja2(self):
        r = self.client.get("/regular_jinja/foobar/")
        self.assertContains(r, "Test for foobar (Jinja)")
        # This should be 2 templates because of the parent template.
        # See test_django_jinja2_parent_template_instrumented
        self.assertContains(r, "<h3>Templates (1 rendered)</h3>")
        self.assertContains(r, "<small>basic.jinja</small>")

    @expectedFailure
    def test_django_jinja2_parent_template_instrumented(self):
        """
        When Jinja2 templates are properly instrumented, the
        parent template should be instrumented.
        """
        r = self.client.get("/regular_jinja/foobar/")
        self.assertContains(r, "Test for foobar (Jinja)")
        self.assertContains(r, "<h3>Templates (2 rendered)</h3>")
        self.assertContains(r, "<small>basic.jinja</small>")


def context_processor(request):
    return {"content": "set by processor"}
