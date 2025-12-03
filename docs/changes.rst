Change log
==========

Pending
-------

* Deprecated ``RedirectsPanel`` in favor of ``HistoryPanel`` for viewing
  toolbar data from redirected requests.
* Fixed support for generating code coverage comments in PRs.
* Added Django 6.0 to the testing matrix. Removed Django 5.0 to save CI
  resources.
* Show the cache backend alias and cache backend class name instead of
  the cache instance in the cache panel.
* Dropped support for the Python 3.9, it has reached its end of life date.
* Toggle tracking the toolbar's queries when using
  ``debug_toolbar.store.DatabaseStore`` with ``SKIP_TOOLBAR_QUERIES``.
* Fixed font family for code blocks and stack traces in the toolbar.
* Added test to confirm Django's ``TestCase.assertNumQueries`` works.
* Updated tox configuration to treat ``DeprecationWarning``,
  ``ResourceWarning``, and ``PendingDeprecationWarning`` as errors.

6.1.0 (2025-10-30)
------------------

* Added support for async to timer panel.
* Added a note about the default password in ``make example``.
* Removed logging about the toolbar failing to serialize a value into JSON.
* Moved the the import statement of ``debug_toolbar.urls`` to within the if
  statement's scope on the installation documentation.
* Changed ``StoredDebugToolbar.from_store`` to always create a panel key and
  class instance, regardless if any data was generated.
* Fixed selenium tests for CI by using psycopg for Python 3.13 runs.
* Added ``CommunityPanel`` containing links to documentation and resources.
* Upgraded CI ``postgis`` version to 17-3.5.
* Added how to generate the documentation locally to the contributing
  documentation.
* Updated logic that forces values to strings (``force_str``) to render
  "Django Debug Toolbar was unable to parse value." when there's a decoding
  error.
* Updated docs to show incompatibility with Django Channels.
* Hide the toolbar's migrations unless ``debug_toolbar.store.DatabaseStore``
  is being used. This may change in the future.
* Hide ``debug_toolbar.HistoryEntry`` as a model unless
  ``debug_toolbar.store.DatabaseStore`` is being used. This may change in the
  future.

6.0.0 (2025-07-22)
------------------

* Added support for checking if pytest as the test runner when determining
  if tests are running.
* Added ``show_toolbar_with_docker`` function to check Docker host IP address
  when running inside Docker containers.
* Defines the ``BaseStore`` interface for request storage mechanisms.
* Added the setting ``TOOLBAR_STORE_CLASS`` to configure the request
  storage mechanism. Defaults to ``debug_toolbar.store.MemoryStore``.
* Rename ``store_id`` properties to ``request_id`` and ``Toolbar.store`` to
  ``Toolbar.init_store``.
* Support ``Panel`` instances with stored stats via
  ``Panel.load_stats_from_store``.
* Swapped ``Toolbar._store`` for the ``get_store()`` class.
* Created a ``StoredDebugToolbar`` that support creating an instance of the
  toolbar representing an old request. It should only be used for fetching
  panels' contents.
* Drop ``raw_params`` from query data.
* Queries now have a unique ``djdt_query_id``. The SQL forms now reference
  this id and avoid passing SQL to be executed.
* Move the formatting logic of SQL queries to just before rendering in
  ``SQLPanel.content``.
* Make ``Panel.panel_id`` a class member.
* Update all panels to utilize data from ``Panel.get_stats()`` to load content
  to render. Specifically for ``Panel.title`` and ``Panel.nav_title``.
* Extend example app to contain an async version.
* Added ``debug_toolbar.store.DatabaseStore`` for persistent debug data
  storage.
* Deduplicated static files in the staticfiles panel.

5.2.0 (2025-04-29)
------------------

* Added hook to RedirectsPanel for subclass customization.
* Added feature to sanitize sensitive data in the Request Panel.
* Fixed dark mode conflict in code block toolbar CSS.
* Properly allowed overriding the system theme preference by using the theme
  selector. Removed the ``DEFAULT_THEME`` setting, we should always default to
  system-level defaults where possible.
* Added support for using django-template-partials with the template panel's
  source view functionality. The same change possibly adds support for other
  template loaders.
* Introduced `djade <https://github.com/adamchainz/djade>`__ to format Django
  templates.
* Swapped display order of panel header and close button to prevent style
  conflicts
* Added CSS for resetting the height of elements too to avoid problems with
  global CSS of a website where the toolbar is used.

5.1.0 (2025-03-20)
------------------

* Added Django 5.2 to the tox matrix.
* Updated package metadata to include well-known labels.
* Added resources section to the documentation.
* Wrap ``SHOW_TOOLBAR_CALLBACK`` function with ``sync_to_async``
  or ``async_to_sync`` to allow sync/async compatibility.
* Make ``require_toolbar`` decorator compatible to async views.
* Added link to contributing documentation in ``CONTRIBUTING.md``.
* Replaced ESLint and prettier with biome in our pre-commit configuration.
* Added a Makefile target (``make help``) to get a quick overview
  of each target.
* Avoided reinitializing the staticfiles storage during instrumentation.
* Avoided a "forked" Promise chain in the rebound ``window.fetch`` function
  with missing exception handling.
* Fixed the pygments code highlighting when using dark mode.
* Fix for exception-unhandled "forked" Promise chain in rebound window.fetch
* Create a CSP nonce property on the toolbar ``Toolbar().csp_nonce``.


5.0.1 (2025-01-13)
------------------
* Fixing the build and release process. No functional changes.

5.0.0 (2025-01-11)
------------------

* Added Python 3.13 to the CI matrix.
* Removed support for Python 3.8 as it has reached end of life.
* Converted to Django Commons PyPI release process.
* Fixed a crash which occurred when using non-``str`` static file values.
* Documented experimental async support.
* Improved troubleshooting doc for incorrect mime types for .js static files

Please see everything under 5.0.0-alpha as well.

5.0.0-alpha (2024-09-01)
------------------------

* Support async applications and ASGI from
  `Google Summer of Code Project 2024
  <https://summerofcode.withgoogle.com/programs/2024/projects/iXVvyGYp>`__.
* Added Django 5.1 to the CI matrix.
* Added support for the ``LoginRequiredMiddleware`` introduced in Django 5.1.
* Support select and explain buttons for ``UNION`` queries on PostgreSQL.
* Fixed internal toolbar requests being instrumented if the Django setting
  ``FORCE_SCRIPT_NAME`` was set.
* Increase opacity of show Debug Toolbar handle to improve accessibility.
* Changed the ``RedirectsPanel`` to be async compatible.
* Increased the contrast of text with dark mode enabled.
* Add translations for Bulgarian and Korean.
* Update translations for several languages.
* Include new translatable strings for translation.
* Fixed a crash which happened in the fallback case when session keys cannot be
  sorted.

4.4.6 (2024-07-10)
------------------

* Changed ordering (and grammatical number) of panels and their titles in
  documentation to match actual panel ordering and titles.
* Skipped processing the alerts panel when response isn't a HTML response.

4.4.5 (2024-07-05)
------------------

* Avoided crashing when the alerts panel was skipped.
* Removed the inadvertently added hard dependency on Jinja2.

4.4.4 (2024-07-05)
------------------

* Added check for StreamingHttpResponse in alerts panel.
* Instrument the Django Jinja2 template backend. This only instruments
  the immediate template that's rendered. It will not provide stats on
  any parent templates.

4.4.3 (2024-07-04)
------------------

* Added alerts panel with warning when form is using file fields
  without proper encoding type.
* Fixed overriding font-family for both light and dark themes.
* Restored compatibility with ``iptools.IpRangeList``.
* Limit ``E001`` check to likely error cases when the
  ``SHOW_TOOLBAR_CALLBACK`` has changed, but the toolbar's URL
  paths aren't installed.
* Introduce helper function ``debug_toolbar_urls`` to
  simplify installation.
* Moved "1rem" height/width for SVGs to CSS properties.

4.4.2 (2024-05-27)
------------------

* Removed some CSS which wasn't carefully limited to the toolbar's elements.
* Stopped assuming that ``INTERNAL_IPS`` is a list.
* Added a section to the installation docs about running tests in projects
  where the toolbar is being used.


4.4.1 (2024-05-26)
------------------

* Pin metadata version to 2.2 to be compatible with Jazzband release
  process.

4.4.0 (2024-05-26)
------------------

* Raised the minimum Django version to 4.2.
* Automatically support Docker rather than having the developer write a
  workaround for ``INTERNAL_IPS``.
* Display a better error message when the toolbar's requests
  return invalid json.
* Render forms with ``as_div`` to silence Django 5.0 deprecation warnings.
* Stayed on top of pre-commit hook updates.
* Added :doc:`architecture documentation <architecture>` to help
  on-board new contributors.
* Removed the static file path validation check in
  :class:`StaticFilesPanel <debug_toolbar.panels.staticfiles.StaticFilesPanel>`
  since that check is made redundant by a similar check in Django 4.0 and
  later.
* Deprecated the ``OBSERVE_REQUEST_CALLBACK`` setting and added check
  ``debug_toolbar.W008`` to warn when it is present in
  ``DEBUG_TOOLBAR_SETTINGS``.
* Add a note on the profiling panel about using Python 3.12 and later
  about needing ``--nothreading``
* Added ``IS_RUNNING_TESTS`` setting to allow overriding the
  ``debug_toolbar.E001`` check to avoid including the toolbar when running
  tests.
* Fixed the bug causing ``'djdt' is not a registered namespace`` and updated
  docs to help in initial configuration while running tests.
* Added a link in the installation docs to a more complete installation
  example in the example app.
* Added check to prevent the toolbar from being installed when tests
  are running.
* Added test to example app and command to run the example app's tests.
* Implemented dark mode theme and button to toggle the theme,
  introduced the ``DEFAULT_THEME`` setting which sets the default theme
  to use.

4.3.0 (2024-02-01)
------------------

* Dropped support for Django 4.0.
* Added Python 3.12 to test matrix.
* Removed outdated third-party panels from the list.
* Avoided the unnecessary work of recursively quoting SQL parameters.
* Postponed context process in templates panel to include lazy evaluated
  content.
* Fixed template panel to avoid evaluating ``LazyObject`` when not already
  evaluated.
* Added support for Django 5.0.
* Refactor the ``utils.get_name_from_obj`` to simulate the behavior of
  ``django.contrib.admindocs.utils.get_view_name``.
* Switched from black to the `ruff formatter
  <https://astral.sh/blog/the-ruff-formatter>`__.
* Changed the default position of the toolbar from top to the upper top
  position.
* Added the setting, ``UPDATE_ON_FETCH`` to control whether the
  toolbar automatically updates to the latest AJAX request or not.
  It defaults to ``False``.

4.2.0 (2023-08-10)
------------------

* Adjusted app directories system check to allow for nested template loaders.
* Switched from flake8, isort and pyupgrade to `ruff
  <https://beta.ruff.rs/>`__.
* Converted cookie keys to lowercase. Fixed the ``samesite`` argument to
  ``djdt.cookie.set``.
* Converted ``StaticFilesPanel`` to no longer use a thread collector. Instead,
  it collects the used static files in a ``ContextVar``.
* Added check ``debug_toolbar.W007`` to warn when JavaScript files are
  resolving to the wrong content type.
* Fixed SQL statement recording under PostgreSQL for queries encoded as byte
  strings.
* Patch the ``CursorWrapper`` class with a mixin class to support multiple
  base wrapper classes.

4.1.0 (2023-05-15)
------------------
* Improved SQL statement formatting performance.  Additionally, fixed the
  indentation of ``CASE`` statements and stopped simplifying ``.count()``
  queries.
* Added support for the new STORAGES setting in Django 4.2 for static files.
* Added support for theme overrides.
* Reworked the cache panel instrumentation code to no longer attempt to undo
  monkey patching of cache methods, as that turned out to be fragile in the
  presence of other code which also monkey patches those methods.
* Update all timing code that used :py:func:`time.time()` to use
  :py:func:`time.perf_counter()` instead.
* Made the check on ``request.META["wsgi.multiprocess"]`` optional, but
  defaults to forcing the toolbar to render the panels on each request. This
  is because it's likely an ASGI application that's serving the responses
  and that's more likely to be an incompatible setup. If you find that this
  is incorrect for you in particular, you can use the ``RENDER_PANELS``
  setting to forcibly control this logic.

4.0.0 (2023-04-03)
------------------

* Added Django 4.2 to the CI.
* Dropped support for Python 3.7.
* Fixed PostgreSQL raw query with a tuple parameter during on explain.
* Use ``TOOLBAR_LANGUAGE`` setting when rendering individual panels
  that are loaded via AJAX.
* Add decorator for rendering toolbar views with ``TOOLBAR_LANGUAGE``.
* Removed the logging panel. The panel's implementation was too complex, caused
  memory leaks and sometimes very verbose and hard to silence output in some
  environments (but not others). The maintainers judged that time and effort is
  better invested elsewhere.
* Added support for psycopg3.
* When ``ENABLE_STACKTRACE_LOCALS`` is ``True``, the stack frames' locals dicts
  will be converted to strings when the stack trace is captured rather when it
  is rendered, so that the correct values will be displayed in the rendered
  stack trace, as they may have changed between the time the stack trace was
  captured and when it is rendered.

3.8.1 (2022-12-03)
------------------

* Fixed release process by re-adding twine to release dependencies. No
  functional change.

3.8.0 (2022-12-03)
------------------

* Added protection against division by 0 in timer.js
* Auto-update History panel for JavaScript ``fetch`` requests.
* Support `HTMX boosting <https://htmx.org/docs/#boosting>`__ and
  `Turbo <https://turbo.hotwired.dev/>`__ pages.
* Simplify logic for ``Panel.enabled`` property by checking cookies earlier.
* Include panel scripts in content when ``RENDER_PANELS`` is set to True.
* Create one-time mouseup listener for each mousedown when dragging the
  handle.
* Update package metadata to use Hatchling.
* Fix highlighting on history panel so odd rows are highlighted when
  selected.
* Formalize support for Python 3.11.
* Added ``TOOLBAR_LANGUAGE`` setting.

3.7.0 (2022-09-25)
------------------

* Added Profiling panel setting ``PROFILER_THRESHOLD_RATIO`` to give users
  better control over how many function calls are included. A higher value
  will include more data, but increase render time.
* Update Profiling panel to include try to always include user code. This
  code is more important to developers than dependency code.
* Highlight the project function calls in the profiling panel.
* Added Profiling panel setting ``PROFILER_CAPTURE_PROJECT_CODE`` to allow
  users to disable the inclusion of all project code. This will be useful
  to project setups that have dependencies installed under
  ``settings.BASE_DIR``.
* The toolbar's font stack now prefers system UI fonts. Tweaked paddings,
  margins and alignments a bit in the CSS code.
* Only sort the session dictionary when the keys are all strings. Fixes a
  bug that causes the toolbar to crash when non-strings are used as keys.

3.6.0 (2022-08-17)
------------------

* Remove decorator ``signed_data_view`` as it was causing issues with
  `django-urlconfchecks <https://github.com/AliSayyah/django-urlconfchecks/>`__.
* Added pygments to the test environment and fixed a crash when using the
  template panel with Django 4.1 and pygments installed.
* Stayed on top of pre-commit hook and GitHub actions updates.
* Added some workarounds to avoid a Chromium warning which was worrisome to
  developers.
* Avoided using deprecated Selenium methods to find elements.
* Raised the minimum Django version from 3.2 to 3.2.4 so that we can take
  advantage of backported improvements to the cache connection handler.

3.5.0 (2022-06-23)
------------------

* Properly implemented tracking and display of PostgreSQL transactions.
* Removed third party panels which have been archived on GitHub.
* Added Django 4.1b1 to the CI matrix.
* Stopped crashing when ``request.GET`` and ``request.POST`` are neither
  dictionaries nor ``QueryDict`` instances. Using anything but ``QueryDict``
  instances isn't a valid use of Django but, again, django-debug-toolbar
  shouldn't crash.
* Fixed the cache panel to work correctly in the presence of concurrency by
  avoiding the use of signals.
* Reworked the cache panel instrumentation mechanism to monkey patch methods on
  the cache instances directly instead of replacing cache instances with
  wrapper classes.
* Added a :meth:`debug_toolbar.panels.Panel.ready` class method that panels can
  override to perform any initialization or instrumentation that needs to be
  done unconditionally at startup time.
* Added pyflame (for flame graphs) to the list of third-party panels.
* Fixed the cache panel to correctly count cache misses from the get_many()
  cache method.
* Removed some obsolete compatibility code from the stack trace recording code.
* Added a new mechanism for capturing stack traces which includes per-request
  caching to reduce expensive file system operations.  Updated the cache and
  SQL panels to record stack traces using this new mechanism.
* Changed the ``docs`` tox environment to allow passing positional arguments.
  This allows e.g. building a HTML version of the docs using ``tox -e docs
  html``.
* Stayed on top of pre-commit hook updates.
* Replaced ``OrderedDict`` by ``dict`` where possible.

Deprecated features
~~~~~~~~~~~~~~~~~~~

* The ``debug_toolbar.utils.get_stack()`` and
  ``debug_toolbar.utils.tidy_stacktrace()`` functions are deprecated in favor
  of the new ``debug_toolbar.utils.get_stack_trace()`` function.  They will
  removed in the next major version of the Debug Toolbar.

3.4.0 (2022-05-03)
------------------

* Fixed issue of stacktrace having frames that have no path to the file,
  but are instead a string of the code such as
  ``'<frozen importlib._bootstrap>'``.
* Renamed internal SQL tracking context var from ``recording`` to
  ``allow_sql``.

3.3.0 (2022-04-28)
------------------

* Track calls to :py:meth:`django.core.cache.cache.get_or_set`.
* Removed support for Django < 3.2.
* Updated check ``W006`` to look for
  ``django.template.loaders.app_directories.Loader``.
* Reset settings when overridden in tests. Packages or projects using
  django-debug-toolbar can now use Django’s test settings tools, like
  ``@override_settings``, to reconfigure the toolbar during tests.
* Optimize rendering of SQL panel, saving about 30% of its run time.
* New records in history panel will flash green.
* Automatically update History panel on AJAX requests from client.

3.2.4 (2021-12-15)
------------------

* Revert PR 1426 - Fixes issue with SQL parameters having leading and
  trailing characters stripped away.

3.2.3 (2021-12-12)
------------------

* Changed cache monkey-patching for Django 3.2+ to iterate over existing
  caches and patch them individually rather than attempting to patch
  ``django.core.cache`` as a whole. The ``middleware.cache`` is still
  being patched as a whole in order to attempt to catch any cache
  usages before ``enable_instrumentation`` is called.
* Add check ``W006`` to warn that the toolbar is incompatible with
  ``TEMPLATES`` settings configurations with ``APP_DIRS`` set to ``False``.
* Create ``urls`` module and update documentation to no longer require
  importing the toolbar package.


3.2.2 (2021-08-14)
------------------

* Ensured that the handle stays within bounds when resizing the window.
* Disabled ``HistoryPanel`` when ``RENDER_PANELS`` is ``True``
  or if ``RENDER_PANELS`` is ``None`` and the WSGI container is
  running with multiple processes.
* Fixed ``RENDER_PANELS`` functionality so that when ``True`` panels are
  rendered during the request and not loaded asynchronously.
* HistoryPanel now shows status codes of responses.
* Support ``request.urlconf`` override when checking for toolbar requests.


3.2.1 (2021-04-14)
------------------

* Fixed SQL Injection vulnerability, CVE-2021-30459. The toolbar now
  calculates a signature on all fields for the SQL select, explain,
  and analyze forms.
* Changed ``djdt.cookie.set()`` to set ``sameSite=Lax`` by default if
  callers do not provide a value.
* Added ``PRETTIFY_SQL`` configuration option to support controlling
  SQL token grouping. By default it's set to True. When set to False,
  a performance improvement can be seen by the SQL panel.
* Added a JavaScript event when a panel loads of the format
  ``djdt.panel.[PanelId]`` where PanelId is the ``panel_id`` property
  of the panel's Python class. Listening for this event corrects the bug
  in the Timer Panel in which it didn't insert the browser timings
  after switching requests in the History Panel.
* Fixed issue with the toolbar expecting URL paths to start with
  ``/__debug__/`` while the documentation indicates it's not required.

3.2 (2020-12-03)
----------------

* Moved CI to GitHub Actions: https://github.com/jazzband/django-debug-toolbar/actions
* Stopped crashing when ``request.GET`` and ``request.POST`` are
  dictionaries instead of ``QueryDict`` instances. This isn't a valid
  use of Django but django-debug-toolbar shouldn't crash anyway.
* Fixed a crash in the history panel when sending a  JSON POST request
  with invalid JSON.
* Added missing signals to the signals panel by default.
* Documented how to avoid CORS errors now that we're using JavaScript
  modules.
* Verified support for Python 3.9.
* Added a ``css`` and a ``js`` template block to
  ``debug_toolbar/base.html`` to allow overriding CSS and JS.


3.2a1 (2020-10-19)
------------------

* Fixed a regression where the JavaScript code crashed with an invalid
  CSS selector when searching for an element to replace.
* Replaced remaining images with CSS.
* Continued refactoring the HTML and CSS code for simplicity, continued
  improving the use of semantic HTML.
* Stopped caring about prehistoric browsers for good. Started splitting
  up the JavaScript code to take advantage of JavaScript modules.
* Continued removing unused CSS.
* Started running Selenium tests on Travis CI.
* Added a system check which prevents using django-debug-toolbar without
  any enabled panels.
* Added :meth:`Panel.run_checks() <debug_toolbar.panels.Panel.run_checks>` for
  panels to verify the configuration before the application starts.
* Validate the static file paths specified in ``STATICFILES_DIRS``
  exist via :class:`~debug_toolbar.panels.staticfiles.StaticFilesPanel`
* Introduced `prettier <https://prettier.io/>`__ to format the frontend
  code.
* Started accessing history views using GET requests since they do not
  change state on the server.
* Fixed a bug where unsuccessful requests (e.g. network errors) were
  silently ignored.
* Started spellchecking the documentation.
* Removed calls to the deprecated ``request.is_ajax()`` method. These calls
  were unnecessary now that most endpoints return JSON anyway.
* Removed support for Python 3.5.


3.1 (2020-09-21)
----------------

* Fixed a crash in the history panel when sending an empty JSON POST
  request.
* Made ``make example`` also set up the database and a superuser
  account.
* Added a Makefile target for regenerating the django-debug-toolbar
  screenshot.
* Added automatic escaping of panel titles resp. disallowed HTML tags.
* Removed some CSS
* Restructured the SQL stats template.
* Changed command line examples to prefer ``python -m pip`` to ``pip``.


3.0 (2020-09-20)
----------------

* Added an ``.editorconfig`` file specifying indentation rules etc.
* Updated the Italian translation.
* Added support for Django 3.1a1. ``fetch()`` and ``jQuery.ajax`` requests are
  now detected by the absence of a ``Accept: text/html`` header instead of the
  jQuery-specific ``X-Requested-With`` header on Django 3.1 or better.
* Pruned unused CSS and removed hacks for ancient browsers.
* Added the new :attr:`Panel.scripts <debug_toolbar.panels.Panel.scripts>`
  property. This property should return a list of JavaScript resources to be
  loaded in the browser when displaying the panel. Right now, this is used by a
  single panel, the Timer panel. Third party panels can use this property to
  add scripts rather then embedding them in the content HTML.
* Switched from JSHint to ESLint. Added an ESLint job to the Travis CI matrix.
* Debug toolbar state which is only needed in the JavaScript code now uses
  ``localStorage``.
* Updated the code to avoid a few deprecation warnings and resource warnings.
* Started loading JavaScript as ES6 modules.
* Added support for :meth:`cache.touch() <django.core.cache.cache.touch>` when
  using django-debug-toolbar.
* Eliminated more inline CSS.
* Updated ``tox.ini`` and ``Makefile`` to use isort>=5.
* Increased RESULTS_CACHE_SIZE to 25 to better support AJAX requests.
* Fixed the close button CSS by explicitly specifying the
  ``box-sizing`` property.
* Simplified the ``isort`` configuration by taking advantage of isort's
  ``black`` profile.
* Added :class:`~debug_toolbar.panels.history.HistoryPanel` including support
  for AJAX requests.

**Backwards incompatible changes**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Loading panel content no longer executes the scripts elements embedded in the
  HTML. Third party panels that require JavaScript resources should now use the
  :attr:`Panel.scripts <debug_toolbar.panels.Panel.scripts>` property.
* Removed support for end of life Django 1.11. The minimum supported Django is
  now 2.2.
* The Debug Toolbar now loads a `JavaScript module`_. Typical local development
  using Django ``runserver`` is not impacted. However, if your application
  server and static files server are at different origins, you may see CORS
  errors in your browser's development console. See the "Cross-Origin Request
  Blocked" section of the :doc:`installation docs <installation>` for details
  on how to resolve this issue.

.. _JavaScript module: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules

2.2 (2020-01-31)
----------------

* Removed support for end of life Django 2.0 and 2.1.
* Added support for Python 3.8.
* Add locals() option for SQL panel.
* Added support for Django 3.0.


2.1 (2019-11-12)
----------------

* Changed the Travis CI matrix to run style checks first.
* Exposed the ``djdt.init`` function too.
* Small improvements to the code to take advantage of newer Django APIs
  and avoid warnings because of deprecated code.
* Verified compatibility with the upcoming Django 3.0 (at the time of
  writing).


2.0 (2019-06-20)
----------------

* Updated :class:`~debug_toolbar.panels.staticfiles.StaticFilesPanel` to be
  compatible with Django 3.0.
* The :class:`~debug_toolbar.panels.profiling.ProfilingPanel` is now enabled
  but inactive by default.
* Fixed toggling of table rows in the profiling panel UI.
* The :class:`~debug_toolbar.panels.profiling.ProfilingPanel` no longer skips
  remaining panels or middlewares.
* Improved the installation documentation.
* Fixed a possible crash in the template panel.
* Added support for psycopg2 ``Composed`` objects.
* Changed the Jinja2 tests to use Django's own Jinja2 template backend.
* Added instrumentation to queries using server side cursors.
* Too many small improvements and cleanups to list them all.

**Backwards incompatible changes**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Removed support for Python 2.
* Removed support for Django's deprecated ``MIDDLEWARE_CLASSES`` setting.
* Restructured :class:`debug_toolbar.panels.Panel` to execute more like the
  new-style Django MIDDLEWARE. The ``Panel.__init__()`` method is now passed
  ``get_response`` as the first positional argument. The
  :meth:`debug_toolbar.panels.Panel.process_request` method must now always
  return a response. Usually this is the response returned by
  ``get_response()`` but the panel may also return a different response as is
  the case in the :class:`~debug_toolbar.panels.redirects.RedirectsPanel`.
  Third party panels must adjust to this new architecture.
  ``Panel.process_response()`` and ``Panel.process_view()`` have been removed
  as a result of this change.

The deprecated API, ``debug_toolbar.panels.DebugPanel``, has been removed.
Third party panels should use :class:`debug_toolbar.panels.Panel` instead.

The following deprecated settings have been removed:

* ``HIDDEN_STACKTRACE_MODULES``
* ``HIDE_DJANGO_SQL``
* ``INTERCEPT_REDIRECTS``
* ``RESULTS_STORE_SIZE``
* ``ROOT_TAG_ATTRS``
* ``TAG``

1.11 (2018-12-03)
-----------------

* Use ``defer`` on all ``<script>`` tags to avoid blocking HTML parsing,
  removed inline JavaScript.
* Stop inlining images in CSS to avoid Content Security Policy errors
  altogether.
* Reformatted the code using `black <https://github.com/ambv/black>`__.
* Added the Django mail panel to the list of third-party panels.
* Convert system check errors to warnings to accommodate exotic
  configurations.
* Fixed a crash when explaining raw querysets.
* Fixed an obscure Unicode error with binary data fields.
* Added MariaDB and Python 3.7 builds to the CI.

1.10.1 (2018-09-11)
-------------------

* Fixed a problem where the duplicate query detection breaks for
  unhashable query parameters.
* Added support for structured types when recording SQL.
* Made Travis CI also run one test no PostgreSQL.
* Added fallbacks for inline images in CSS.
* Improved cross-browser compatibility around ``URLSearchParams`` usage.
* Fixed a few typos and redundancies in the documentation, removed
  mentions of django-debug-toolbar's jQuery which aren't accurate
  anymore.

1.10 (2018-09-06)
-----------------

* Removed support for Django < 1.11.
* Added support and testing for Django 2.1 and Python 3.7. No actual code
  changes were required.
* Removed the jQuery dependency. This means that django-debug-toolbar
  now requires modern browsers with support for ``fetch``, ``classList``
  etc. The ``JQUERY_URL`` setting is also removed because it isn't
  necessary anymore. If you depend on jQuery, integrate it yourself.
* Added support for the server timing header.
* Added a differentiation between similar and duplicate queries. Similar
  queries are what duplicate queries used to be (same SQL, different
  parameters).
* Stopped hiding frames from Django's contrib apps in stacktraces by
  default.
* Lots of small cleanups and bug fixes.

1.9.1 (2017-11-15)
------------------

* Fix erroneous ``ContentNotRenderedError`` raised by the redirects panel.

1.9 (2017-11-13)
----------------

This version is compatible with Django 2.0 and requires Django 1.8 or
later.

Bug fixes
~~~~~~~~~

* The profiling panel now escapes reported data resulting in valid HTML.
* Many minor cleanups and bug fixes.

1.8 (2017-05-05)
----------------

This version is compatible with Django 1.11 and requires Django 1.8 or
later.

**Backwards incompatible changes**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``debug_toolbar.middleware.show_toolbar`` (the default value of setting
  ``SHOW_TOOLBAR_CALLBACK``) no longer returns ``False`` for AJAX requests.
  This is to allow reusing the ``SHOW_TOOLBAR_CALLBACK`` function to verify
  access to panel views requested via AJAX. Projects defining a custom
  ``SHOW_TOOLBAR_CALLBACK`` should remove checks for AJAX requests in order to
  continue to allow access to these panels.

Features
~~~~~~~~

* New decorator ``debug_toolbar.decorators.require_show_toolbar`` prevents
  unauthorized access to decorated views by checking ``SHOW_TOOLBAR_CALLBACK``
  every request. Unauthorized access results in a 404.
* The ``SKIP_TEMPLATE_PREFIXES`` setting allows skipping templates in
  the templates panel. Template-based form widgets' templates are
  skipped by default to avoid panel sizes going into hundreds of
  megabytes of HTML.

Bug fixes
~~~~~~~~~

* All views are now decorated with
  ``debug_toolbar.decorators.require_show_toolbar`` preventing unauthorized
  access.
* The templates panel now reuses contexts' pretty printed version which
  makes the debug toolbar usable again with Django 1.11's template-based
  forms rendering.
* Long SQL statements are now forcibly wrapped to fit on the screen.

1.7 (2017-03-05)
----------------

Bug fixes
~~~~~~~~~

* Recursive template extension is now understood.
* Deprecation warnings were fixed.
* The SQL panel uses HMAC instead of simple hashes to verify that SQL
  statements have not been changed. Also, the handling of bytes and text
  for hashing has been hardened. Also, a bug with Python's division
  handling has been fixed for improved Python 3 support.
* An error with django-jinja has been fixed.
* A few CSS classes have been prefixed with ``djdt-`` to avoid
  conflicting class names.

1.6 (2016-10-05)
----------------

The debug toolbar was adopted by Jazzband.

Removed features
~~~~~~~~~~~~~~~~

* Support for automatic setup has been removed as it was frequently
  problematic. Installation now requires explicit setup. The
  ``DEBUG_TOOLBAR_PATCH_SETTINGS`` setting has also been removed as it is now
  unused. See the :doc:`installation documentation <installation>` for details.

Bug fixes
~~~~~~~~~

* The ``DebugToolbarMiddleware`` now also supports Django 1.10's ``MIDDLEWARE``
  setting.

1.5 (2016-07-21)
----------------

This version is compatible with Django 1.10 and requires Django 1.8 or later.

Support for Python 3.2 is dropped.

Bug fixes
~~~~~~~~~

* Restore compatibility with sqlparse ≥ 0.2.0.
* Add compatibility with Bootstrap 4, Pure CSS, MDL, etc.
* Improve compatibility with RequireJS / AMD.
* Improve the UI slightly.
* Fix invalid (X)HTML.

1.4 (2015-10-06)
----------------

This version is compatible with Django 1.9 and requires Django 1.7 or later.

New features
~~~~~~~~~~~~

* New panel method :meth:`debug_toolbar.panels.Panel.generate_stats` allows
  panels to only record stats when the toolbar is going to be inserted into
  the response.

Bug fixes
~~~~~~~~~

* Response time for requests of projects with numerous media files has
  been improved.

1.3 (2015-03-10)
----------------

This is the first version compatible with Django 1.8.

New features
~~~~~~~~~~~~

* A new panel is available: Template Profiler.
* The ``SHOW_TOOLBAR_CALLBACK`` accepts a callable.
* The toolbar now provides a :ref:`javascript-api`.

Bug fixes
~~~~~~~~~

* The toolbar handle cannot leave the visible area anymore when the toolbar is
  collapsed.
* The root level logger is preserved.
* The ``RESULTS_CACHE_SIZE`` setting is taken into account.
* CSS classes are prefixed with ``djdt-`` to prevent name conflicts.
* The private copy of jQuery no longer registers as an AMD module on sites
  that load RequireJS.

1.2 (2014-04-25)
----------------

New features
~~~~~~~~~~~~

* The ``JQUERY_URL`` setting defines where the toolbar loads jQuery from.

Bug fixes
~~~~~~~~~

* The toolbar now always loads a private copy of jQuery in order to avoid
  using an incompatible version. It no longer attempts to integrate with AMD.

  This private copy is available in ``djdt.jQuery``. Third-party panels are
  encouraged to use it because it should be as stable as the toolbar itself.

1.1 (2014-04-12)
----------------

This is the first version compatible with Django 1.7.

New features
~~~~~~~~~~~~

* The SQL panel colors queries depending on the stack level.
* The Profiler panel allows configuring the maximum depth.

Bug fixes
~~~~~~~~~

* Support languages where lowercase and uppercase strings may have different
  lengths.
* Allow using cursor as context managers.
* Make the SQL explain more helpful on SQLite.
* Various JavaScript improvements.

Deprecated features
~~~~~~~~~~~~~~~~~~~

* The ``INTERCEPT_REDIRECTS`` setting is superseded by the more generic
  ``DISABLE_PANELS``.

1.0 (2013-12-21)
----------------

This is the first stable version of the Debug Toolbar!

It includes many new features and performance improvements as well a few
backwards-incompatible changes to make the toolbar easier to deploy, use,
extend and maintain in the future.

You're strongly encouraged to review the installation and configuration docs
and redo the setup in your projects.

Third-party panels will need to be updated to work with this version.
