from django.template import Context, Template
from django.test import SimpleTestCase

from debug_toolbar.templatetags.debug_toolbar import dict_items


class DictItemsTestCase(SimpleTestCase):
    def test_returns_pairs_for_a_mapping(self):
        self.assertEqual(list(dict_items({"a": 1, "b": 2})), [("a", 1), ("b", 2)])

    def test_key_named_items_does_not_shadow_the_method(self):
        """The whole point of the filter. See #2453."""
        self.assertEqual(
            list(dict_items({"items": "a string"})), [("items", "a string")]
        )

    def test_non_mappings_yield_nothing(self):
        for value in (None, "a string", [1, 2, 3], 42):
            with self.subTest(value=value):
                self.assertEqual(list(dict_items(value)), [])

    def test_rendered_in_a_for_loop(self):
        template = Template(
            "{% load debug_toolbar %}"
            "{% for key, value in data|dict_items %}{{ key }}={{ value }};"
            "{% empty %}empty{% endfor %}"
        )
        cases = [
            ({"foo": "bar"}, "foo=bar;"),
            ({"items": "a string"}, "items=a string;"),
            ({"items": [1, 2, 3]}, "items=[1, 2, 3];"),
            (None, "empty"),
            ("a string", "empty"),
        ]
        for data, expected in cases:
            with self.subTest(data=data):
                self.assertEqual(template.render(Context({"data": data})), expected)
