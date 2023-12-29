from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from basic_auth.authentication import JWTAuthentication
from panda_backend.utils import PandaListView, PandaCreateView, PandaDetailView, PandaUpdateView, PandaDeleteView, PandaPagination
from user.models import UserActivity
from user.serializers import UserActivitySerializer

class UserActivityListView(PandaListView):
    authentication_classes = [JWTAuthentication]
    serializer_class = UserActivitySerializer
    pagination_class = PandaPagination
    def list(self, request, *args, **kwargs): 
        self.pagination_class.page_size = request.query_params.get('page_size', self.pagination_class.page_size)
        queryset = self.filter_queryset(self.get_queryset(request))

        # Get the total count before pagination
        total_count = queryset.count()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data, total_count=total_count)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    def get_queryset(self, request):
        if 'user_id' in request.GET:
            user_id = self.kwargs['user_id']
            queryset = UserActivity.objects.filter(user_id=user_id)
        else:
            queryset = UserActivity.objects.all()
        return queryset

class UserActivityCreateView(PandaCreateView):
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    
class UserActivityDetailView(PandaDetailView):
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer

    def get_object(self):
        user_id = self.kwargs['user_id']
        activity_id = self.kwargs['pk']
        queryset = self.get_queryset()
        user_activity = get_object_or_404(queryset, user_id=user_id, pk=activity_id)
        return user_activity
    
class UserActivityUpdateView(PandaUpdateView):
    authentication_classes = [JWTAuthentication]
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer

    def get_object(self):
        user_id = self.kwargs['user_id']
        activity_id = self.kwargs['pk']
        queryset = self.get_queryset()
        user_activity = get_object_or_404(queryset, user_id=user_id, pk=activity_id)
        return user_activity
    
class UserActivityDeleteView(PandaDeleteView):
    authentication_classes = [JWTAuthentication]
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer

    def get_object(self):
        user_id = self.kwargs['user_id']
        activity_id = self.kwargs['pk']
        queryset = self.get_queryset()
        user_activity = get_object_or_404(queryset, user_id=user_id, pk=activity_id)
        return user_activity