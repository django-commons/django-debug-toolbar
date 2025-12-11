README
======

About
-----

This sample project demonstrates how to use the debug toolbar. It is designed
to run under the latest stable version of Django.

It also provides a few test pages to ensure the debug toolbar doesn't
interfere with common JavaScript frameworks.

How to
------

The example project requires a working installation of Django and a few other
packages::

    $ python -m pip install --group dev

The following command must run from the root directory of Django Debug Toolbar,
i.e. the directory that contains ``example/``::

    $ make example

This will create a database, superuser, and run the Django development server.
The superuser's username will be the same as the current OS user and the
password is "p".

If you'd like to run these steps individually, use the following commands.
Again, run from the root directory of Django Debug Toolbar.

Create a database::

    $ python example/manage.py migrate

Create a superuser::

    $ python example/manage.py createsuperuser

Run the Django development server::

    $ python example/manage.py runserver

You can change the database used by specifying the ``DB_BACKEND``
environment variable::

    $ DB_BACKEND=postgresql python example/manage.py migrate
    $ DB_BACKEND=postgresql python example/manage.py runserver

Using an asynchronous (ASGI) server:

Install [Daphne](https://pypi.org/project/daphne/) first:

    $ python -m pip install daphne

Then run the Django development server:

    $ ASYNC_SERVER=true python example/manage.py runserver
