from django.urls import path

from example.async_ import views
from example.urls import urlpatterns as sync_urlpatterns

from .views import async_chat_index, async_chat_room

urlpatterns = [
    path("async/db/", views.async_db_view, name="async_db_view"),
    path("async/chat/", async_chat_index, name="async_chat"),
    path("async/chat/<str:room_name>/", async_chat_room, name="room"),
    *sync_urlpatterns,
]
