=====================================
Django Debug Toolbar |latest-version|
=====================================

|build-status| |coverage| |docs| |python-support| |django-support|

.. |latest-version| image:: https://img.shields.io/pypi/v/django-debug-toolbar.svg
   :target: https://pypi.org/project/django-debug-toolbar/
   :alt: Latest version on PyPI

.. |build-status| image:: https://github.com/django-commons/django-debug-toolbar/workflows/Test/badge.svg
   :target: https://github.com/django-commons/django-debug-toolbar/actions/workflows/test.yml
   :alt: Build Status

.. |coverage| image:: https://img.shields.io/badge/Coverage-94%25-green
   :target: https://github.com/django-commons/django-debug-toolbar/actions/workflows/test.yml?query=branch%3Amain
   :alt: Test coverage status

.. |docs| image:: https://img.shields.io/readthedocs/django-debug-toolbar/latest.svg
   :target: https://readthedocs.org/projects/django-debug-toolbar/
   :alt: Documentation status

.. |python-support| image:: https://img.shields.io/pypi/pyversions/django-debug-toolbar
   :target: https://pypi.org/project/django-debug-toolbar/
   :alt: Supported Python versions

.. |django-support| image:: https://img.shields.io/pypi/djversions/django-debug-toolbar
   :target: https://pypi.org/project/django-debug-toolbar/
   :alt: Supported Django versions

The Django Debug Toolbar is a configurable set of panels that display various
debug information about the current request/response and when clicked, display
more details about the panel's content.

Here's a screenshot of the toolbar in action:

.. image:: https://raw.github.com/django-commons/django-debug-toolbar/main/example/django-debug-toolbar.png
   :alt: Django Debug Toolbar screenshot

In addition to the built-in panels, a number of third-party panels are
contributed by the community.

The current stable version of the Debug Toolbar is 5.1.0. It works on
Django ≥ 4.2.0.

The Debug Toolbar has experimental support for `Django's asynchronous views
<https://docs.djangoproject.com/en/dev/topics/async/>`_. Please note that
the Debug Toolbar still lacks the capability for handling concurrent requests.
If you find any issues, please report them on the `issue tracker`_.

Documentation, including installation and configuration instructions, is
available at https://django-debug-toolbar.readthedocs.io/.

The Django Debug Toolbar is released under the BSD license, like Django
itself. If you like it, please consider contributing!

The Django Debug Toolbar was originally created by Rob Hudson <rob@cogit8.org>
in August 2008 and was further developed by many contributors_.

.. _contributors: https://github.com/django-commons/django-debug-toolbar/graphs/contributors
.. _issue tracker: https://github.com/django-commons/django-debug-toolbar/issues
