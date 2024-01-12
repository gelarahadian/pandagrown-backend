from rest_framework import generics
from .models import Notifications
from .serializers import NotificationsSerializer
# Create your views here.
class NotificationsListAPIView(generics.ListAPIView):
    serializer_class = NotificationsSerializer
    search_fields = ['name']  # Specify the fields to search for
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        if user_id:
            queryset = Notifications.objects.filter(user_id=user_id)
        else:
            queryset = Notifications.objects.all()
        queryset.update(is_read=True)
        queryset = queryset.order_by('-created_at')
        return queryset