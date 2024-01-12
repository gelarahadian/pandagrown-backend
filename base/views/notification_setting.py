from rest_framework import viewsets, filters

from base.models import NotificationSetting
from base.serializers import NotificationSettingSerializer
from basic_auth.authentication import JWTAuthentication

class NotificationSettingViewSet(viewsets.ModelViewSet):
    queryset = NotificationSetting.objects.all()
    serializer_class = NotificationSettingSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]  # Add OrderingFilter and SearchFilter backends
    search_fields = ['name']  # Specify the fields to search for
    def get_permissions(self):
        print(self.action)
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            # Apply custom authentication only for POST, DELETE, UPDATE, PATCH
            return [JWTAuthentication()]
        else:
            # Use default authentication for other actions
            return super().get_permissions()