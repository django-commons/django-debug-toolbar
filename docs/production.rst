Installing in production
=========================

.. _production-usage:

It's common to want to install the Django Debug Toolbar in an environment
that also serves production (or production-like) traffic, and rely on
:ref:`SHOW_TOOLBAR_CALLBACK <SHOW_TOOLBAR_CALLBACK>` (or ``DEBUG``) to
decide, per request, whether the toolbar is actually shown. This page
documents what actually happens when the toolbar is installed but not
shown, so you can make an informed decision about whether that's safe
for your deployment.

.. important::

   ``SHOW_TOOLBAR_CALLBACK`` only controls whether the toolbar is *rendered
   and populated* for a given request. It does **not** prevent every panel
   from touching global state at process start time. Some panels install
   their instrumentation (which sometimes means monkey-patching Django or
   third-party code) as soon as the ``debug_toolbar`` app is loaded,
   regardless of ``SHOW_TOOLBAR_CALLBACK``, ``DISABLE_PANELS``, or whether
   any request ever triggers the toolbar. The only way to avoid that
   instrumentation entirely is to remove the panel from
   ``DEBUG_TOOLBAR_PANELS`` so its module is never imported.

How instrumentation is set up
------------------------------

Each panel can hook into three different points in its lifecycle:

* :meth:`~debug_toolbar.panels.Panel.ready`, a classmethod called once for
  every panel listed in ``DEBUG_TOOLBAR_PANELS``, when the
  ``debug_toolbar`` app is loaded (i.e. at process/interpreter start,
  regardless of ``DEBUG``, ``SHOW_TOOLBAR_CALLBACK``, or ``DISABLE_PANELS``).
* Module import side effects. A few panels install patches directly at the
  top of their module, outside of any method. Because
  ``DebugToolbar.get_panel_classes()``
  imports every panel listed in ``DEBUG_TOOLBAR_PANELS`` while
  building the panel list, these patches run at the same time as ``ready()``
  and are just as unconditional.
* :meth:`~debug_toolbar.panels.Panel.enable_instrumentation` /
  :meth:`~debug_toolbar.panels.Panel.disable_instrumentation`, called by
  ``debug_toolbar.middleware.DebugToolbarMiddleware`` at the start and
  end of a request, but **only** when ``SHOW_TOOLBAR_CALLBACK`` returns
  ``True`` for that request *and* the panel itself is enabled (i.e. not
  listed in ``DISABLE_PANELS`` and not turned off via the panel's cookie).

``DISABLE_PANELS`` stops a panel from being included in
``toolbar.enabled_panels``, which means its ``enable_instrumentation()`` and
``disable_instrumentation()`` are never called. It has no effect on
``ready()`` or on import-time patches: those already ran once for every
panel in ``DEBUG_TOOLBAR_PANELS`` before any request was processed.

Audit summary
--------------

The table below summarizes, for each built-in panel, when its
instrumentation is installed, whether it can be disabled entirely (i.e.
avoided without removing the panel from ``DEBUG_TOOLBAR_PANELS``), and
whether it monkey-patches anything.

.. list-table::
   :header-rows: 1
   :widths: 18 42 20 20

   * - Panel
     - When instrumentation is installed
     - Fully avoidable without removing from ``DEBUG_TOOLBAR_PANELS``?
     - Monkey-patches?

   * - :class:`~debug_toolbar.panels.cache.CachePanel`
     - ``ready()`` permanently wraps
       ``CacheHandler.create_connection`` at startup so that any cache
       connection opened while a request is being instrumented gets
       wrapped too. ``enable_instrumentation()`` then wraps the methods
       (``get``, ``set``, ``delete``, etc.) of every already-open cache
       connection, per request.
     - No. The ``create_connection`` wrap installed by ``ready()`` is
       permanent for the life of the process.
     - Yes. Wraps ``CacheHandler.create_connection`` and the individual
       cache backend methods listed in ``CachePanel.WRAPPED_CACHE_METHODS``.

   * - :class:`~debug_toolbar.panels.sql.SQLPanel`
     - Only in ``enable_instrumentation()``, called per request.
       There is no ``ready()`` hook.
     - Yes. With no request enabling the panel, nothing is patched.
     - Yes, but only while active. Wraps ``connection.cursor()`` and
       ``connection.chunked_cursor()`` for each open database connection
       for the duration of the request.

   * - :class:`~debug_toolbar.panels.templates.TemplatesPanel`
     - At **import time** (module-level code, not even ``ready()``).
       ``Template._render`` and ``RequestContext.bind_template`` are
       replaced as soon as the module is imported, and the Jinja2
       ``Template.render`` method is patched too if ``jinja2`` is
       installed. ``enable_instrumentation()`` only connects the
       ``template_rendered`` signal receiver per request.
     - No. Because the patch is a side effect of importing the module,
       it happens as soon as ``TemplatesPanel`` is loaded from
       ``DEBUG_TOOLBAR_PANELS``.
     - Yes. Patches ``django.template.base.Template._render``,
       ``django.template.context.RequestContext.bind_template``, and
       (conditionally) ``django.template.backends.jinja2.Template.render``.

   * - :class:`~debug_toolbar.panels.staticfiles.StaticFilesPanel`
     - ``ready()`` permanently mixes an ``URLMixin`` class into
       ``staticfiles_storage.__class__.__bases__`` at startup.
       ``enable_instrumentation()`` connects a signal receiver and sets a
       ``contextvar`` per request.
     - No. The storage class hierarchy is changed once, at startup, and
       is not reverted.
     - Yes. Mutates the ``__bases__`` of the configured staticfiles
       storage class.

   * - :class:`~debug_toolbar.panels.profiling.ProfilingPanel`
     - Only in ``process_request()``, and only when the panel is enabled
       for the current request. There is no ``ready()`` hook.
     - Yes.
     - No.

   * - :class:`~debug_toolbar.panels.redirects.RedirectsPanel`
     - Only in ``process_request()``/``aprocess_request()``, and only
       when the panel is enabled for the current request.
     - Yes.
     - No.

   * - :class:`~debug_toolbar.panels.history.HistoryPanel`
     - No instrumentation; reads data already collected by other panels.
     - Yes.
     - No.

   * - :class:`~debug_toolbar.panels.versions.VersionsPanel`
     - No instrumentation.
     - Yes.
     - No.

   * - :class:`~debug_toolbar.panels.timer.TimerPanel`
     - No instrumentation.
     - Yes.
     - No.

   * - :class:`~debug_toolbar.panels.settings.SettingsPanel`
     - No instrumentation.
     - Yes.
     - No.

   * - :class:`~debug_toolbar.panels.headers.HeadersPanel`
     - No instrumentation.
     - Yes.
     - No.

   * - :class:`~debug_toolbar.panels.request.RequestPanel`
     - No instrumentation.
     - Yes.
     - No.

   * - :class:`~debug_toolbar.panels.alerts.AlertsPanel`
     - No instrumentation.
     - Yes.
     - No.

   * - :class:`~debug_toolbar.panels.signals.SignalsPanel`
     - No instrumentation; reads signal receivers already registered by
       Django/your project at ``generate_stats()`` time.
     - Yes.
     - No.

   * - :class:`~debug_toolbar.panels.community.CommunityPanel`
     - No instrumentation.
     - Yes.
     - No.

Recommendation for production-like environments
-------------------------------------------------

If you install the toolbar in an environment that also serves real traffic,
and you rely on ``SHOW_TOOLBAR_CALLBACK`` to gate it, the panels below are
safe to leave in ``DEBUG_TOOLBAR_PANELS`` because they only touch
global state while actively enabled for a request:

* ``HistoryPanel``
* ``VersionsPanel``
* ``TimerPanel``
* ``SettingsPanel``
* ``HeadersPanel``
* ``RequestPanel``
* ``SQLPanel``
* ``AlertsPanel``
* ``SignalsPanel``
* ``CommunityPanel``
* ``RedirectsPanel`` (disabled by default)
* ``ProfilingPanel`` (disabled by default)

``CachePanel``, ``TemplatesPanel``, and ``StaticFilesPanel`` install
permanent, process-wide monkey-patches the moment they are imported
(``ready()`` or module import), *before* any request is ever processed, and
those patches stay in place even if ``SHOW_TOOLBAR_CALLBACK`` always returns
``False`` and even if the panel is listed in ``DISABLE_PANELS``. If you need
to guarantee that the toolbar leaves the codebase's runtime behavior
completely untouched, remove those three panels from
``DEBUG_TOOLBAR_PANELS`` in the deployment(s) where that matters, for
example by building the setting conditionally::

    DEBUG_TOOLBAR_PANELS = [
        panel
        for panel in [
            "debug_toolbar.panels.history.HistoryPanel",
            "debug_toolbar.panels.versions.VersionsPanel",
            "debug_toolbar.panels.timer.TimerPanel",
            "debug_toolbar.panels.settings.SettingsPanel",
            "debug_toolbar.panels.headers.HeadersPanel",
            "debug_toolbar.panels.request.RequestPanel",
            "debug_toolbar.panels.sql.SQLPanel",
            "debug_toolbar.panels.staticfiles.StaticFilesPanel",
            "debug_toolbar.panels.templates.TemplatesPanel",
            "debug_toolbar.panels.alerts.AlertsPanel",
            "debug_toolbar.panels.cache.CachePanel",
            "debug_toolbar.panels.signals.SignalsPanel",
            "debug_toolbar.panels.community.CommunityPanel",
        ]
        if not IS_PRODUCTION_LIKE
        or panel
        not in {
            "debug_toolbar.panels.staticfiles.StaticFilesPanel",
            "debug_toolbar.panels.templates.TemplatesPanel",
            "debug_toolbar.panels.cache.CachePanel",
        }
    ]

Keep in mind that this trims functionality: the Templates, Static files, and
Cache panels will not be available at all, even when the toolbar is shown,
in environments where they've been excluded this way.
