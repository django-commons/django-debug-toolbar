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
class BuiltInShortcutTestCase(IntegrationTestCase):
    def test_builtin_panels_advertise_their_letters(self):
        response = self.client.get("/regular/basic/")
        for keys in (
            "h",
            "v",
            "i",
            "l",
            "d",
            "r",
            "s",
            "f",
            "t",
            "a",
            "c",
            "n",
            "k",
            "y",
        ):
            self.assertContains(response, f'aria-keyshortcuts="g {keys}"')
        self.assertNotContains(response, 'aria-keyshortcuts="g p"')
        self.assertContains(response, 'id="djDebugShortcuts"')


@override_settings(
    DEBUG=True,
    DEBUG_TOOLBAR_PANELS=[
        "tests.panels.test_shortcuts.FirstPanel",
        "tests.panels.test_shortcuts.SecondPanel",
        "tests.panels.test_shortcuts.NoShortcutPanel",
    ],
)
class DuplicateShortcutTestCase(IntegrationTestCase):
    def test_earlier_panel_keeps_the_letter(self):
        response = self.client.get("/regular/basic/")
        self.assertContains(
            response,
            'href="#" title="First" class="FirstPanel" aria-controls="FirstPanel"'
            ' aria-expanded="false" aria-keyshortcuts="g s"',
        )
        self.assertContains(
            response,
            'href="#" title="Second" class="SecondPanel" aria-controls="SecondPanel"'
            ' aria-expanded="false">',
        )
        self.assertNotContains(
            response,
            'aria-controls="SecondPanel" aria-expanded="false" aria-keyshortcuts',
        )
        self.assertContains(
            response,
            'href="#" title="Plain" class="NoShortcutPanel"'
            ' aria-controls="NoShortcutPanel" aria-expanded="false">',
        )
