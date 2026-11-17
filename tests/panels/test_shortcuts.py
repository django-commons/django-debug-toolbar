from django.test import override_settings

from debug_toolbar.panels import Panel

from ..base import IntegrationTestCase


class FirstPanel(Panel):
    shortcut_key = "s"
    title = "First"


class SecondPanel(Panel):
    shortcut_key = "s"
    title = "Second"


class NoShortcutPanel(Panel):
    title = "Plain"


@override_settings(DEBUG=True)
class ShortcutsTestCase(IntegrationTestCase):
    def test_rendering(self):
        panels = [
            "tests.panels.test_shortcuts.FirstPanel",
            "tests.panels.test_shortcuts.SecondPanel",
            "tests.panels.test_shortcuts.NoShortcutPanel",
        ]
        cases = [
            # Disabling the config stops advertising panel shortcuts.
            (
                {"DEBUG_TOOLBAR_CONFIG": {"ENABLE_KEYBOARD_SHORTCUTS": False}},
                ['data-keyboard-shortcuts="False"'],
                ["aria-keyshortcuts", 'id="djDebugShortcuts"'],
            ),
            # The earlier of two panels using the same letter keeps it.
            (
                {"DEBUG_TOOLBAR_PANELS": panels},
                [
                    'id="djDebugShortcuts"',
                    (
                        'title="First" class="FirstPanel" aria-controls="FirstPanel"'
                        ' aria-expanded="false" aria-keyshortcuts="g s"'
                    ),
                    (
                        'title="Second" class="SecondPanel" aria-controls="SecondPanel"'
                        ' aria-expanded="false">'
                    ),
                    (
                        'title="Plain" class="NoShortcutPanel"'
                        ' aria-controls="NoShortcutPanel" aria-expanded="false">'
                    ),
                ],
                ['aria-controls="SecondPanel" aria-expanded="false" aria-keyshortcuts'],
            ),
        ]
        for overrides, contains, not_contains in cases:
            with self.subTest(**overrides):
                with self.settings(**overrides):
                    response = self.client.get("/regular/basic/")
                for fragment in contains:
                    with self.subTest(fragment=fragment):
                        self.assertContains(response, fragment)
                for fragment in not_contains:
                    with self.subTest(fragment=fragment):
                        self.assertNotContains(response, fragment)
