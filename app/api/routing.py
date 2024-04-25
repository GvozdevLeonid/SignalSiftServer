from django.urls import re_path

from api import consumers

websocket_urlpatterns = [
    re_path("api/(?P<room_name>\w+)/$", consumers.ApiConsumer.as_asgi()),
]
