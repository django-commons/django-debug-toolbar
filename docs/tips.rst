Tips
====

The toolbar isn't displayed!
----------------------------

The Debug Toolbar will only display when ``DEBUG = True`` in your project's
settings (see :ref:`Show Toolbar Callback <SHOW_TOOLBAR_CALLBACK>`) and your
IP address must also match an entry in your project's ``INTERNAL_IPS`` setting
(see :ref:`internal-ips`).  It will also only display if the MIME type of the
response is either ``text/html`` or ``application/xhtml+xml`` and contains a
closing ``</body>`` tag.

Be aware of middleware ordering and other middleware that may intercept
requests and return responses. Putting the debug toolbar middleware *after* the
``FlatpageFallbackMiddleware`` middleware, for example, means the toolbar will
not show up on flatpages.

Check your browser's caching
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Browsers have become more aggressive with caching static assets, such as
JavaScript and CSS files. Check your browser's development console, and if
you see errors, try a hard browser refresh or clearing your cache. There
should be an option on the network panel to disable caching, enable that
at least temporarily to make sure you're using the latest static assets.

Working with htmx and Turbo
----------------------------

Libraries such as `htmx <https://htmx.org/>`_ and
`Turbo <https://turbo.hotwired.dev/>`_ need additional configuration to retain
the toolbar handle element through page renders. This can be done by
configuring the :ref:`ROOT_TAG_EXTRA_ATTRS <ROOT_TAG_EXTRA_ATTRS>` to include
the relevant JavaScript library's attribute.

htmx
~~~~

The attribute `htmx <https://htmx.org/>`_ uses is
`hx-preserve <https://htmx.org/attributes/hx-preserve/>`_.

Update your settings to include:

.. code-block:: python

    DEBUG_TOOLBAR_CONFIG = {
        "ROOT_TAG_EXTRA_ATTRS": "hx-preserve"
    }

Hotwire Turbo
~~~~~~~~~~~~~

The attribute `Turbo <https://turbo.hotwired.dev/>`_ uses is
`data-turbo-permanent <https://turbo.hotwired.dev/reference/attributes>`_

Update your settings to include:

.. code-block:: python

    DEBUG_TOOLBAR_CONFIG = {
        "ROOT_TAG_EXTRA_ATTRS": "data-turbo-permanent"
    }


Performance considerations
--------------------------

The Debug Toolbar is designed to introduce as little overhead as possible in
the rendering of pages. However, depending on your project, the overhead may
become noticeable. In extreme cases, it can make development impractical.
Here's a breakdown of the performance issues you can run into and their
solutions.

Problems
~~~~~~~~

The Debug Toolbar works in two phases. First, it gathers data while Django
handles a request and stores this data in memory. Second, when you open a
panel in the browser, it fetches the data on the server and displays it.

If you're seeing excessive CPU or memory consumption while browsing your site,
you must optimize the "gathering" phase. If displaying a panel is slow, you
must optimize the "rendering" phase.

Culprits
~~~~~~~~

The SQL panel may be the culprit if your view performs many SQL queries. You
should attempt to minimize the number of SQL queries, but this isn't always
possible, for instance if you're using a CMS and have disabled caching for
development.

The cache panel is very similar to the SQL panel, except it isn't always a bad
practice to make many cache queries in a view.

The template panel becomes slow if your views or context processors return
large contexts and your templates have complex inheritance or inclusion
schemes.

Solutions
~~~~~~~~~

If the "gathering" phase is too slow, you can disable problematic panels
temporarily by deselecting the checkbox at the top right of each panel. That
change will apply to the next request. If you don't use some panels at all,
you can remove them permanently by customizing the ``DEBUG_TOOLBAR_PANELS``
setting.

By default, data gathered during the last 25 requests is kept in memory. This
allows you to use the toolbar on a page even if you have browsed to a few
other pages since you first loaded that page. You can reduce memory
consumption by setting the ``RESULTS_CACHE_SIZE`` configuration option to a
lower value. At worst, the toolbar will tell you that the data you're looking
for isn't available anymore.

If the "rendering" phase is too slow, refrain from clicking on problematic
panels :) Or reduce the amount of data gathered and rendered by these panels
by disabling some configuration options that are enabled by default:

- ``ENABLE_STACKTRACES`` for the SQL and cache panels,
- ``SHOW_TEMPLATE_CONTEXT`` for the template panel.
- ``PROFILER_CAPTURE_PROJECT_CODE`` and ``PROFILER_THRESHOLD_RATIO`` for the
  profiling panel.

Also, check ``SKIP_TEMPLATE_PREFIXES`` when you're using template-based
form widgets.
