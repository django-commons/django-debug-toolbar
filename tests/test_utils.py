import unittest

from django.http import QueryDict
from django.test import override_settings

import debug_toolbar.utils
from debug_toolbar.utils import (
    get_name_from_obj,
    get_sorted_request_variable,
    get_stack,
    get_stack_trace,
    render_stacktrace,
    sanitize_value,
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


class SanitizeValueTestCase(unittest.TestCase):
    """Tests for the sanitize_value function."""

    def test_sanitize_sensitive_key(self):
        """Test that sensitive keys are sanitized."""
        self.assertEqual(
            sanitize_value("password", "secret123"), "********************"
        )
        self.assertEqual(sanitize_value("api_key", "abc123"), "********************")
        self.assertEqual(sanitize_value("auth_token", "xyz789"), "********************")

    def test_sanitize_non_sensitive_key(self):
        """Test that non-sensitive keys are not sanitized."""
        self.assertEqual(sanitize_value("username", "testuser"), "testuser")
        self.assertEqual(
            sanitize_value("email", "user@example.com"), "user@example.com"
        )

    @override_settings(DEBUG_TOOLBAR_CONFIG={"SANITIZE_REQUEST_DATA": False})
    def test_sanitize_disabled(self):
        """Test that sanitization can be disabled."""
        self.assertEqual(sanitize_value("password", "secret123"), "secret123")

    @override_settings(
        DEBUG_TOOLBAR_CONFIG={"REQUEST_SANITIZATION_PATTERNS": ("CUSTOM",)}
    )
    def test_custom_sanitization_patterns(self):
        """Test that custom sanitization patterns can be used."""
        self.assertEqual(
            sanitize_value("custom_field", "sensitive"), "********************"
        )
        self.assertEqual(
            sanitize_value("password", "secret123"),
            "secret123",  # Not sanitized with custom pattern
        )


class GetSortedRequestVariableTestCase(unittest.TestCase):
    """Tests for the get_sorted_request_variable function."""

    def test_dict_sanitization(self):
        """Test sanitization of a regular dictionary."""
        test_dict = {
            "username": "testuser",
            "password": "secret123",
            "api_key": "abc123",
        }
        result = get_sorted_request_variable(test_dict)

        # Convert to dict for easier testing
        result_dict = dict(result["list"])

        self.assertEqual(result_dict["username"], "testuser")
        self.assertEqual(result_dict["password"], "********************")
        self.assertEqual(result_dict["api_key"], "********************")

    def test_querydict_sanitization(self):
        """Test sanitization of a QueryDict."""
        query_dict = QueryDict("username=testuser&password=secret123&api_key=abc123")
        result = get_sorted_request_variable(query_dict)

        # Convert to dict for easier testing
        result_dict = dict(result["list"])

        self.assertEqual(result_dict["username"], "testuser")
        self.assertEqual(result_dict["password"], "********************")
        self.assertEqual(result_dict["api_key"], "********************")

    @override_settings(DEBUG_TOOLBAR_CONFIG={"SANITIZE_REQUEST_DATA": False})
    def test_sanitization_disabled(self):
        """Test that sanitization can be disabled."""
        test_dict = {"username": "testuser", "password": "secret123"}
        result = get_sorted_request_variable(test_dict)

        # Convert to dict for easier testing
        result_dict = dict(result["list"])

        self.assertEqual(result_dict["username"], "testuser")
        self.assertEqual(result_dict["password"], "secret123")  # Not sanitized
