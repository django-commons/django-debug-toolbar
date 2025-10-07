import unittest

from django.http import QueryDict
from django.test import override_settings

import debug_toolbar.utils
from debug_toolbar.utils import (
    get_editor_url,
    get_name_from_obj,
    get_stack,
    get_stack_trace,
    render_stacktrace,
    sanitize_and_sort_request_vars,
    tidy_stacktrace,
)


class GetNameFromObjTestCase(unittest.TestCase):
    def test_func(self):
        def x():
            return 1

        res = get_name_from_obj(x)
        self.assertEqual(
            res, "tests.test_utils.GetNameFromObjTestCase.test_func.<locals>.x"
        )

    def test_lambda(self):
        res = get_name_from_obj(lambda: 1)
        self.assertEqual(
            res, "tests.test_utils.GetNameFromObjTestCase.test_lambda.<locals>.<lambda>"
        )

    def test_class(self):
        class A:
            pass

        res = get_name_from_obj(A)
        self.assertEqual(
            res, "tests.test_utils.GetNameFromObjTestCase.test_class.<locals>.A"
        )


class RenderStacktraceTestCase(unittest.TestCase):
    def test_importlib_path_issue_1612(self):
        trace = [
            ("/server/app.py", 1, "foo", ["code line 1", "code line 2"], {"foo": "bar"})
        ]
        result = render_stacktrace(trace)
        self.assertIn('<span class="djdt-path">/server/</span>', result)
        self.assertIn('<span class="djdt-file">app.py</span> in', result)

        trace = [
            (
                "<frozen importlib._bootstrap>",
                1,
                "foo",
                ["code line 1", "code line 2"],
                {"foo": "bar"},
            )
        ]
        result = render_stacktrace(trace)
        self.assertIn('<span class="djdt-path"></span>', result)
        self.assertIn(
            '<span class="djdt-file">&lt;frozen importlib._bootstrap&gt;</span> in',
            result,
        )


class StackTraceTestCase(unittest.TestCase):
    @override_settings(DEBUG_TOOLBAR_CONFIG={"HIDE_IN_STACKTRACES": []})
    def test_get_stack_trace_skip(self):
        stack_trace = get_stack_trace(skip=-1)
        self.assertTrue(len(stack_trace) > 2)
        self.assertEqual(stack_trace[-1][0], debug_toolbar.utils.__file__)
        self.assertEqual(stack_trace[-1][2], "get_stack_trace")
        self.assertEqual(stack_trace[-2][0], __file__)
        self.assertEqual(stack_trace[-2][2], "test_get_stack_trace_skip")

        stack_trace = get_stack_trace()
        self.assertTrue(len(stack_trace) > 1)
        self.assertEqual(stack_trace[-1][0], __file__)
        self.assertEqual(stack_trace[-1][2], "test_get_stack_trace_skip")

    def test_deprecated_functions(self):
        with self.assertWarns(DeprecationWarning):
            stack = get_stack()
        self.assertEqual(stack[0][1], __file__)
        with self.assertWarns(DeprecationWarning):
            stack_trace = tidy_stacktrace(reversed(stack))
        self.assertEqual(stack_trace[-1][0], __file__)

    @override_settings(DEBUG_TOOLBAR_CONFIG={"ENABLE_STACKTRACES_LOCALS": True})
    def test_locals(self):
        # This wrapper class is necessary to mask the repr() of the list
        # returned by get_stack_trace(); otherwise the 'test_locals_value_1'
        # string will also be present in rendered_stack_2.
        class HideRepr:
            def __init__(self, value):
                self.value = value

        x = "test_locals_value_1"
        stack_1_wrapper = HideRepr(get_stack_trace())

        x = x.replace("1", "2")
        stack_2_wrapper = HideRepr(get_stack_trace())

        rendered_stack_1 = render_stacktrace(stack_1_wrapper.value)
        self.assertIn("test_locals_value_1", rendered_stack_1)
        self.assertNotIn("test_locals_value_2", rendered_stack_1)

        rendered_stack_2 = render_stacktrace(stack_2_wrapper.value)
        self.assertNotIn("test_locals_value_1", rendered_stack_2)
        self.assertIn("test_locals_value_2", rendered_stack_2)


class SanitizeAndSortRequestVarsTestCase(unittest.TestCase):
    """Tests for the sanitize_and_sort_request_vars function."""

    def test_dict_sanitization(self):
        """Test sanitization of a regular dictionary."""
        test_dict = {
            "username": "testuser",
            "password": "secret123",
            "api_key": "abc123",
        }
        result = sanitize_and_sort_request_vars(test_dict)

        # Convert to dict for easier testing
        result_dict = dict(result["list"])

        self.assertEqual(result_dict["username"], "testuser")
        self.assertEqual(result_dict["password"], "********************")
        self.assertEqual(result_dict["api_key"], "********************")

    def test_querydict_sanitization(self):
        """Test sanitization of a QueryDict."""
        query_dict = QueryDict("username=testuser&password=secret123&api_key=abc123")
        result = sanitize_and_sort_request_vars(query_dict)

        # Convert to dict for easier testing
        result_dict = dict(result["list"])

        self.assertEqual(result_dict["username"], "testuser")
        self.assertEqual(result_dict["password"], "********************")
        self.assertEqual(result_dict["api_key"], "********************")

    def test_non_sortable_dict_keys(self):
        """Test dictionary with keys that can't be sorted."""
        test_dict = {
            1: "one",
            "2": "two",
            None: "none",
        }
        result = sanitize_and_sort_request_vars(test_dict)
        self.assertEqual(len(result["list"]), 3)
        result_dict = dict(result["list"])
        self.assertEqual(result_dict[1], "one")
        self.assertEqual(result_dict["2"], "two")
        self.assertEqual(result_dict[None], "none")

    def test_querydict_multiple_values(self):
        """Test QueryDict with multiple values for the same key."""
        query_dict = QueryDict("name=bar1&name=bar2&title=value")
        result = sanitize_and_sort_request_vars(query_dict)
        result_dict = dict(result["list"])
        self.assertEqual(result_dict["name"], ["bar1", "bar2"])
        self.assertEqual(result_dict["title"], "value")

    def test_non_dict_input(self):
        """Test handling of non-dict input."""
        test_input = ["not", "a", "dict"]
        result = sanitize_and_sort_request_vars(test_input)
        self.assertEqual(result["raw"], test_input)


class GetEditorUrlTestCase(unittest.TestCase):
    @override_settings(DEBUG_TOOLBAR_CONFIG={"EDITOR": "vscode"})
    def test_get_editor_url(self):
        editors = {
            "cursor": "cursor://file/test.py:5",
            "emacs": "emacs://open?url=file://test.py&line=5",
            "espresso": "x-espresso://open?filepath=test.py&lines=5",
            "idea": "idea://open?file=test.py&line=5",
            "idea-remote": "javascript:(()=>{let r=new XMLHttpRequest; r.open('get','http://localhost:63342/api/file/?file=test.py&line=5');r.send();})()",
            "macvim": "mvim://open/?url=file://test.py&line=5",
            "nova": "nova://open?path=test.py&line=5",
            "pycharm": "pycharm://open?file=test.py&line=5",
            "pycharm-remote": "javascript:(()=>{let r=new XMLHttpRequest; r.open('get','http://localhost:63342/api/file/test.py:5');r.send();})()",
            "sublime": "subl://open?url=file://test.py&line=5",
            "vscode": "vscode://file/test.py:5",
            "vscode-insiders": "vscode-insiders://file/test.py:5",
            "vscode-remote": "vscode://vscode-remote/test.py:5",
            "vscode-insiders-remote": "vscode-insiders://vscode-remote/test.py:5",
            "vscodium": "vscodium://file/test.py:5",
            "windsurf": "windsurf://file/test.py:5",
        }
        for editor, expected_url in editors.items():
            with (
                self.subTest(editor=editor),
                override_settings(DEBUG_TOOLBAR_CONFIG={"EDITOR": editor}),
            ):
                url = get_editor_url("test.py", 5)
                self.assertEqual(url, expected_url)
