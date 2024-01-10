from django.urls import path, include

from .views import market
from websocket_app.views import NotificationsListAPIView


urlpatterns = [
    # user
    path('manage/', market.MarketListView.as_view(), name="market-list")
]