from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from inventory.models import Inventory

User = get_user_model()

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['id']
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    
