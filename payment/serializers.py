
from rest_framework import serializers
from payment.models import TransactionLog

class TransactionLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(read_only=True)
    user_name = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    unit = serializers.CharField(read_only=True)
    icon = serializers.CharField(read_only=True)
    class Meta:
        model = TransactionLog
        fields = ['id', 'user_name', 'user_email', 'user', 'amount', 'status', 'icon', 'tx_hash', 'type_id', 'method', 'address', 'coin_amount', 'created_at', 'updated_at', 'name', 'unit']