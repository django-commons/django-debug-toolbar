import argparse
import importlib
import os
import signal
import subprocess
from time import sleep

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", required=True)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--outfile", "-o", required=True)
    parser.add_argument("--width", type=int, default=900)
    parser.add_argument("--height", type=int, default=1200)
    return parser.parse_args()


def create_webdriver_options(browser, headless):
    mod = importlib.import_module(f"selenium.webdriver.{browser}.options")
    options = mod.Options()
    if headless:
        options.headless = True
    return options


def create_webdriver(browser, headless):
    mod = importlib.import_module(f"selenium.webdriver.{browser}.webdriver")
    return mod.WebDriver(options=create_webdriver_options(browser, headless))


def example_server():
    proc = subprocess.Popen(["make", "example"])
    # `make example` runs a few things before runserver.
    sleep(2)
    return proc


def set_viewport_size(selenium, width, height):
    script = """
        return [
            window.outerWidth - window.innerWidth + arguments[0],
            window.outerHeight - window.innerHeight + arguments[1],
        ];
    """
    window_width, window_height = selenium.execute_script(script, width, height)
    selenium.set_window_size(window_width, window_height)


def submit_form(selenium, data):
    url = selenium.current_url
    for name, value in data.items():
        el = selenium.find_element(By.NAME, name)
        el.send_keys(value)
    el.send_keys(Keys.RETURN)
    WebDriverWait(selenium, timeout=5).until(EC.url_changes(url))


def find_including_toolbar(selenium, by, value):
    """Find the toolbar elements within the shadow root DOM"""
    selectors = {
        By.ID: "#{}",
        By.CLASS_NAME: ".{}",
        By.TAG_NAME: "{}",
        By.CSS_SELECTOR: "{}",
    }
    try:
        return selenium.find_element(by, value)
    except NoSuchElementException:
        shadow_root = selenium.find_element(By.ID, "djDebugRoot").shadow_root
        return shadow_root.find_element(By.CSS_SELECTOR, selectors[by].format(value))


def main():
    args = parse_args()
    with example_server() as p:
        try:
            with create_webdriver(args.browser, args.headless) as selenium:
                set_viewport_size(selenium, args.width, args.height)

                selenium.get("http://localhost:8000/admin/login/")
                submit_form(selenium, {"username": os.environ["USER"], "password": "p"})

                selenium.get("http://localhost:8000/admin/auth/user/")
                # Check if SQL Panel is already visible:
                sql_panel = find_including_toolbar(selenium, By.ID, "djdt-SQLPanel")
                if not sql_panel:
                    # Open the admin sidebar.
                    el = find_including_toolbar(selenium, By.ID, "djDebugToolbarHandle")
                    el.click()
                    sql_panel = find_including_toolbar(selenium, By.ID, "djdt-SQLPanel")
                # Open the SQL panel.
                sql_panel.click()

                selenium.save_screenshot(args.outfile)
        finally:
            p.send_signal(signal.SIGTERM)


if __name__ == "__main__":
    main()
