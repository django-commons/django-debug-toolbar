from django.urls import path

from example.async_ import views
from example.urls import urlpatterns as sync_urlpatterns

urlpatterns = [
    path("async/db/", views.async_db_view, name="async_db_view"),
    *sync_urlpatterns,
    path("async/chat", views.async_chat_index, name="chat"),
]
