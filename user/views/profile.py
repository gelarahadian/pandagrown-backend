from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import json

from base.models import NotificationSetting
from basic_auth.authentication import JWTAuthentication
from panda_backend.utils import PandaListView, PandaCreateView, PandaDetailView, PandaUpdateView, PandaDeleteView, calc_round
from panda_backend.async_tasks import send_websocket_data
from shop.models import SeedUser
from user.models import UserProfile
from user.schema import UserProfileSchema
from user.serializers import UserProfileSerializer
from websocket_app.models import Notifications

User = get_user_model()
class UserProfileListView(PandaListView):
    authentication_classes = [JWTAuthentication]
    serializer_class = UserProfileSerializer
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        queryset = UserProfile.objects.filter(user_id=user_id)
        return queryset
    def retrieve(self, request, *args, **kwargs):
        user_id = self.kwargs['user_id']
        queryset = self.get_queryset().filter(user_id=user_id)
        user_profile = self.get_object(queryset)
        serializer = self.get_serializer(user_profile)
        return Response(serializer.data)
class UserProfileBalanceView(PandaListView):
    authentication_classes = [JWTAuthentication]
    def get(self, request, user_id, format=None):
        user = User.objects.get(pk=user_id)
        user_profile = UserProfile.objects.filter(user_id=user.id).first()
        return Response({'usd': user_profile.balance, 'pga': user_profile.pandami_balance})

class UserProfileCreateView(PandaCreateView):
    authentication_classes = [JWTAuthentication]
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    # Swagger 
    @swagger_auto_schema(responses={200: UserProfileSchema})
    def get_user_schema(self):
        return super().get_user_schema()
    
class UserProfileDetailView(PandaDetailView):
    authentication_classes = [JWTAuthentication]
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        user_id = self.kwargs['user_id']
        user = User.objects.get(pk=user_id)
        data = serializer.data
        data.update({'email': user.email})
        if data['avatar'] == settings.MEDIA_URL + 'avatar/avatar.jpg':  # Check 'avatar' in the data dictionary
            if data['gender'] == '0':
                data['avatar'] = settings.MEDIA_URL + 'avatar/female.png'
            else:
                data['avatar'] = settings.MEDIA_URL + 'avatar/male.png'
        return Response(data)
    
class UserProfileUpdateView(PandaUpdateView):
    authentication_classes = [JWTAuthentication]
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def get_object(self):
        user_id = self.kwargs['user_id']
        profile_id = self.kwargs['pk']
        queryset = self.get_queryset()
        user_profile = get_object_or_404(queryset, user_id=user_id, pk=profile_id)
        return user_profile
    
    def perform_update(self, serializer):
        user_id = self.kwargs['user_id']
        user_profile = UserProfile.objects.get(pk=self.kwargs['pk'])
        pre_balance = user_profile.balance
        pre_pga_balance = user_profile.pandami_balance
        # Call the superclass's perform_update method to perform the actual update
        super().perform_update(serializer)
        user_profile = UserProfile.objects.get(pk=self.kwargs['pk'])
        post_balance = user_profile.balance
        post_pga_balance = user_profile.pandami_balance
        if (pre_balance != post_balance):
            notification_setting = NotificationSetting.objects.filter(type='Profile_Update').first()
            context = Context({
                'NAME': user_profile.user.username,
                'BALANCE_TYPE': 'balance',
                'PRE_BALANCE': pre_balance,  
                'POST_BALANCE': user_profile.balance
            })
            template = Template(notification_setting.content)
            content = template.render(context)
            send_websocket_data.apply_async(args=[user_id, {'type': 'Profile_Update', 'content': content}])
        if (pre_pga_balance != post_pga_balance):
            notification_setting = NotificationSetting.objects.filter(type='Profile_Update').first()
            context = Context({
                'NAME': user_profile.user.username,
                'BALANCE_TYPE': 'PGA balance',
                'PRE_BALANCE': pre_pga_balance,  
                'POST_BALANCE': user_profile.pandami_balance
            })
            template = Template(notification_setting.content)
            content = template.render(context)
            send_websocket_data.apply_async(args=[user_id, {'type': 'Profile_Update', 'content': content}])
        data = serializer.data
        # Customizing the response data
        response_data = {
            'type': 'success',
            'detail': 'Profile updated successfully.',  # Add your custom message here
            'data': data
        }
        return Response(response_data, status=status.HTTP_200_OK)
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        data = serializer.data
        # Customizing the response data
        response_data = {
            'type': 'success',
            'detail': 'Profile updated successfully.',  # Add your custom message here
            'data': data
        }
        return Response(response_data, status=status.HTTP_200_OK)
        
class UserProfileDeleteView(PandaDeleteView):
    authentication_classes = [JWTAuthentication]
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def get_object(self):
        user_id = self.kwargs['user_id']
        profile_id = self.kwargs['pk']
        queryset = self.get_queryset()
        user_profile = get_object_or_404(queryset, user_id=user_id, pk=profile_id)
        return user_profile

class GetStatusView(APIView):
    authentication_classes = [JWTAuthentication]
    def get(self, request, user_id, format=None):
        user = User.objects.get(pk=user_id)
        user_profile = UserProfile.objects.filter(user_id=user.id).first()
        avatar_url = user_profile.avatar.url if user_profile.avatar else None
        full_avatar_url = request.build_absolute_uri(avatar_url) if avatar_url else None
        notifications = Notifications.objects.filter(user_id=user.id).filter(is_read=False).count()
        user_plants_count = calc_round(SeedUser.objects.filter(user_id=user.id).count())
        user_harvest_amount = calc_round(SeedUser.objects.filter(user_id=user.id, status=1).aggregate(sum_value=Sum(F('seed__harvest_rate') * F('purchased_amount') / 100))['sum_value'])
        user_profit = calc_round(
            SeedUser.objects.filter(user_id=user.id, status=1, payment_method=1).aggregate(sum_value=Sum(F('profit')))[
                'sum_value']) or 0
        user_profit_pga = calc_round(
            SeedUser.objects.filter(user_id=user.id, status=1, payment_method=0).aggregate(sum_value=Sum(F('profit')))[
                'sum_value'])
        response_data = json.dumps({
            'type': 'success', 
            'user_id': user.id, 
            'profile_avatar': full_avatar_url, 
            'username': user.username, 
            'profile_country': user_profile.country, 
            'profile_id': user_profile.id,
            'balance': user_profile.balance,
            'pga_balance': user_profile.pandami_balance,
            'notifications': notifications,
            'user_plants_count': user_plants_count,
            'user_harvest_amount': user_harvest_amount,
            'user_profit': user_profit,
            'user_profit_pga': user_profit_pga
        }, ensure_ascii=False).encode('utf-8')
        return HttpResponse(response_data, content_type='application/json; charset=utf-8')
