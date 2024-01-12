from shop.models import SeedUser, SeedOrder, Seed
from user.models import UserProfile
from panda_backend.utils import calc_round
from base.models import NotificationSetting
from shop.serializers import SeedUserSerializer, SellOrderSerializer
from django.conf import settings
from django.db.models import F, ExpressionWrapper, IntegerField, FloatField, EmailField, CharField
from django.db.models.functions import ExtractDay
from django.utils import timezone
from rest_framework.views import APIView
from basic_auth.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import generics, status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from panda_backend.async_tasks import send_websocket_data
from django.template import Template, Context


class GreenHouseListAPIView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    # queryset = SeedUser.objects.prefetch_related('seed_media')  # Add 'seed_media' prefetch
    queryset = SeedUser.objects.select_related('seed').prefetch_related('seed__seed_media')
    serializer_class = SeedUserSerializer
    search_fields = ['name']  # Specify the fields to search for
    def get_queryset(self):
        # user_id = self.request.GET.get('user_id')
        user_id = self.kwargs['user_id']
        if user_id:
            queryset = SeedUser.objects.filter(user_id=user_id)
        else:
            queryset = SeedUser.objects.all()
        sort_param = self.request.query_params.get('sort', None)
        if sort_param:
            # Determine the field and direction for sorting
            sort_fields = sort_param.split(',')
            ordering = []
            for field in sort_fields:
                if field.startswith('-'):
                    if field in ['-name', '-buy_price', '-harvest_rate']:
                        field = '-seed__' + field[1:]
                else:
                    if field in ['name', 'buy_price', 'harvest_rate']:
                        field = 'seed__' + field
                ordering.append(field.strip())

            # Apply sorting to the queryset
            queryset = queryset.order_by(*ordering)
        queryset = queryset.filter(seed__name__icontains=self.request.query_params.get('search', ''))
        queryset = queryset.filter(status=0) # Getting items which are status = 0 (greenhouse and warehouse)
         # Filter based on (vegetation_mass_period + flowering_preharvest_period + seed__harvest_period) > current_period
        current_time = timezone.now()
        vegetation_mass_period = ExpressionWrapper(
            F('seed__vegetation_mass_period') - settings.SERVICE_SILICA_PERIOD * F('method_silica'),
            output_field=IntegerField()
        )
        flowering_preharvest_period = ExpressionWrapper(
            F('seed__flowering_preharvest_period') - settings.SERVICE_BOTANICARE_PERIOD * F('method_botanicare'),
            output_field=IntegerField()
        )
        total_greenhouse_period = ExpressionWrapper(
            F('seed__vegetation_mass_period') - settings.SERVICE_SILICA_PERIOD * F('method_silica') +
            F('seed__flowering_preharvest_period') - settings.SERVICE_BOTANICARE_PERIOD * F('method_botanicare') +
            F('seed__harvest_period'),
            output_field=IntegerField()
        )
        user_email = ExpressionWrapper(
            F('user__email'),
            output_field=EmailField()
        )
        queryset = queryset.annotate(
            vegetation_mass_period=vegetation_mass_period,
            flowering_preharvest_period=flowering_preharvest_period,
            current_period=ExpressionWrapper(
                ExtractDay(current_time - F('purchased_at')),
                output_field=IntegerField()
            ),
            user_email = user_email
        ).filter(
            current_period__lte=total_greenhouse_period
        )

        return queryset
    
class WareHouseListAPIView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    # queryset = SeedUser.objects.prefetch_related('seed_media')  # Add 'seed_media' prefetch
    queryset = SeedUser.objects.select_related('seed').prefetch_related('seed__seed_media')
    serializer_class = SeedUserSerializer
    search_fields = ['name']  # Specify the fields to search for
    def get_queryset(self):
        # user_id = self.request.GET.get('user_id')
        user_id = self.kwargs['user_id']
        if user_id:
            queryset = SeedUser.objects.filter(user_id=user_id)
        else:
            queryset = SeedUser.objects.all()
        sort_param = self.request.query_params.get('sort', None)
        if sort_param:
            # Determine the field and direction for sorting
            sort_fields = sort_param.split(',')
            ordering = []
            for field in sort_fields:
                if field.startswith('-'):
                    if field in ['-name', '-buy_price', '-harvest_rate']:
                        field = '-seed__' + field[1:]
                else:
                    if field in ['name', 'buy_price', 'harvest_rate']:
                        field = 'seed__' + field
                ordering.append(field.strip())

            # Apply sorting to the queryset
            queryset = queryset.order_by(*ordering)
        queryset = queryset.filter(seed__name__icontains=self.request.query_params.get('search', ''))
        queryset = queryset.filter(status=0) # Getting items which are status = 0 (greenhouse and warehouse)
        # Filter based on (vegetation_mass_period + flowering_preharvest_period + seed__harvest_period) > current_period
        current_time = timezone.now()
        vegetation_mass_period = ExpressionWrapper(
            F('seed__vegetation_mass_period') - settings.SERVICE_SILICA_PERIOD * F('method_silica'),
            output_field=IntegerField()
        )
        flowering_preharvest_period = ExpressionWrapper(
            F('seed__flowering_preharvest_period') - settings.SERVICE_BOTANICARE_PERIOD * F('method_botanicare'),
            output_field=IntegerField()
        )
        total_greenhouse_period = ExpressionWrapper(
            F('seed__vegetation_mass_period') - settings.SERVICE_SILICA_PERIOD * F('method_silica') +
            F('seed__flowering_preharvest_period') - settings.SERVICE_BOTANICARE_PERIOD * F('method_botanicare') +
            F('seed__harvest_period'),
            output_field=IntegerField()
        )
        queryset = queryset.annotate(
            current_period=ExpressionWrapper(
                ExtractDay(current_time - F('purchased_at')),
                output_field=IntegerField()
            )
        ).filter(
            current_period__gt=total_greenhouse_period
        )
        user_email = ExpressionWrapper(
            F('user__email'),
            output_field=EmailField()
        )
        queryset = queryset.annotate(
            vegetation_mass_period=vegetation_mass_period,
            flowering_preharvest_period=flowering_preharvest_period,
            warehouse_period=ExpressionWrapper(
                F('current_period') - total_greenhouse_period,
                output_field=IntegerField()
            ),
            user_email = user_email
        )
        return queryset

class SellHarvestAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    def post(self, request, seed_user_id, format=None):
        try:
            seed_user_row = SeedUser.objects.get(pk=seed_user_id)
            seed_user_row.status = 1
            seed_user_row.save()
            seed_order_item = SeedOrder(
                seed_id=seed_user_row.seed_id,
                user_id=seed_user_row.user_id,
                purchase_id=seed_user_row.id,
                status=0 # pending
            )
            seed_order_item.save()
        except (SeedUser.DoesNotExist):
            return Response({"type": "failure", "detail": "purchased seed does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'type':'success'}, status=status.HTTP_200_OK)
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['status'],
            properties={
                'status': openapi.Schema(type=openapi.TYPE_INTEGER)
            },
        ),
        responses={
            200: openapi.Response('OK'),
            400: openapi.Response('Bad Request'),
            403: openapi.Response('Forbidden'),
        }
    )
    def patch(self, request, seed_user_id, format=None):
        try:
            seed_order_item = SeedOrder.objects.get(pk=seed_user_id)
            user_profile_row = UserProfile.objects.filter(user_id=seed_order_item.user.pk).first()
            amount = seed_order_item.purchase.profit
            payment_method = seed_order_item.purchase.payment_method

            if (int(request.data.get('status')) == 1):                
                if (int(payment_method) == 0):
                    user_profile_row.pandami_balance = calc_round(user_profile_row.pandami_balance + amount)
                else:
                    user_profile_row.balance = calc_round(user_profile_row.balance + amount)
            elif ((int(request.data.get('status')) == 0 or int(request.data.get('status')) == 2) and seed_order_item.status == 1):
                # if previous status is success and current status is pending or rejected, user's balance should be decreased
                if (int(payment_method) == 0):
                    user_profile_row.pandami_balance = calc_round(user_profile_row.pandami_balance - amount)
                else:
                    user_profile_row.balance = calc_round(user_profile_row.balance - amount)

            user_profile_row.save()
            seed_order_item.status = request.data.get('status')      
            seed_order_item.save()
            notification_setting = NotificationSetting.objects.filter(type='Sell_Harvest').first()
            if (int(request.data.get('status')) == 1):
                action = 'confirmed'
            else:
                action = 'rejected'
            context = Context({
                'NAME': user_profile_row.user.username,
                'ACTION': action,  
                'BALANCE': user_profile_row.balance,
                'PGABALANCE': user_profile_row.pandami_balance
            })
            template = Template(notification_setting.content)
            content = template.render(context)
            send_websocket_data.apply_async(args=[user_profile_row.user.pk, {'type': 'Sell_Harvest', 'content': content}])
        except (SeedOrder.DoesNotExist, Seed.DoesNotExist, SeedUser.DoesNotExist, UserProfile.DoesNotExist):
            return Response({"type": "failure", "detail": "purchased seed does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'type':'success'}, status=status.HTTP_200_OK)
    
class SellOrderListAPIView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    serializer_class = SellOrderSerializer
    search_fields = ['name']  # Specify the fields to search for
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        if user_id:
            queryset = SeedOrder.objects.filter(user_id=user_id)
        else:
            queryset = SeedOrder.objects.all()
        sort_param = self.request.query_params.get('sort', None)
        if sort_param:
            # Determine the field and direction for sorting
            sort_fields = sort_param.split(',')
            ordering = []
            for field in sort_fields:
                if field.startswith('-'):
                    if field in ['-name', '-buy_price', '-harvest_rate']:
                        field = '-seed__' + field[1:]
                else:
                    if field in ['name', 'buy_price', 'harvest_rate']:
                        field = 'seed__' + field
                ordering.append(field.strip())

            # Apply sorting to the queryset
            queryset = queryset.order_by(*ordering)
        queryset = queryset.filter(seed__name__icontains=self.request.query_params.get('search', ''))
        # queryset = queryset.filter(status=0) # Getting items which are status = 0 (greenhouse and warehouse)
        # Filter based on (vegetation_mass_period + flowering_preharvest_period + seed__harvest_period) > current_period
        total_period = ExpressionWrapper(
            F('seed__vegetation_mass_period') - settings.SERVICE_SILICA_PERIOD * F('purchase__method_silica') +
            F('seed__flowering_preharvest_period') - settings.SERVICE_BOTANICARE_PERIOD * F('purchase__method_botanicare') +
            F('seed__harvest_period') + 
            F('seed__drying_period') + 
            F('seed__curing_period') + 
            F('seed__packing_period'),
            output_field=IntegerField()
        )
        vegetation_mass_period = ExpressionWrapper(
            F('seed__vegetation_mass_period') - settings.SERVICE_SILICA_PERIOD * F('purchase__method_silica'),
            output_field=IntegerField()
        )
        flowering_preharvest_period = ExpressionWrapper(
            F('seed__flowering_preharvest_period') - settings.SERVICE_BOTANICARE_PERIOD * F('purchase__method_botanicare'),
            output_field=IntegerField()
        )
        total_purchase = ExpressionWrapper(
            F('purchase__price_sum'),
            output_field=FloatField()
        )
        total_profit = ExpressionWrapper(
            F('purchase__profit'),
            output_field=FloatField()
        )
        harvest_amount = ExpressionWrapper(
            F('seed__harvest_rate') * F('purchase__purchased_amount') / 100,
            output_field=FloatField()
        )
        user_email = ExpressionWrapper(
            F('user__email'),
            output_field=EmailField()
        )
        user_name = ExpressionWrapper(
            F('user__username'),
            output_field=CharField()
        )
        payment_method = ExpressionWrapper(
            F('purchase__payment_method'),
            output_field=CharField()
        )
        queryset = queryset.annotate(
            vegetation_mass_period=vegetation_mass_period,
            flowering_preharvest_period=flowering_preharvest_period,
            total_period=total_period, 
            total_purchase = total_purchase, 
            total_profit = total_profit,
            harvest_amount = harvest_amount,
            user_email = user_email,
            user_name = user_name,
            payment_method=payment_method
        )
        
        return queryset