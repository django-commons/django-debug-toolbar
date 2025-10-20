from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from debug_toolbar.toolbar import debug_toolbar_urls
from example.views import (
    async_db,
    async_db_concurrent,
    async_home,
    increment,
    jinja2_view,
)

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path(
        "bad-form/",
        TemplateView.as_view(template_name="bad_form.html"),
        name="bad_form",
    ),
    path("jinja/", jinja2_view, name="jinja"),
    path("async/", async_home, name="async_home"),
    path("async/db/", async_db, name="async_db"),
    path("async/db-concurrent/", async_db_concurrent, name="async_db_concurrent"),
    path("jquery/", TemplateView.as_view(template_name="jquery/index.html")),
    path("mootools/", TemplateView.as_view(template_name="mootools/index.html")),
    path("prototype/", TemplateView.as_view(template_name="prototype/index.html")),
    path(
        "htmx/boost/",
        TemplateView.as_view(template_name="htmx/boost.html"),
        name="htmx",
    ),
    path(
        "htmx/boost/2",
        TemplateView.as_view(
            template_name="htmx/boost.html", extra_context={"page_num": "2"}
        ),
        name="htmx2",
    ),
    path(
        "turbo/", TemplateView.as_view(template_name="turbo/index.html"), name="turbo"
    ),
    path(
        "turbo/2",
        TemplateView.as_view(
            template_name="turbo/index.html", extra_context={"page_num": "2"}
        ),
        name="turbo2",
    ),
    path("admin/", admin.site.urls),
    path("ajax/increment", increment, name="ajax_increment"),
] + debug_toolbar_urls()
