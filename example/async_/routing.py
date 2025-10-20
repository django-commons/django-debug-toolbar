# This is the routing logic for the Django Channels "Web Socket" chat app
# https://channels.readthedocs.io/en/latest/tutorial/index.html
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
]
