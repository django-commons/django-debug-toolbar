from unittest.mock import patch

from django.test import TestCase

from debug_toolbar.settings import _is_running_tests


class SettingsTestCase(TestCase):
    @patch("debug_toolbar.settings.sys")
    @patch("debug_toolbar.settings.os")
    def test_is_running_tests(self, mock_os, mock_sys):
        mock_sys.argv = "test"
        mock_os.environ = {}
        self.assertTrue(_is_running_tests())

        mock_sys.argv = ""
        mock_os.environ = {}
        self.assertFalse(_is_running_tests())

        mock_sys.argv = ""
        mock_os.environ = {"PYTEST_VERSION": "1"}
        self.assertTrue(_is_running_tests())
