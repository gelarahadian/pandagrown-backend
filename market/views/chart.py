from channels.auth import get_user

from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.response import Response
from basic_auth.authentication import JWTAuthentication
from market.models import MarketChart, Market
from market.serializers import MarketChartSerializer

User = get_user_model()

class MarketCartListCreateAPIView(generics.ListCreateAPIView):
    authentication_classes = [JWTAuthentication]
    queryset = MarketChart.objects.all()
    serializer_class = MarketChartSerializer
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        if user_id:
            queryset = MarketChart.objects.filter(user_id=user_id)
        else:
            queryset = MarketChart.objects.all()
        return queryset

    def get_permissions(self):
        if self.request.method == 'POST':
            # Apply custom authentication only for POST
            return [JWTAuthentication()]
        else:
            # Use default authentication for other methods
            return super().get_permissions()
    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user')
        market = request.data.get('market')
        purchased_amount = request.data.get('purchased_amount')
        seed_row = Market.objects.get(pk=market)
        if seed_row.stock < purchased_amount:
            return Response({"type": "failure", "detail": "lack of stock"}, status=status.HTTP_400_BAD_REQUEST)    
        # Call the base create() method to perform the default creation process
        return super().create(request, *args, **kwargs)
