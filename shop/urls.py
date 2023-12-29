from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.seed import SeedViewSet, SeedListViewSet, SeedMediaViewSet
from .views.cart import CartListCreateAPIView, CartRetrieveUpdateAPIView, PurchaseAPIView
from .views.house import GreenHouseListAPIView, WareHouseListAPIView, SellHarvestAPIView, SellOrderListAPIView

router = DefaultRouter()
router.register('list', SeedListViewSet, basename='seeds-list')
router.register('(?P<seed_id>\d+)/media', SeedMediaViewSet, basename='seed-media')
router.register(r'', SeedViewSet)

urlpatterns = [
    # Seed 
    path('seed/', include(router.urls)),
    path('<int:user_id>/cart/', CartListCreateAPIView.as_view(), name='cart-list-create'),
    path('cart/<int:pk>/', CartRetrieveUpdateAPIView.as_view(), name='cart-retrieve-update'),
    path('<int:user_id>/purchase/', PurchaseAPIView.as_view(), name='cart-purchase'),
    path('<int:user_id>/greenhouse/', GreenHouseListAPIView.as_view(), name='green-house-list'),
    path('<int:user_id>/warehouse/', WareHouseListAPIView.as_view(), name='ware-house-list'),
    path('<int:seed_user_id>/sell/harvest/', SellHarvestAPIView.as_view(), name='sell-harvest'),
    path('<int:user_id>/sell/order/', SellOrderListAPIView.as_view(), name='sell-order-list')
]