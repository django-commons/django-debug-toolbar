Configuration
=============

The debug toolbar provides two settings that you can add in your project's
settings module to customize its behavior.

.. note:: Do you really need a customized configuration?

    The debug toolbar ships with a default configuration that is considered
    sane for the vast majority of Django projects. Don't copy-paste blindly
    the default values shown below into your settings module! It's useless and
    it'll prevent you from taking advantage of better defaults that may be
    introduced in future releases.

DEBUG_TOOLBAR_PANELS
--------------------

This setting specifies the full Python path to each panel that you want
included in the toolbar. It works like Django's ``MIDDLEWARE`` setting. The
default value is::

    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.history.HistoryPanel',
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.alerts.AlertsPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.community.CommunityPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'debug_toolbar.panels.profiling.ProfilingPanel',
    ]

This setting allows you to:

* add built-in panels that aren't enabled by default,
* add third-party panels,
* remove built-in panels,
* change the order of panels.

DEBUG_TOOLBAR_CONFIG
--------------------

This dictionary contains all other configuration options. Some apply to the
toolbar itself, others are specific to some panels.

Toolbar options
~~~~~~~~~~~~~~~

* ``DISABLE_PANELS``

  Default:

  .. code-block:: python

      {
          "debug_toolbar.panels.profiling.ProfilingPanel",
          "debug_toolbar.panels.redirects.RedirectsPanel",
      }

  This setting is a set of the full Python paths to each panel that you
  want disabled (but still displayed) by default.

* ``INSERT_BEFORE``

  Default: ``'</body>'``

  The toolbar searches for this string in the HTML and inserts itself just
  before.

.. _IS_RUNNING_TESTS:

* ``IS_RUNNING_TESTS``

  Default: ``"test" in sys.argv or "PYTEST_VERSION" in os.environ``

  This setting whether the application is running tests. If this resolves to
  ``True``, the toolbar will prevent you from running tests. This should only
  be changed if your test command doesn't include ``test`` or if you wish to
  test your application with the toolbar configured. If you do wish to test
  your application with the toolbar configured, set this setting to
  ``False``.

.. _RENDER_PANELS:

* ``RENDER_PANELS``

  Default: ``None``

  If set to ``False``, the debug toolbar will keep the contents of panels in
  memory on the server and load them on demand.

  If set to ``True``, it will disable ``HistoryPanel`` and render panels
  inside every page. This may slow down page rendering but it's
  required on multi-process servers, for example if you deploy the toolbar in
  production (which isn't recommended).

  The default value of ``None`` tells the toolbar to automatically do the
  right thing depending on whether the WSGI container runs multiple processes.
  This setting allows you to force a different behavior if needed. If the
  WSGI container runs multiple processes, it will disable ``HistoryPanel``.

* ``RESULTS_CACHE_SIZE``

  Default: ``25``

  The toolbar keeps up to this many results in memory or persistent storage.


.. _ROOT_TAG_EXTRA_ATTRS:

* ``ROOT_TAG_EXTRA_ATTRS``

  Default: ``''``

  This setting is injected in the root template div in order to avoid
  conflicts with client-side frameworks. For example, when using the debug
  toolbar with Angular.js, set this to ``'ng-non-bindable'`` or
  ``'class="ng-non-bindable"'``.

* ``SHOW_COLLAPSED``

  Default: ``False``

  If changed to ``True``, the toolbar will be collapsed by default.

.. _SHOW_TOOLBAR_CALLBACK:

* ``SHOW_TOOLBAR_CALLBACK``

  Default: ``'debug_toolbar.middleware.show_toolbar'``

  This is the dotted path to a function used for determining whether the
  toolbar should show or not. The default checks are that ``DEBUG`` must be set
  to ``True`` and the IP of the request must be in ``INTERNAL_IPS``. You can
  provide your own function ``callback(request)`` which returns ``True`` or
  ``False``.

  For versions < 1.8, the callback should also return ``False`` for AJAX
  requests. Since version 1.8, AJAX requests are checked in the middleware, not
  the callback. This allows reusing the callback to verify access to panel
  views requested via AJAX.

  .. warning::

     Please note that the debug toolbar isn't hardened for use in production
     environments or on public servers. You should be aware of the implications
     to the security of your servers when using your own callback. One known
     implication is that it is possible to execute arbitrary SQL through the
     SQL panel when the ``SECRET_KEY`` value is leaked somehow.

  .. warning::

     Do not use
     ``DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG}``
     in your project's settings.py file. The toolbar expects to use
     ``django.conf.settings.DEBUG``. Using your project's setting's ``DEBUG``
     is likely to cause unexpected results when running your tests. This is because
     Django automatically sets ``settings.DEBUG = False``, but your project's
     setting's ``DEBUG`` will still be set to ``True``.

.. _OBSERVE_REQUEST_CALLBACK:

* ``OBSERVE_REQUEST_CALLBACK``

  Default: ``'debug_toolbar.toolbar.observe_request'``

  .. note::

     This setting is deprecated in favor of the ``UPDATE_ON_FETCH`` and
     ``SHOW_TOOLBAR_CALLBACK`` settings.

  This is the dotted path to a function used for determining whether the
  toolbar should update on AJAX requests or not. The default implementation
  always returns ``True``.

.. _TOOLBAR_STORE_CLASS:

* ``TOOLBAR_STORE_CLASS``

  Default: ``"debug_toolbar.store.MemoryStore"``

  The path to the class to be used for storing the toolbar's data per request.

  Available store classes:

  * ``debug_toolbar.store.MemoryStore`` - Stores data in memory
  * ``debug_toolbar.store.DatabaseStore`` - Stores data in the database

  The DatabaseStore provides persistence and automatically cleans up old
  entries based on the ``RESULTS_CACHE_SIZE`` setting.

  Note: When using ``DatabaseStore`` migrations are required for
  the ``debug_toolbar`` app:

  .. code-block:: bash

      python manage.py migrate debug_toolbar

  For the ``DatabaseStore`` to work properly, you need to run migrations for the
  ``debug_toolbar`` app. The migrations create the necessary database table to store
  toolbar data.

.. _TOOLBAR_LANGUAGE:

* ``TOOLBAR_LANGUAGE``

  Default: ``None``

  The language used to render the toolbar. If no value is supplied, then the
  application's current language will be used. This setting can be used to
  render the toolbar in a different language than what the application is
  rendered in. For example, if you wish to use English for development,
  but want to render your application in French, you would set this to
  ``"en-us"`` and :setting:`LANGUAGE_CODE` to ``"fr"``.

.. _UPDATE_ON_FETCH:

* ``UPDATE_ON_FETCH``

  Default: ``False``

  This controls whether the toolbar should update to the latest AJAX
  request when it occurs. This is especially useful when using htmx
  boosting or similar JavaScript techniques.


Panel options
~~~~~~~~~~~~~

* ``EXTRA_SIGNALS``

  Default: ``[]``

  Panel: signals

  A list of custom signals that might be in your project, defined as the
  Python path to the signal.

* ``ENABLE_STACKTRACES``

  Default: ``True``

  Panels: cache, SQL

  If set to ``True``, this will show stacktraces for SQL queries and cache
  calls. Enabling stacktraces can increase the CPU time used when executing
  queries.

* ``ENABLE_STACKTRACES_LOCALS``

  Default: ``False``

  Panels: cache, SQL

  If set to ``True``, this will show locals() for each stacktrace piece of
  code for SQL queries and cache calls.
  Enabling stacktraces locals will increase the CPU time used when executing
  queries and will give too verbose information in most cases, but is useful
  for debugging complex cases.

.. caution::
   This will expose all members from each frame of the stacktrace. This can
   potentially expose sensitive or private information. It's advised to only
   use this configuration locally.

* ``HIDE_IN_STACKTRACES``

  Default::

    (
        "socketserver",
        "threading",
        "wsgiref",
        "debug_toolbar",
        "django.db",
        "django.core.handlers",
        "django.core.servers",
        "django.utils.decorators",
        "django.utils.deprecation",
        "django.utils.functional",
    )


  Panels: cache, SQL

  Useful for eliminating server-related entries which can result
  in enormous DOM structures and toolbar rendering delays.

* ``PRETTIFY_SQL``

  Default: ``True``

  Panel: SQL

  Controls SQL token grouping.

  Token grouping allows pretty print of similar tokens,
  like aligned indentation for every selected field.

  When set to ``True``, it might cause render slowdowns
  when a view make long SQL textual queries.

  **Without grouping**::

    SELECT
        "auth_user"."id", "auth_user"."password", "auth_user"."last_login",
        "auth_user"."is_superuser", "auth_user"."username", "auth_user"."first_name",
        "auth_user"."last_name"
    FROM "auth_user"
    WHERE "auth_user"."username" = '''test_username'''
    LIMIT 21

  **With grouping**::

    SELECT "auth_user"."id",
       "auth_user"."password",
       "auth_user"."last_login",
       "auth_user"."is_superuser",
       "auth_user"."username",
       "auth_user"."first_name",
       "auth_user"."last_name",
      FROM "auth_user"
    WHERE "auth_user"."username" = '''test_username'''
    LIMIT 21

* ``PROFILER_CAPTURE_PROJECT_CODE``

  Default: ``True``

  Panel: profiling

  When enabled this setting will include all project function calls in the
  panel. Project code is defined as files in the path defined at
  ``settings.BASE_DIR``. If you install dependencies under
  ``settings.BASE_DIR`` in a directory other than ``sites-packages`` or
  ``dist-packages`` you may need to disable this setting.

* ``PROFILER_MAX_DEPTH``

  Default: ``10``

  Panel: profiling

  This setting affects the depth of function calls in the profiler's
  analysis.

* ``PROFILER_THRESHOLD_RATIO``

  Default: ``8``

  Panel: profiling

  This setting affects the which calls are included in the profile. A higher
  value will include more function calls. A lower value will result in a faster
  render of the profiling panel, but will exclude data.

  This value is used to determine the threshold of cumulative time to include
  the nested functions. The threshold is calculated by the root calls'
  cumulative time divided by this ratio.

* ``SHOW_TEMPLATE_CONTEXT``

  Default: ``True``

  Panel: templates

  If set to ``True`` then a template's context will be included with it in the
  template debug panel. Turning this off is useful when you have large
  template contexts, or you have template contexts with lazy data structures
  that you don't want to be evaluated.

* ``SKIP_TEMPLATE_PREFIXES``

  Default: ``('django/forms/widgets/', 'admin/widgets/')``

  Panel: templates.

  Templates starting with those strings are skipped when collecting
  rendered templates and contexts. Template-based form widgets are
  skipped by default because the panel HTML can easily grow to hundreds
  of megabytes with many form fields and many options.

* ``SKIP_TOOLBAR_QUERIES``

  Default: ``True``

  Panel: SQL

  The debug toolbar can generate queries if ``TOOLBAR_STORE_CLASS`` is set to
  use ``DatabaseStore``. This setting controls whether those queries are
  tracked in the ``SQLPanel``. Set this to ``False`` to see the debug
  toolbar's queries.

* ``SQL_WARNING_THRESHOLD``

  Default: ``500``

  Panel: SQL

  The SQL panel highlights queries that took more that this amount of time,
  in milliseconds, to execute.

Here's what a slightly customized toolbar configuration might look like::

    # This example is unlikely to be appropriate for your project.
    DEBUG_TOOLBAR_CONFIG = {
        # Toolbar options
        'RESULTS_CACHE_SIZE': 3,
        'SHOW_COLLAPSED': True,
        # Panel options
        'SQL_WARNING_THRESHOLD': 100,   # milliseconds
    }

Here's an example of using a persistent store to keep debug data between server
restarts::

    DEBUG_TOOLBAR_CONFIG = {
        'TOOLBAR_STORE_CLASS': 'debug_toolbar.store.DatabaseStore',
        'RESULTS_CACHE_SIZE': 100,  # Store up to 100 requests
    }

Theming support
---------------
The debug toolbar uses CSS variables to define fonts and colors. This allows
changing fonts and colors without having to override many individual CSS rules.
For example, if you preferred Roboto instead of the default list of fonts you
could add a **debug_toolbar/base.html** template override to your project:

.. code-block:: django

    {% extends 'debug_toolbar/base.html' %}

    {% block css %}{{ block.super }}
    <style>
        :host {
            --djdt-font-family-primary: 'Roboto', sans-serif;
        }
    </style>
    {% endblock %}

The list of CSS variables are defined at
`debug_toolbar/static/debug_toolbar/css/toolbar.css
<https://github.com/django-commons/django-debug-toolbar/blob/main/debug_toolbar/static/debug_toolbar/css/toolbar.css>`_
