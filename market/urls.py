from django.urls import path, include

from .views import market, chart
from websocket_app.views import NotificationsListAPIView

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'', market.MarketViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('<int:user_id>/cart/', chart.MarketCartListCreateAPIView.as_view(), name='cart-list-create'),
]