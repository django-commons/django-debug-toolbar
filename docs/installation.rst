Installation
============

Process
-------

Each of the following steps needs to be configured for the Debug Toolbar to be
fully functional.

.. warning::

    The Debug Toolbar now supports `Django's asynchronous views <https://docs.djangoproject.com/en/dev/topics/async/>`_ and ASGI environment, but
    still lacks the capability for handling concurrent requests.

1. Install the Package
^^^^^^^^^^^^^^^^^^^^^^

The recommended way to install the Debug Toolbar is via pip_:

.. code-block:: console

    $ python -m pip install django-debug-toolbar

If you aren't familiar with pip, you may also obtain a copy of the
``debug_toolbar`` directory and add it to your Python path.

.. _pip: https://pip.pypa.io/

To test an upcoming release, you can install the in-development version
instead with the following command:

.. code-block:: console

    $ python -m pip install -e git+https://github.com/django-commons/django-debug-toolbar.git#egg=django-debug-toolbar

If you're upgrading from a previous version, you should review the
:doc:`change log <changes>` and look for specific upgrade instructions.

2. Check for Prerequisites
^^^^^^^^^^^^^^^^^^^^^^^^^^

The Debug Toolbar requires two things from core Django. These are already
configured in Django’s default ``startproject`` template, so in most cases you
will already have these set up.

First, ensure that ``'django.contrib.staticfiles'`` is in your
``INSTALLED_APPS`` setting, and `configured properly
<https://docs.djangoproject.com/en/stable/howto/static-files/>`_:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "django.contrib.staticfiles",
        # ...
    ]

    STATIC_URL = "static/"

Second, ensure that your ``TEMPLATES`` setting contains a
``DjangoTemplates`` backend whose ``APP_DIRS`` options is set to ``True``:

.. code-block:: python

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
            # ...
        }
    ]

3. Install the App
^^^^^^^^^^^^^^^^^^

Add ``"debug_toolbar"`` to your ``INSTALLED_APPS`` setting:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "debug_toolbar",
        # ...
    ]
.. note:: Check  out the configuration example in the
   `example app
   <https://github.com/django-commons/django-debug-toolbar/tree/main/example>`_
   to learn how to set up the toolbar to function smoothly while running
   your tests.

4. Add the URLs
^^^^^^^^^^^^^^^

Add django-debug-toolbar's URLs to your project's URLconf:

.. code-block:: python

    from django.urls import include, path
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns = [
        # ... the rest of your URLconf goes here ...
    ] + debug_toolbar_urls()

By default this uses the ``__debug__`` prefix for the paths, but you can
use any prefix that doesn't clash with your application's URLs.


5. Add the Middleware
^^^^^^^^^^^^^^^^^^^^^

The Debug Toolbar is mostly implemented in a middleware. Add it to your
``MIDDLEWARE`` setting:

.. code-block:: python

    MIDDLEWARE = [
        # ...
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        # ...
    ]

.. warning::

    The order of ``MIDDLEWARE`` is important. You should include the Debug
    Toolbar middleware as early as possible in the list. However, it must come
    after any other middleware that encodes the response's content, such as
    :class:`~django.middleware.gzip.GZipMiddleware`.

.. _internal-ips:

6. Configure Internal IPs
^^^^^^^^^^^^^^^^^^^^^^^^^

The Debug Toolbar is shown only if your IP address is listed in Django’s
:setting:`INTERNAL_IPS` setting.  This means that for local
development, you *must* add ``"127.0.0.1"`` to :setting:`INTERNAL_IPS`.
You'll need to create this setting if it doesn't already exist in your
settings module:

.. code-block:: python

   INTERNAL_IPS = [
       # ...
       "127.0.0.1",
       # ...
   ]

You can change the logic of determining whether or not the Debug Toolbar
should be shown with the :ref:`SHOW_TOOLBAR_CALLBACK <SHOW_TOOLBAR_CALLBACK>`
option.

.. warning::

    If using Docker, the toolbar will attempt to look up your host name
    automatically and treat it as an allowable internal IP. If you're not
    able to get the toolbar to work with your docker installation, review
    the code in ``debug_toolbar.middleware.show_toolbar``.

7. Disable the toolbar when running tests (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you're running tests in your project you shouldn't activate the toolbar. You
can do this by adding another setting:

.. code-block:: python

    TESTING = "test" in sys.argv

    if not TESTING:
        INSTALLED_APPS = [
            *INSTALLED_APPS,
            "debug_toolbar",
        ]
        MIDDLEWARE = [
            "debug_toolbar.middleware.DebugToolbarMiddleware",
            *MIDDLEWARE,
        ]

You should also modify your URLconf file:

.. code-block:: python

    from django.conf import settings
    from debug_toolbar.toolbar import debug_toolbar_urls

    if not settings.TESTING:
        urlpatterns = [
            *urlpatterns,
        ] + debug_toolbar_urls()

Alternatively, you can check out the :ref:`IS_RUNNING_TESTS <IS_RUNNING_TESTS>`
option.

Troubleshooting
---------------

If the toolbar doesn't appear, check your browser's development console for
errors. These errors can often point to one of the issues discussed in the
section below. Note that the toolbar only shows up for pages with an HTML body
tag, which is absent in the templates of the Django Polls tutorial.

Incorrect MIME type for toolbar.js
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When this error occurs, the development console shows an error similar to:

.. code-block:: text

    Loading module from “http://127.0.0.1:8000/static/debug_toolbar/js/toolbar.js” was blocked because of a disallowed MIME type (“text/plain”).

On some platforms (commonly on Windows O.S.), the Django ``runserver``
command may use incorrect content types for static assets. To guess content
types, Django relies on the :mod:`mimetypes` module from the Python standard
library, which itself relies on the underlying platform's map files.

The easiest workaround is to add the following to your ``settings.py`` file.
This forces the MIME type for ``.js`` files:

.. code-block:: python

    import mimetypes
    mimetypes.add_type("application/javascript", ".js", True)

Alternatively, you can try to fix your O.S. configuration. If you find improper
content types for certain files, it is most likely that the platform's map
files are incorrect or need to be updated. This can be achieved, for example:

- On Red Hat distributions, install or update the ``mailcap`` package.
- On Debian distributions, install or update the ``mime-support`` package.
- On Windows O.S., edit the keys under ``HKEY_CLASSES_ROOT`` in the Windows
  registry.

Cross-Origin Request Blocked
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Debug Toolbar loads a `JavaScript module`_. Typical local development using
Django ``runserver`` is not impacted. However, if your application server and
static files server are at different origins, you may see `CORS errors`_ in
your browser's development console:

.. code-block:: text

    Cross-Origin Request Blocked: The Same Origin Policy disallows reading the remote resource at http://localhost/static/debug_toolbar/js/toolbar.js. (Reason: CORS header ‘Access-Control-Allow-Origin’ missing).

Or

.. code-block:: text

    Access to script at 'http://localhost/static/debug_toolbar/js/toolbar.js' from origin 'http://localhost:8000' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.

To resolve, configure your static files server to add the
`Access-Control-Allow-Origin header`_ with the origin of the application
server. For example, if your application server is at ``http://example.com``,
and your static files are served by NGINX, add:

.. code-block:: nginx

    add_header Access-Control-Allow-Origin http://example.com;

And for Apache:

.. code-block:: apache

    Header add Access-Control-Allow-Origin http://example.com

.. _JavaScript module: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules
.. _CORS errors: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS/Errors/CORSMissingAllowOrigin
.. _Access-Control-Allow-Origin header: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Origin

Django Channels & Async
^^^^^^^^^^^^^^^^^^^^^^^

The Debug Toolbar currently has experimental support for Django Channels and
async projects. The Debug Toolbar is compatible with the following exceptions:

- Concurrent requests aren't supported
- ``TimerPanel``, ``RequestPanel`` and ``ProfilingPanel`` can't be used
  in async contexts.

HTMX
^^^^

If you're using `HTMX`_ to `boost a page`_ you will need to add the following
event handler to your code:

.. code-block:: javascript

    {% if debug %}
        if (typeof window.htmx !== "undefined") {
            htmx.on("htmx:afterSettle", function(detail) {
                if (
                    typeof window.djdt !== "undefined"
                    && detail.target instanceof HTMLBodyElement
                ) {
                    djdt.show_toolbar();
                }
            });
        }
    {% endif %}


The use of ``{% if debug %}`` requires
`django.template.context_processors.debug`_ be included in the
``'context_processors'`` option of the `TEMPLATES`_ setting. Django's
default configuration includes this context processor.


.. _HTMX: https://htmx.org/
.. _boost a page: https://htmx.org/docs/#boosting
.. _django.template.context_processors.debug: https://docs.djangoproject.com/en/4.1/ref/templates/api/#django-template-context-processors-debug
.. _TEMPLATES: https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-TEMPLATES
