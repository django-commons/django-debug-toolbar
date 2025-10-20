Architecture
============

The Django Debug Toolbar is designed to be flexible and extensible for
developers and third-party panel creators.

Core Components
---------------

While there are several components, the majority of logic and complexity
lives within the following:

- ``debug_toolbar.middleware.DebugToolbarMiddleware``
- ``debug_toolbar.toolbar.DebugToolbar``
- ``debug_toolbar.panels``

^^^^^^^^^^^^^^^^^^^^^^
DebugToolbarMiddleware
^^^^^^^^^^^^^^^^^^^^^^

The middleware is how the toolbar integrates with Django projects.
It determines if the toolbar should instrument the request, which
panels to use, facilitates the processing of the request and augmenting
the response with the toolbar. Most logic for how the toolbar interacts
with the user's Django project belongs here.

^^^^^^^^^^^^
DebugToolbar
^^^^^^^^^^^^

The ``DebugToolbar`` class orchestrates the processing of a request
for each of the panels. It contains the logic that needs to be aware
of all the panels, but doesn't need to interact with the user's Django
project.

^^^^^^
Panels
^^^^^^

The majority of the complex logic lives within the panels themselves. This
is because the panels are responsible for collecting the various metrics.
Some of the metrics are collected via
`monkey-patching <https://stackoverflow.com/a/5626250>`_, such as
``TemplatesPanel``. Others, such as ``SettingsPanel`` don't need to collect
anything and include the data directly in the response.

Some panels such as ``SQLPanel`` have additional functionality. This tends
to involve a user clicking on something, and the toolbar presenting a new
page with additional data. That additional data is handled in views defined
in the panels package (for example, ``debug_toolbar.panels.sql.views``).

Logic Flow
----------

When a request comes in, the toolbar first interacts with it in the
middleware. If the middleware determines the request should be instrumented,
it will instantiate the toolbar and pass the request for processing. The
toolbar will use the enabled panels to collect information on the request
and/or response. When the toolbar has completed collecting its metrics on
both the request and response, the middleware will collect the results
from the toolbar. It will inject the HTML and JavaScript to render the
toolbar as well as any headers into the response.

After the browser renders the panel and the user interacts with it, the
toolbar's JavaScript will send requests to the server. If the view handling
the request needs to fetch data from the toolbar, the request must supply
the store ID. This is so that the toolbar can load the collected metrics
for that particular request.

The history panel allows a user to view the metrics for any request since
the application was started. The toolbar maintains its state entirely in
memory for the process running ``runserver``. If the application is
restarted the toolbar will lose its state.

Problematic Parts
-----------------

- ``debug.panels.templates.panel``: This monkey-patches template rendering
  when the panel module is loaded
- ``debug.panels.sql``: This package is particularly complex, but provides
  the main benefit of the toolbar
- Support for async and multi-threading: ``debug_toolbar.middleware.DebugToolbarMiddleware``
  is now async compatible and can process async requests. However certain
  panels such as ``RequestPanel`` and ``ProfilingPanel`` aren't
  fully compatible and currently being worked on. For now, these panels
  are disabled by default when running in async environment.
  follow the progress of this issue in `Async compatible toolbar project <https://github.com/orgs/jazzband/projects/9>`_.
- Django Channels incompatibility: The toolbar does not currently support
  Django Channels' consumers.
