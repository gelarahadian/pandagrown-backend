from django.urls import path
from websocket_app.consumers import HengrownConsumer

websocket_urlpatterns = [
    path('ws/<int:user_id>/', HengrownConsumer.as_asgi()),
]