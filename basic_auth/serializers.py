from rest_framework import serializers

class ObtainTokenSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()
