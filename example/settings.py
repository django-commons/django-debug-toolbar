"""Django settings for example project."""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production


SECRET_KEY = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

DEBUG = True

INTERNAL_IPS = ["127.0.0.1", "::1"]

# Application definition

INSTALLED_APPS = [
    *(["daphne"] if os.getenv("ASYNC_SERVER", False) else []),  # noqa: FBT003
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "example.urls"

STATIC_URL = "/static/"

TEMPLATES = [
    {
        "NAME": "jinja2",
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "APP_DIRS": True,
        "DIRS": [os.path.join(BASE_DIR, "example", "templates", "jinja2")],
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [os.path.join(BASE_DIR, "example", "templates")],
        "OPTIONS": {
            "debug": True,
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

USE_TZ = True

WSGI_APPLICATION = "example.wsgi.application"
ASGI_APPLICATION = "example.asgi.application"

# Cache and database

CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "example", "db.sqlite3"),
    }
}

# To use another database, set the DB_BACKEND environment variable.
if os.environ.get("DB_BACKEND", "").lower() == "postgresql":
    # See docs/contributing for instructions on configuring PostgreSQL.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "debug_toolbar",
            "USER": "debug_toolbar",
            "PASSWORD": "debug_toolbar",
        }
    }
if os.environ.get("DB_BACKEND", "").lower() == "mysql":
    # See docs/contributing for instructions on configuring MySQL/MariaDB.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "debug_toolbar",
            "USER": "debug_toolbar",
            "PASSWORD": "debug_toolbar",
        }
    }

STATICFILES_DIRS = [os.path.join(BASE_DIR, "example", "static")]

# Only enable the toolbar when we're in debug mode and we're
# not running tests. Django will change DEBUG to be False for
# tests, so we can't rely on DEBUG alone.
ENABLE_DEBUG_TOOLBAR = DEBUG and "test" not in sys.argv
if ENABLE_DEBUG_TOOLBAR:
    INSTALLED_APPS += [
        "debug_toolbar",
    ]
    MIDDLEWARE += [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]
    # Customize the config to support turbo and htmx boosting.
    DEBUG_TOOLBAR_CONFIG = {"ROOT_TAG_EXTRA_ATTRS": "data-turbo-permanent hx-preserve"}
