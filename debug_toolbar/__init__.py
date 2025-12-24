__all__ = ["APP_NAME", "VERSION"]

APP_NAME = "djdt"

# Do not use pkg_resources to find the version but set it here directly!
# see issue #1446
VERSION = "6.1.0"

# Code that discovers files or modules in INSTALLED_APPS imports this module.
urls = "debug_toolbar.urls", APP_NAME
