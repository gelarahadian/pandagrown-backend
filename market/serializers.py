from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from market.models import Market, MarketCart

User = get_user_model()

class MarketSerializer(serializers.ModelSerializer):
    cover_img = serializers.ImageField(required = False)
    class Meta:
        model = Market
        fields = ['id', 'cover_img', 'name', 'unit', 'buy_price', 'size', 'stock', 'benefit', 'benefit_type']
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    

class MarketCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketCart
        fields = ['id', 'market', 'user', 'purchased_amount', 'price_sum', 'payment_method']
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class MarketCartPurchaseSerializer(serializers.ModelSerializer):
    market_data = MarketSerializer(source="market", read_only=True)
    class Meta:
        model = MarketCart
        fields = ['id', 'market', 'user', 'purchased_amount', 'price_sum', 'market_data']
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)