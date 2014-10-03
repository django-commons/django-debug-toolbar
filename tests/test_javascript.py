# coding: utf-8

from __future__ import absolute_import, unicode_literals

import calendar
import os
from datetime import timedelta

try:
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
except ImportError:
    NoSuchElementException, WebDriverWait, Keys, ActionChains = (
        None, None, None, None)

try:
    from django.contrib.staticfiles.testing import StaticLiveServerTestCase \
        as LiveServerTestCase
except ImportError:
    # When we're using < Django 1.7
    from django.test import LiveServerTestCase

from django.test.utils import override_settings
from django.utils import timezone
from django.utils.unittest import skipIf, skipUnless

from debug_toolbar.settings import PANELS_DEFAULTS

from .selenium_utils import create_web_driver


webdriver = create_web_driver()


class ToolbarTestCase(LiveServerTestCase):
    """Helper class that provides a few methods for fetching elements."""
    @classmethod
    def setUpClass(cls):
        super(ToolbarTestCase, cls).setUpClass()
        cls.selenium = create_web_driver()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(ToolbarTestCase, cls).tearDownClass()

    def setUp(self):
        self.selenium.delete_all_cookies()
        self.selenium.get(self.live_server_url + '/execute_sql/')
        self.get_web_driver_wait().until(
            lambda selenium:
            self.get_panel_trigger("HeadersPanel").is_displayed()
        )

    def get_panel_trigger(self, name):
        return self.selenium.find_element_by_class_name(name)

    def get_panel(self, name):
        return self.selenium.find_element_by_id(name)

    def get_web_driver_wait(self):
        return WebDriverWait(self.selenium, timeout=10)


@skipIf(webdriver is None, "selenium isn't installed")
@skipUnless(
    'DJANGO_SELENIUM_TESTS' in os.environ, "selenium tests not requested")
@override_settings(DEBUG=True, DEBUG_TOOLBAR_PANELS=PANELS_DEFAULTS + [
    'debug_toolbar.panels.profiling.ProfilingPanel',
])
class InitTestCase(ToolbarTestCase):

    def test_show_toolbar(self):
        toolbar = self.selenium.find_element_by_id('djDebug')
        self.assertTrue(toolbar.is_displayed())

    def test_panel_li_a_click_once(self):
        panel_name = "HeadersPanel"
        panel_trigger = self.get_panel_trigger(panel_name)
        panel = self.get_panel(panel_name)
        self.assertFalse(panel.is_displayed())
        panel_trigger.click()
        self.assertTrue(panel.is_displayed())

        # Verify that the panels parent had the djdt-active class added
        trigger_count = self.selenium.execute_script(
            "return djdt.jQuery('#djDebugToolbar').find('.djdt-active')"
            ".find('.{0}').length".format(panel_name)
        )
        self.assertEquals(trigger_count, 1)

    def test_panel_li_a_click_twice(self):
        panel_name = "HeadersPanel"
        panel_trigger = self.get_panel_trigger(panel_name)
        panel = self.get_panel(panel_name)
        # Click the trigger twice
        panel_trigger.click()
        panel_trigger.click()
        # Verify that the panels parent had the djdt-active class removed
        trigger_count = self.selenium.execute_script(
            "return djdt.jQuery('#djDebugToolbar').find('.djdt-active')"
            ".find('.{0}').length".format(panel_name)
        )
        self.assertEquals(trigger_count, 0)
        self.assertFalse(panel.is_displayed())

    def test_ajax_fail(self):
        panel_name = "HeadersPanel"
        panel_trigger = self.get_panel_trigger(panel_name)
        self.selenium.execute_script(
            "djdt.jQuery('#djDebug').data('render-panel-url', '/test_fail/')"
        )
        debug_window = self.selenium.find_element_by_id("djDebugWindow")
        self.assertFalse(debug_window.is_displayed())
        panel_trigger.click()
        self.assertTrue(debug_window.is_displayed())

    def test_dj_debug_close(self):
        panel_name = "HeadersPanel"
        panel_trigger = self.get_panel_trigger(panel_name)
        panel = self.get_panel(panel_name)
        # Click a panel to set a djdt-active class
        panel_trigger.click()
        active_panel_items = self.selenium.find_element_by_css_selector(
            "#djDebugToolbar li.djdt-active")
        self.assertTrue(active_panel_items.is_displayed())
        panel.find_element_by_css_selector(
            "#djDebug a.djDebugClose").click()
        self.assertRaises(
            NoSuchElementException,
            self.selenium.find_element_by_css_selector,
            "#djDebugToolbar li.djdt-active"
        )

    def test_click_panel_button_checkbox(self):
        panel_name = "HeadersPanel"
        panel_trigger = self.get_panel_trigger(panel_name)
        checkbox = panel_trigger.find_element_by_xpath('..')\
            .find_element_by_css_selector("input[type=checkbox]")
        cookie_name = checkbox.get_attribute("data-cookie")
        self.assertEquals(cookie_name, "djdt{0}".format(panel_name))
        cookie = self.selenium.get_cookie(cookie_name)
        self.assertIsNone(cookie)
        # Click on the checkbox to turn off
        checkbox.click()
        cookie = self.selenium.get_cookie(cookie_name)
        self.assertEquals(cookie['name'], cookie_name)
        self.assertEquals(cookie['value'], 'off')
        # Click on it again to verify it's turned on again.
        checkbox.click()
        cookie = self.selenium.get_cookie(cookie_name)
        self.assertEquals(cookie['value'], 'on')

    def test_remote_class_click(self):
        # Click the sql panel trigger
        for panel_name in ['TemplatesPanel', 'SQLPanel']:
            self.selenium.find_element_by_class_name(panel_name).click()
            panel = self.selenium.find_element_by_id(panel_name)

            remote_call_trigger = self.get_web_driver_wait().until(
                lambda selenium: panel.find_element_by_class_name('remoteCall')
            )

            remote_call_trigger.click()
            debug_window = self.selenium.find_element_by_id('djDebugWindow')
            if panel_name == 'TemplatesPanel':
                code_section = self.get_web_driver_wait().until(
                    lambda selenium:
                    debug_window.find_element_by_tag_name('code')
                )
                self.assertEquals(
                    "basic.html", code_section.get_attribute('innerHTML')
                )
            elif panel_name == 'SQLPanel':
                sql_select = self.get_web_driver_wait().until(
                    lambda selenium:
                    debug_window.find_element_by_class_name('djdt-scroll')
                )
                self.assertIn(
                    "<dt>Executed SQL</dt>",
                    sql_select.get_attribute('innerHTML')
                )
            self.assertTrue(
                debug_window.is_displayed()
            )
            # Click to go back to the Templates Panel
            debug_window.find_element_by_class_name('djDebugBack').click()
            self.assertFalse(
                debug_window.is_displayed()
            )

    def test_toggle_switch_click(self):
        panel_name = 'SQLPanel'
        self.selenium.find_element_by_class_name(panel_name).click()
        panel = self.selenium.find_element_by_id(panel_name)
        toggle_switch = panel.find_element_by_class_name('djToggleSwitch')
        id_javascript_selector = (
            "return djdt.jQuery('#{0}').find('.djToggleSwitch').attr('{1}')")
        target_id = self.selenium.execute_script(
            id_javascript_selector.format(panel_name, 'data-toggle-id')
        )
        toggle_class = "djToggleDetails_{0}".format(target_id)
        toggled_element = panel.find_element_by_class_name(toggle_class)
        toggled = "djUnselected"
        untoggled = "djSelected"
        if panel_name == "ProfilingPanel":
            # Profiling panel is reversed.
            toggled, untoggled = untoggled, toggled

        self.assertNotIn(
            untoggled,
            toggled_element.get_attribute('className')
        )
        if panel_name != "ProfilingPanel":
            self.assertIn(
                toggled,
                toggled_element.get_attribute('className')
            )
        toggle_switch.click()
        self.assertIn(
            untoggled,
            toggled_element.get_attribute('className')
        )
        self.assertNotIn(
            toggled,
            toggled_element.get_attribute('className')
        )

    def test_hide_toolbar_button(self):
        panel_name = "HeadersPanel"
        panel_trigger = self.get_panel_trigger(panel_name)
        self.assertTrue(panel_trigger.is_displayed())
        self.selenium.find_element_by_id("djHideToolBarButton").click()
        self.get_web_driver_wait().until(
            lambda selenium: not panel_trigger.is_displayed())

    def test_show_toolbar_button(self):
        panel_name = "HeadersPanel"
        panel_trigger = self.get_panel_trigger(panel_name)
        self.selenium.find_element_by_id("djHideToolBarButton").click()

        self.get_web_driver_wait().until(
            lambda selenium:
            self.selenium.find_element_by_id(
                'djShowToolBarButton').is_displayed()
        )
        show_button = self.selenium.find_element_by_id('djShowToolBarButton')
        self.assertTrue(show_button.is_displayed())
        self.assertFalse(panel_trigger.is_displayed())
        # Verify when the show button is clicked and held that it's not hidden.
        ActionChains(self.selenium).click_and_hold(show_button).perform()
        self.assertTrue(show_button.is_displayed())
        show_button.click()
        self.assertTrue(panel_trigger.is_displayed())

    def test_move_show_toolbar_button(self):
        self.selenium.find_element_by_id("djHideToolBarButton").click()
        show_button = self.selenium.find_element_by_id('djShowToolBarButton')

        action = ActionChains(self.selenium).click_and_hold(show_button)
        action.move_to_element_with_offset(show_button, 100, 100)
        action.release(show_button)
        action.perform()

        cookie = self.selenium.get_cookie('djdttop')
        self.assertEquals(cookie['name'], 'djdttop')

    def test_close_binding(self):
        self.selenium.find_element_by_class_name('SQLPanel').click()
        sql_panel = self.selenium.find_element_by_id('SQLPanel')
        toolbar = self.selenium.find_element_by_id('djDebugToolbar')
        self.selenium.find_element_by_class_name('remoteCall').click()
        debug_window = self.selenium.find_element_by_id('djDebugWindow')
        self.get_web_driver_wait().until(
            lambda selenium:
            debug_window.find_element_by_class_name('djdt-scroll')
        )
        self.assertTrue(debug_window.is_displayed())
        # Verify the sql debug window is hidden on close
        self.selenium.execute_script('djdt.close()')
        self.assertFalse(debug_window.is_displayed())
        self.assertTrue(sql_panel.is_displayed())

        # Verify the sql panel is hidden on click
        self.selenium.execute_script('djdt.close()')
        self.assertFalse(sql_panel.is_displayed())
        self.assertTrue(toolbar.is_displayed())

        # Verify the sql debug window is hidden on click
        self.selenium.execute_script('djdt.close()')
        self.get_web_driver_wait().until(
            lambda selenium: not toolbar.is_displayed())
        self.assertFalse(sql_panel.is_displayed())

    @skipIf(True, "Unsure how to produce.")
    def test_debug_hoverable(self):
        pass

    def test_hidden_via_cookie(self):
        self.assertTrue(
            self.selenium.find_element_by_id('djDebugToolbar').is_displayed())
        self.selenium.execute_script('djdt.close()')
        self.get_web_driver_wait().until(
            lambda selenium:
            selenium.find_element_by_id('djShowToolBarButton').is_displayed())
        # Verify that when the page reloads that the toolbar is still closed.
        self.selenium.refresh()
        self.assertFalse(
            self.selenium.find_element_by_id('djDebugToolbar').is_displayed())
        show_button = self.selenium.find_element_by_id('djShowToolBarButton')
        self.assertTrue(show_button.is_displayed())


@skipIf(webdriver is None, "selenium isn't installed")
@skipUnless(
    'DJANGO_SELENIUM_TESTS' in os.environ, "selenium tests not requested")
@override_settings(DEBUG=True)
class APITestCase(ToolbarTestCase):

    def test_show_toolbar(self):
        self.selenium.execute_script("djdt.hide_toolbar(false)")
        # Verify that it closes the toolbar.
        self.assertTrue(self.get_web_driver_wait().until(
            lambda selenium:
            selenium.find_element_by_id('djDebugToolbarHandle').is_displayed())
        )
        self.selenium.execute_script("djdt.show_toolbar(true)")
        handle = self.selenium.find_element_by_id('djDebugToolbarHandle')
        self.assertFalse(handle.is_displayed())
        self.assertTrue(self.get_web_driver_wait().until(
            lambda selenium:
            selenium.find_element_by_id('djDebugToolbar').is_displayed())
        )
        cookie = self.selenium.get_cookie('djdt')
        self.assertEquals(cookie['name'], 'djdt')
        self.assertEquals(cookie['value'], 'show')
        action = ActionChains(self.selenium)
        action.key_down(
            Keys.ESCAPE,
            self.selenium.find_element_by_tag_name('body')
        )
        action.perform()
        # Verify that it closes the toolbar.
        self.assertTrue(self.get_web_driver_wait().until(
            lambda selenium:
            selenium.find_element_by_id('djDebugToolbarHandle').is_displayed())
        )

    def test_hide_toolbar(self):
        self.selenium.find_element_by_class_name('SQLPanel').click()
        sql_panel = self.selenium.find_element_by_id('SQLPanel')
        toolbar = self.selenium.find_element_by_id('djDebugToolbar')
        self.selenium.find_element_by_class_name('remoteCall').click()
        debug_window = self.selenium.find_element_by_id('djDebugWindow')
        self.get_web_driver_wait().until(
            lambda selenium:
            debug_window.find_element_by_class_name('djdt-scroll')
        )
        self.assertTrue(debug_window.is_displayed())

        # Hide the toolbar
        self.selenium.execute_script('djdt.hide_toolbar(false)')
        self.assertTrue(self.get_web_driver_wait().until(
            lambda selenium: not debug_window.is_displayed())
        )
        self.assertTrue(self.get_web_driver_wait().until(
            lambda selenium: not toolbar.is_displayed())
        )
        self.assertFalse(sql_panel.is_displayed())
        cookie = self.selenium.get_cookie('djdt')
        self.assertEquals(cookie['value'], 'show')
        # Run the function again, but with set_cookie = true
        self.selenium.execute_script('djdt.hide_toolbar(true)')
        cookie = self.selenium.get_cookie('djdt')
        self.assertEquals(cookie['name'], 'djdt')
        self.assertEquals(cookie['value'], 'hide')

    def test_cookie_get_none(self):
        null_cookie = self.selenium.execute_script(
            "return djdt.cookie.get('test')"
        )
        self.assertIsNone(null_cookie)

    def test_cookie_get(self):
        key = str("test")
        value = str("val")
        path = str("/")
        expires = calendar.timegm(
            (timezone.now() + timedelta(days=10)).timetuple()
        )
        domain = str("localhost")
        self.selenium.add_cookie({
            "name": key,
            "value": value,
            "expiry": expires,
            "path": path,
            "domain": domain,
        })
        actual_value = self.selenium.execute_script(
            "return djdt.cookie.get('{0}')".format(key)
        )
        self.assertEquals(actual_value, value)

    def test_cookie_set(self):
        key = str("test")
        value = str("val")
        path = str("/")
        expires = 3
        domain = str("localhost")
        expires_lower_bound = timezone.now().date() + timedelta(days=expires)
        expires_upper_bound = expires_lower_bound + timedelta(days=1)
        self.selenium.execute_script(
            "djdt.cookie.set('{0}','{1}',"
            "{{'path':'{2}','expires':{3},'domain':'{4}'}})"
            .format(key, value, path, expires, domain)
        )
        cookie = self.selenium.get_cookie(key)
        self.assertEquals(cookie['name'], key)
        self.assertEquals(cookie['value'], value)
        self.assertEquals(cookie['path'], path)
        self.assertEquals(cookie['domain'], domain)
        # Verify the expiration date is close to the value we passed in.
        # The method calculates the current time, so it's difficult to compare.
        self.assertGreaterEqual(
            cookie['expiry'],
            calendar.timegm(expires_lower_bound.timetuple())
        )
        self.assertLessEqual(
            cookie['expiry'],
            calendar.timegm(expires_upper_bound.timetuple())
        )
