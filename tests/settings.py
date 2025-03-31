"""Django settings for tests."""

import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production

DEBUG = False
SECRET_KEY = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

INTERNAL_IPS = ["127.0.0.1"]

LOGGING = {  # avoids spurious output in tests
    "version": 1,
    "disable_existing_loggers": True,
}


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "debug_toolbar",
    "tests",
]


USE_GIS = os.getenv("DB_BACKEND") == "postgis"

if USE_GIS:
    INSTALLED_APPS = ["django.contrib.gis"] + INSTALLED_APPS

MEDIA_URL = "/media/"  # Avoids https://code.djangoproject.com/ticket/21451

MIDDLEWARE = [
    "tests.middleware.UseCacheAfterToolbar",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tests.urls"

TEMPLATES = [
    {
        "NAME": "jinja2",
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "APP_DIRS": True,
        "DIRS": [os.path.join(BASE_DIR, "tests", "templates", "jinja2")],
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    },
]

USE_TZ = True

STATIC_ROOT = os.path.join(BASE_DIR, "tests", "static")

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "tests", "additional_static"),
    ("prefix", os.path.join(BASE_DIR, "tests", "additional_static")),
]

# Cache and database

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "second": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}

DATABASES = {
    "default": {
        "ENGINE": "django.{}db.backends.{}".format(
            "contrib.gis." if USE_GIS else "", os.getenv("DB_BACKEND", "sqlite3")
        ),
        "NAME": os.getenv("DB_NAME", ":memory:"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
        "TEST": {
            "USER": "default_test",
        },
    },
    "replica": {
        "ENGINE": "django.{}db.backends.{}".format(
            "contrib.gis." if USE_GIS else "", os.getenv("DB_BACKEND", "sqlite3")
        ),
        "NAME": os.getenv("DB_NAME", ":memory:"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
        "TEST": {
            "USER": "default_test",
            "MIRROR": "default",
        },
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Debug Toolbar configuration

DEBUG_TOOLBAR_CONFIG = {
    # Django's test client sets wsgi.multiprocess to True inappropriately
    "RENDER_PANELS": False,
    # IS_RUNNING_TESTS must be False even though we're running tests because we're running the toolbar's own tests.
    "IS_RUNNING_TESTS": False,
}
