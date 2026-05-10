from debug_toolbar import APP_NAME
from debug_toolbar.toolbar import DebugToolbar

app_name = APP_NAME
urlpatterns = DebugToolbar.get_urls()
