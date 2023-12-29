from rest_framework import viewsets, filters

from base.models import FAQList
from base.serializers import FAQListSerializer
from basic_auth.authentication import JWTAuthentication

class FAQListViewSet(viewsets.ModelViewSet):
    queryset = FAQList.objects.all()
    serializer_class = FAQListSerializer
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