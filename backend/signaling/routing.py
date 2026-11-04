from django.urls import path
from . import consumers


websocket_urlpatterns = [
    path('ws/signaling/<uuid:room_uuid>', consumers.SignalingConsumer.as_asgi()),
]