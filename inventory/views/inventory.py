from channels.auth import get_user

from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from basic_auth.authentication import JWTAuthentication
from market.models import MarketUser
from market.serializers import MarketCartPurchaseSerializer

User = get_user_model()

class InventoryCartListAPIView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    queryset = MarketUser.objects.all()
    serializer_class = MarketCartPurchaseSerializer
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        if user_id:
            queryset = MarketUser.objects.filter(user_id=user_id)
        else:
            queryset = MarketUser.objects.all()
        return queryset

    def get_permissions(self):
        if self.request.method == 'POST':
            # Apply custom authentication only for POST
            return [JWTAuthentication()]
        else:
            # Use default authentication for other methods
            return super().get_permissions()

