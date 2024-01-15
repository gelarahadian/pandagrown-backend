from django.urls import path, include

from .views import inventory
from websocket_app.views import NotificationsListAPIView



urlpatterns = [
    path('<int:user_id>/user/', inventory.InventoryCartListAPIView.as_view(), name='inventory-list-create')
]