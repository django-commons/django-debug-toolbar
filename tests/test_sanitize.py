import unittest

from debug_toolbar.sanitize import force_str


class ForceStrTestCase(unittest.TestCase):
    def test_success_convert(self):
        input = 0

        self.assertEqual(force_str(input), "0")

    def test_failed_convert(self):
        input = bytes.fromhex(
            "a3f2b8c14e972d5a8fb3c7291a64e0859c472bf63d18a0945e73b2c84f917ae2"
        )
        self.assertEqual(
            force_str(input), "Django Debug Toolbar was unable to parse value."
        )
