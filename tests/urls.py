from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import include, path, re_path

from . import views
from .models import NonAsciiRepr

urlpatterns = [
    re_path(
        r"^resolving1/(.+)/(.+)/$", views.resolving_view, name="positional-resolving"
    ),
    path("resolving2/<path:arg1>/<path:arg2>/", views.resolving_view),
    re_path(r"^resolving3/(.+)/$", views.resolving_view, {"arg2": "default"}),
    re_path(r"^regular/(?P<title>.*)/$", views.regular_view),
    re_path(r"^template_response/(?P<title>.*)/$", views.template_response_view),
    re_path(r"^regular_jinja/(?P<title>.*)/$", views.regular_jinjia_view),
    path("non_ascii_request/", views.regular_view, {"title": NonAsciiRepr()}),
    path("new_user/", views.new_user),
    path("execute_sql/", views.execute_sql),
    path("async_execute_sql/", views.async_execute_sql),
    path("async_execute_sql_concurrently/", views.async_execute_sql_concurrently),
    path("cached_view/", views.cached_view),
    path("cached_low_level_view/", views.cached_low_level_view),
    path("json_view/", views.json_view),
    path("redirect/", views.redirect_view),
    path("ajax/", views.ajax_view),
    path("login_without_redirect/", LoginView.as_view(redirect_field_name=None)),
    path("csp_view/", views.csp_view),
    path("admin/", admin.site.urls),
    path("__debug__/", include("debug_toolbar.urls")),
]
