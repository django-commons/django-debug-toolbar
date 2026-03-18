from collections import namedtuple

from debug_toolbar.panels.versions import VersionsPanel

from ..base import BaseTestCase

version_info_t = namedtuple(
    "version_info_t", ("major", "minor", "micro", "releaselevel", "serial")
)


class VersionsPanelTestCase(BaseTestCase):
    panel_id = VersionsPanel.panel_id

    def test_app_version_from_get_version_fn(self):
        class FakeApp:
            def get_version(self):
                return version_info_t(1, 2, 3, "", "")

        self.assertEqual(self.panel.get_app_version(FakeApp()), "1.2.3")

    def test_incompatible_app_version_fn(self):
        class FakeApp:
            def get_version(self, some_other_arg):
                # This should be ignored by the get_version_from_app
                return version_info_t(0, 0, 0, "", "")

            VERSION = version_info_t(1, 2, 3, "", "")

        self.assertEqual(self.panel.get_app_version(FakeApp()), "1.2.3")

    def test_app_version_from_VERSION(self):
        class FakeApp:
            VERSION = version_info_t(1, 2, 3, "", "")

        self.assertEqual(self.panel.get_app_version(FakeApp()), "1.2.3")

    def test_app_version_from_underscore_version(self):
        class FakeApp:
            __version__ = version_info_t(1, 2, 3, "", "")

        self.assertEqual(self.panel.get_app_version(FakeApp()), "1.2.3")
