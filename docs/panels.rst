Panels
======

The Django Debug Toolbar ships with a series of built-in panels. In addition,
several third-party panels are available.

Default built-in panels
-----------------------

The following panels are enabled by default.

History
~~~~~~~

.. class:: debug_toolbar.panels.history.HistoryPanel

This panel shows the history of requests made and allows switching to a past
snapshot of the toolbar to view that request's stats.

.. caution::
   If :ref:`RENDER_PANELS <RENDER_PANELS>` configuration option is set to
   ``True`` or if the server runs with multiple processes, the History Panel
   will be disabled.

Versions
~~~~~~~~

.. class:: debug_toolbar.panels.versions.VersionsPanel

Shows versions of Python, Django, and installed apps if possible.

Timer
~~~~~

.. class:: debug_toolbar.panels.timer.TimerPanel

Request timer.

Settings
~~~~~~~~

.. class:: debug_toolbar.panels.settings.SettingsPanel

A list of settings in settings.py.

Headers
~~~~~~~

.. class:: debug_toolbar.panels.headers.HeadersPanel

This panels shows the HTTP request and response headers, as well as a
selection of values from the WSGI environment.

Note that headers set by middleware placed before the debug toolbar middleware
in ``MIDDLEWARE`` won't be visible in the panel. The WSGI server itself may
also add response headers such as ``Date`` and ``Server``.

Request
~~~~~~~

.. class:: debug_toolbar.panels.request.RequestPanel

GET/POST/cookie/session variable display.

SQL
~~~

.. class:: debug_toolbar.panels.sql.SQLPanel

SQL queries including time to execute and links to EXPLAIN each query.

Static files
~~~~~~~~~~~~

.. class:: debug_toolbar.panels.staticfiles.StaticFilesPanel

Used static files and their locations (via the ``staticfiles`` finders).

Templates
~~~~~~~~~

.. class:: debug_toolbar.panels.templates.TemplatesPanel

Templates and context used, and their template paths.

Alerts
~~~~~~~

.. class:: debug_toolbar.panels.alerts.AlertsPanel

This panel shows alerts for a set of pre-defined cases:

- Alerts when the response has a form without the
  ``enctype="multipart/form-data"`` attribute and the form contains
  a file input.

Cache
~~~~~

.. class:: debug_toolbar.panels.cache.CachePanel

Cache queries. Is incompatible with Django's per-site caching.

Signals
~~~~~~~

.. class:: debug_toolbar.panels.signals.SignalsPanel

List of signals and receivers.

Community
~~~~~~~~~

.. class:: debug_toolbar.panels.community.CommunityPanel

A panel that provides links to the Django Debug Toolbar community.

Redirects
~~~~~~~~~

.. class:: debug_toolbar.panels.redirects.RedirectsPanel

.. deprecated:: 6.0

The RedirectsPanel is deprecated and will be removed in a future version.
The HistoryPanel now provides the ability to view toolbar data for redirected
requests. If you have a use case for this panel, please comment on the
GitHub issue <https://github.com/django-commons/django-debug-toolbar/issues/2216>`_.

When this panel is enabled, the debug toolbar will show an intermediate page
upon redirect so you can view any debug information prior to redirecting. This
page will provide a link to the redirect destination you can follow when
ready.

Since this behavior is annoying when you aren't debugging a redirect, this
panel is included but inactive by default. You can activate it by default with
the ``DISABLE_PANELS`` configuration option.

To further customize the behavior, you can subclass the ``RedirectsPanel``
and override the ``get_interception_response`` method to manipulate the
response directly. To use a custom ``RedirectsPanel``, you need to replace
the original one in ``DEBUG_TOOLBAR_PANELS`` in your ``settings.py``.

.. _profiling-panel:

Profiling
~~~~~~~~~

.. class:: debug_toolbar.panels.profiling.ProfilingPanel

Profiling information for the processing of the request.

This panel is included but inactive by default. You can activate it by default
with the ``DISABLE_PANELS`` configuration option.

For version of Python 3.12 and later you need to use
``python -m manage runserver --nothreading``
Concurrent requests don't work with the profiling panel.

The panel will include all function calls made by your project if you're using
the setting ``settings.BASE_DIR`` to point to your project's root directory.
If a function is in a file within that directory and does not include
``"/site-packages/"`` or ``"/dist-packages/"`` in the path, it will be
included.

Third-party panels
------------------

.. note:: Third-party panels aren't officially supported!

    The authors of the Django Debug Toolbar maintain a list of third-party
    panels, but they can't vouch for the quality of each of them. Please
    report bugs to their authors.

If you'd like to add a panel to this list, please submit a pull request!

Flame Graphs
~~~~~~~~~~~~

URL: https://gitlab.com/living180/pyflame

Path: ``pyflame.djdt.panel.FlamegraphPanel``

Displays a flame graph for visualizing the performance profile of the request,
using Brendan Gregg's `flamegraph.pl script
<https://github.com/brendangregg/FlameGraph/flamegraph.pl>`_ to perform the
heavy lifting.

LDAP Tracing
~~~~~~~~~~~~

URL: https://github.com/danyi1212/django-windowsauth

Path: ``windows_auth.panels.LDAPPanel``

LDAP Operations performed during the request, including timing, request and response messages,
the entries received, write changes list, stack-tracing and error debugging.
This panel also shows connection usage metrics when it is collected.
`Check out the docs <https://django-windowsauth.readthedocs.io/en/latest/howto/debug_toolbar.html>`_.

Line Profiler
~~~~~~~~~~~~~

URL: https://github.com/mikekeda/django-debug-toolbar-line-profiler

Path: ``debug_toolbar_line_profiler.panel.ProfilingPanel``

This package provides a profiling panel that incorporates output from
line_profiler_.

.. _line_profiler: https://github.com/rkern/line_profiler

Mail
~~~~~~~~

URL: https://github.com/scuml/django-mail-panel

Path: ``mail_panel.panels.MailToolbarPanel``

This panel captures and displays emails sent from your application.

Memcache
~~~~~~~~

URL: https://github.com/ross/memcache-debug-panel

Path: ``memcache_toolbar.panels.memcache.MemcachePanel`` or
``memcache_toolbar.panels.pylibmc.PylibmcPanel``

This panel tracks memcached usage. It currently supports both the pylibmc and
memcache libraries.

MongoDB
~~~~~~~

URL: https://github.com/hmarr/django-debug-toolbar-mongo

Path: ``debug_toolbar_mongo.panel.MongoDebugPanel``

Adds MongoDB debugging information.

MrBenn Toolbar Plugin
~~~~~~~~~~~~~~~~~~~~~

URL: https://github.com/andytwoods/mrbenn

Path: ``mrbenn_panel.panel.MrBennPanel``

Allows you to quickly open template files and views directly in your IDE!
In addition to the path above, you need to add ``mrbenn_panel`` in
``INSTALLED_APPS``

Neo4j
~~~~~

URL: https://github.com/robinedwards/django-debug-toolbar-neo4j-panel

Path: ``neo4j_panel.Neo4jPanel``

Trace neo4j rest API calls in your Django application, this also works for
neo4django and neo4jrestclient, support for py2neo is on its way.

Pympler
~~~~~~~

URL: https://pythonhosted.org/Pympler/django.html

Path: ``pympler.panels.MemoryPanel``

Shows process memory information (virtual size, resident set size) and model
instances for the current request.

Request History
~~~~~~~~~~~~~~~

URL: https://github.com/djsutho/django-debug-toolbar-request-history

Path: ``ddt_request_history.panels.request_history.RequestHistoryPanel``

Switch between requests to view their stats. Also adds support for viewing
stats for AJAX requests.

Requests
~~~~~~~~

URL: https://github.com/marceltschoppch/django-requests-debug-toolbar

Path: ``requests_panel.panel.RequestsDebugPanel``

Lists HTTP requests made with the popular `requests <https://requests.readthedocs.io/>`_ library.

Template Profiler
~~~~~~~~~~~~~~~~~

URL: https://github.com/node13h/django-debug-toolbar-template-profiler

Path: ``template_profiler_panel.panels.template.TemplateProfilerPanel``

Shows template render call duration and distribution on the timeline.
Lightweight. Compatible with WSGI servers which reuse threads for multiple
requests (Werkzeug).

Template Timings
~~~~~~~~~~~~~~~~

URL: https://github.com/orf/django-debug-toolbar-template-timings

Path: ``template_timings_panel.panels.TemplateTimings.TemplateTimings``

Displays template rendering times for your Django application.

VCS Info
~~~~~~~~

URL: https://github.com/giginet/django-debug-toolbar-vcs-info

Path: ``vcs_info_panel.panels.GitInfoPanel``

Displays VCS status (revision, branch, latest commit log and more) of your
Django application.

uWSGI Stats
~~~~~~~~~~~

URL: https://github.com/unbit/django-uwsgi

Path: ``django_uwsgi.panels.UwsgiPanel``

Displays uWSGI stats (workers, applications, spooler jobs and more).

API for third-party panels
--------------------------

Third-party panels must subclass :class:`~debug_toolbar.panels.Panel`,
according to the public API described below. Unless noted otherwise, all
methods are optional.

Panels can ship their own templates, static files and views.

Any views defined for the third-party panel use the following decorators:

- ``debug_toolbar.decorators.require_show_toolbar`` - Prevents unauthorized
  access to the view. This decorator is compatible with async views.
- ``debug_toolbar.decorators.render_with_toolbar_language`` - Supports
  internationalization for any content rendered by the view. This will render
  the response with the :ref:`TOOLBAR_LANGUAGE <TOOLBAR_LANGUAGE>` rather than
  :setting:`LANGUAGE_CODE`.

There is no public CSS API at this time.

.. autoclass:: debug_toolbar.panels.Panel

    .. autoattribute:: debug_toolbar.panels.Panel.nav_title

    .. autoattribute:: debug_toolbar.panels.Panel.nav_subtitle

    .. autoattribute:: debug_toolbar.panels.Panel.has_content

    .. autoattribute:: debug_toolbar.panels.Panel.title

    .. autoattribute:: debug_toolbar.panels.Panel.template

    .. autoattribute:: debug_toolbar.panels.Panel.content

    .. autoattribute:: debug_toolbar.panels.Panel.scripts

    .. automethod:: debug_toolbar.panels.Panel.ready

    .. automethod:: debug_toolbar.panels.Panel.get_urls

    .. automethod:: debug_toolbar.panels.Panel.enable_instrumentation

    .. automethod:: debug_toolbar.panels.Panel.disable_instrumentation

    .. automethod:: debug_toolbar.panels.Panel.record_stats

    .. automethod:: debug_toolbar.panels.Panel.get_stats

    .. automethod:: debug_toolbar.panels.Panel.process_request

    .. automethod:: debug_toolbar.panels.Panel.generate_server_timing

    .. automethod:: debug_toolbar.panels.Panel.generate_stats

    .. automethod:: debug_toolbar.panels.Panel.get_headers

    .. automethod:: debug_toolbar.panels.Panel.run_checks

.. autoclass:: debug_toolbar._stubs.GetResponse

.. _javascript-api:

JavaScript API
~~~~~~~~~~~~~~

Panel templates should include any JavaScript files they need. There are a few
common methods available.

.. js:function:: djdt.close

    Closes the topmost level (window/panel/toolbar)

.. js:function:: djdt.cookie.get(key)

    This is a helper function to fetch values stored in the cookies.

    :param key: The key for the value to be fetched.

.. js:function:: djdt.cookie.set(key, value, options)

    This is a helper function to set a value stored in the cookies.

    :param key: The key to be used.

    :param value: The value to be set.

    :param options: The options for the value to be set. It should contain the
        properties ``expires`` and ``path``. The properties ``domain``,
        ``secure`` and ``samesite`` are also supported. ``samesite`` defaults
        to ``lax`` if not provided.

.. js:function:: djdt.hide_toolbar

    Closes any panels and hides the toolbar.

.. js:function:: djdt.show_toolbar

    Shows the toolbar. This can be used to re-render the toolbar when reloading the
    entire DOM. For example, then using `HTMX's boosting`_.

.. _HTMX's boosting: https://htmx.org/docs/#boosting

Events
^^^^^^

.. js:attribute:: djdt.panel.render

    This is an event raised when a panel is rendered. It has the property
    ``detail.panelId`` which identifies which panel has been loaded. This
    event can be useful when creating custom scripts to process the HTML
    further.

    An example of this for the ``CustomPanel`` would be:

.. code-block:: javascript

    import { $$, getDebugElement } from "./utils.js";
    function addCustomMetrics() {
        // Logic to process/add custom metrics here.

        // Be sure to cover the case of this function being called twice
        // due to file being loaded asynchronously.
    }
    const djDebug = getDebugElement();
    $$.onPanelRender(djDebug, "CustomPanel", addCustomMetrics);
    // Since a panel's scripts are loaded asynchronously, it's possible that
    // the above statement would occur after the djdt.panel.render event has
    // been raised. To account for that, the rendering function should be
    // called here as well.
    addCustomMetrics();
