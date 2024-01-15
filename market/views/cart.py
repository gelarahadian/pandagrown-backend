from channels.auth import get_user

from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from basic_auth.authentication import JWTAuthentication
from django.db.models import Sum, F
from panda_backend.utils import calc_profit, calc_round, calc_bonus
from market.models import MarketCart, Market, MarketUser
from user.models import UserProfile
from market.serializers import MarketCartSerializer, MarketCartPurchaseSerializer

User = get_user_model()

class MarketCartListCreateAPIView(generics.ListCreateAPIView):
    authentication_classes = [JWTAuthentication]
    queryset = MarketCart.objects.all()
    serializer_class = MarketCartSerializer
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        if user_id:
            queryset = MarketCart.objects.filter(user_id=user_id)
        else:
            queryset = MarketCart.objects.all()
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
        price_sum = request.data.get('price_sum')
        market_row = Market.objects.get(pk=market)
        if market_row.stock < purchased_amount:
            return Response({"type": "failure", "detail": "lack of stock"}, status=status.HTTP_400_BAD_REQUEST)    
        # Call the base create() method to perform the default creation process
        return super().create(request, *args, **kwargs)
    def delete(self, request, *args, **kwargs):
        user_id = self.kwargs['user_id']
        data = MarketCart.objects.filter(user_id=user_id)
        data.delete()
        return Response({'type': 'success'}, status=status.HTTP_200_OK)


class MarketCartPurchase(APIView):
    authentication_classes = [JWTAuthentication]
    def post(self, request, user_id, format=None):
        try:
            cart_rows = MarketCart.objects.filter(user_id=user_id)
            total_value = cart_rows.filter(payment_method=1).aggregate(sum_value=Sum(F('price_sum')))['sum_value'] or 0
            total_pga_value = cart_rows.filter(payment_method=0).aggregate(sum_value=Sum(F('price_sum')))['sum_value'] or 0


            user_profile_row = UserProfile.objects.filter(user_id=user_id).first()
            if (user_profile_row.balance < total_value):
                return Response({"type": "failure", "detail": "lack of balance"}, status=status.HTTP_400_BAD_REQUEST)    
            if user_profile_row.pandami_balance < total_pga_value:
                return Response({"type": "failure", "detail": "lack of PGA balance"}, status=status.HTTP_400_BAD_REQUEST)    
            lack_stock_detail_list = []
            for cart_item in cart_rows:
                market_row = Market.objects.get(pk=cart_item.market_id)
                cart_item.delete()
                if market_row.stock < cart_item.purchased_amount:
                    lack_stock_detail_list.append(market_row.name + ' is insufficient now')
                    continue

                # calculate profit according to payment method
                total_price = market_row.buy_price * cart_item.purchased_amount

                purchased_item = MarketUser(
                    market_id=cart_item.market_id,
                    user_id=cart_item.user_id,
                    purchased_amount=cart_item.purchased_amount,
                    payment_method=cart_item.payment_method,
                    price_sum=total_price,
                    status=0
                )
                
                
                purchased_item.save()
                market_row.stock = calc_round(market_row.stock - cart_item.purchased_amount)
                market_row.save()
            user_profile_row.balance = calc_round(user_profile_row.balance - total_value)
            user_profile_row.pandami_balance = calc_round(user_profile_row.pandami_balance - total_pga_value)
            user_profile_row.save()
        except (MarketCart.DoesNotExist):
            return Response({"type": "failure", "detail": "cart does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except (Market.DoesNotExist):
            return Response({"type": "failure", "detail": "market does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'type':'success', 'balance': user_profile_row.balance, 'pga_balance': user_profile_row.pandami_balance}, status=status.HTTP_200_OK)