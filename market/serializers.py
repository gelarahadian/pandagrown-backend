from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from market.models import Market

User = get_user_model()

class MarketSerializer(serializers.ModelSerializer):
    cover_img = serializers.ImageField(required = False)
    class Meta:
        model = Market
        fields = ['id', 'cover_img', 'name', 'unit', 'buy_price', 'size', 'stock', 'benefit', 'benefit_type']
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
