from django.urls import path

from debug_toolbar import APP_NAME, views as debug_toolbar_views
from debug_toolbar.toolbar import DebugToolbar

app_name = APP_NAME

urlpatterns = DebugToolbar.get_urls() + [
    path(
        "download_prof_file/",
        debug_toolbar_views.download_prof_file,
        name="debug_toolbar_download_prof_file",
    ),
]
