from rest_framework import generics, status
from shop.models import SeedCart, Seed, SeedUser
from user.models import UserProfile
from django.contrib.auth import get_user_model
from django.conf import settings
from base.models import EmailSetting
from shop.serializers import SeedCartSerializer
from base.models import NotificationSetting
from rest_framework.views import APIView
from basic_auth.authentication import JWTAuthentication
from panda_backend.utils import calc_profit, calc_round, calc_bonus
from rest_framework.response import Response
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
from panda_backend.async_tasks import send_email_task, send_websocket_data
from django.template import Template, Context

User = get_user_model()

class CartListCreateAPIView(generics.ListCreateAPIView):
    authentication_classes = [JWTAuthentication]
    queryset = SeedCart.objects.all()
    serializer_class = SeedCartSerializer
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        if user_id:
            queryset = SeedCart.objects.filter(user_id=user_id)
        else:
            queryset = SeedCart.objects.all()
        return queryset

    def get_permissions(self):
        if self.request.method == 'POST':
            # Apply custom authentication only for POST
            return [JWTAuthentication()]
        else:
            # Use default authentication for other methods
            return super().get_permissions()
    def create(self, request, *args, **kwargs):
        seed_id = request.data.get('seed')
        amount = request.data.get('purchased_amount')
        payment_method = request.data.get('payment_method')
        price_sum = request.data.get('price_sum')
        seed_row = Seed.objects.get(pk=seed_id)
        if seed_row.stock < amount:
            return Response({"type": "failure", "detail": "lack of stock"}, status=status.HTTP_400_BAD_REQUEST)    
        # Call the base create() method to perform the default creation process
        return super().create(request, *args, **kwargs)

class CartRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = SeedCart.objects.all()
    serializer_class = SeedCartSerializer
    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT']:
            # Apply custom authentication only for PATCH, PUT
            return [JWTAuthentication()]
        else:
            # Use default authentication for other actions
            return super().get_permissions()
    def patch(self, request, *args, **kwargs):
        seed_id = request.data.get('seed')
        amount = request.data.get('purchased_amount')
        seed_row = Seed.objects.get(pk=seed_id)
        if seed_row.stock < amount:
            return Response({"type": "failure", "detail": "lack of stock"}, status=status.HTTP_400_BAD_REQUEST)    
        # Call the base patch() method to perform the default creation process
        return super().patch(request, *args, **kwargs)
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'type': 'success'}, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        instance.delete()

class PurchaseAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    def post(self, request, user_id, format=None):
        try:
            user_row = User.objects.get(pk=user_id)
            cart_rows = SeedCart.objects.filter(user_id=user_id)
            total_value = cart_rows.filter(payment_method=1).aggregate(sum_value=Sum(F('price_sum')))['sum_value'] or 0
            total_silica_value = cart_rows.filter(payment_method=1).aggregate(sum_value=Sum(F('method_silica') * settings.SERVICE_SILICA_FEE))['sum_value'] or 0
            total_botanicare_value = cart_rows.filter(payment_method=1).aggregate(sum_value=Sum(F('method_botanicare') * settings.SERVICE_BOTANICARE_FEE))['sum_value'] or 0
            total_rhizo_value = cart_rows.filter(payment_method=1).aggregate(sum_value=Sum(F('method_rhizo') * settings.SERVICE_RHIZO_FEE))['sum_value'] or 0
            total_pga_value = (cart_rows.filter(payment_method=0).aggregate(sum_value=Sum(F('price_sum')))['sum_value'] or 0) + (total_silica_value or 0) + (total_botanicare_value or 0) + (total_rhizo_value or 0)


            user_profile_row = UserProfile.objects.filter(user_id=user_id).first()
            if (user_profile_row.balance < total_value):
                return Response({"type": "failure", "detail": "lack of balance"}, status=status.HTTP_400_BAD_REQUEST)    
            if user_profile_row.pandami_balance < total_pga_value:
                return Response({"type": "failure", "detail": "lack of PGA balance"}, status=status.HTTP_400_BAD_REQUEST)    
            lack_stock_detail_list = []
            for cart_item in cart_rows:
                seed_row = Seed.objects.get(pk=cart_item.seed_id)
                cart_item.delete()
                if seed_row.stock < cart_item.purchased_amount:
                    lack_stock_detail_list.append(seed_row.name + ' is insufficient now')
                    continue

                # calculate profit according to payment method
                if ((int)(cart_item.payment_method) == 1):
                    invest_price = seed_row.buy_price * cart_item.purchased_amount
                    profit = (1 + settings.SERVICE_RHIZO_PERCENT * cart_item.method_rhizo / 100 + calc_bonus(invest_price, 1)) * invest_price
                else:
                    invest_price = calc_round((cart_item.price_sum - settings.SERVICE_RHIZO_FEE * cart_item.method_rhizo - settings.SERVICE_BOTANICARE_FEE * cart_item.method_botanicare - settings.SERVICE_SILICA_FEE * cart_item.method_silica) / 0.9)
                    profit = calc_round((1 + settings.SERVICE_RHIZO_PERCENT * cart_item.method_rhizo / 100 + calc_bonus(invest_price, 0)) * invest_price)

                vegetation_mass_period = seed_row.vegetation_mass_period - settings.SERVICE_SILICA_PERIOD * cart_item.method_silica
                flowering_preharvest_period = seed_row.flowering_preharvest_period - settings.SERVICE_BOTANICARE_PERIOD * cart_item.method_botanicare

                purchased_item = SeedUser(
                    seed_id=cart_item.seed_id,
                    user_id=cart_item.user_id,
                    purchased_amount=cart_item.purchased_amount,
                    profit=profit,
                    method_silica=cart_item.method_silica,
                    method_botanicare=cart_item.method_botanicare,
                    method_rhizo=cart_item.method_rhizo,
                    payment_method=cart_item.payment_method,
                    price_sum=cart_item.price_sum,
                    status=0,  # purchased_item
                    est_harvest_at=timezone.now() + timedelta(vegetation_mass_period
                                   +flowering_preharvest_period
                                   +seed_row.harvest_period
                                   +seed_row.drying_period
                                   + seed_row.curing_period
                                   + seed_row.packing_period)
                )
                scheduled_time = timezone.now() + timedelta(seconds=10) 
                cur_period = 0
                type = 'Purchase'
                content = self.render_seed_notification_setting(type, seed_row.name)
                send_websocket_data.apply_async(args=[user_id, {'type': type, 'content': content}])

                # when vegetation_mass_period, this service will send message to user
                cur_period += vegetation_mass_period
                scheduled_time = timezone.now() + timedelta(days=cur_period) 
                subject, rendered_html = self.render_seed_email_setting('GREENHOUSE', user_profile_row.user.username, seed_row.name, 'Vegetation Mass Period')
                content = self.render_seed_step_notification_setting('GREENHOUSE', user_profile_row.user.username, seed_row.name, 'Vegetation Mass Period')
                send_email_task.apply_async(args=[user_row.email, subject, rendered_html], eta=scheduled_time)
                send_websocket_data.apply_async(args=[user_id, {'type': 'Seed_Step', 'content': content}], eta=scheduled_time)

                # when flowering_preharvest_period, this service will send message to user
                cur_period += flowering_preharvest_period
                scheduled_time = timezone.now() + timedelta(days=cur_period) 
                subject, rendered_html = self.render_seed_email_setting('GREENHOUSE', user_profile_row.user.username, seed_row.name, 'Flowering Preharvest Period')
                content = self.render_seed_step_notification_setting('GREENHOUSE', user_profile_row.user.username, seed_row.name, 'Flowering Preharvest Period')
                send_email_task.apply_async(args=[user_row.email, subject, rendered_html], eta=scheduled_time)
                send_websocket_data.apply_async(args=[user_id, {'type': 'Seed_Step', 'content': content}], eta=scheduled_time)

                # when harvest_period, this service will send message to user
                cur_period += seed_row.harvest_period
                scheduled_time = timezone.now() + timedelta(days=cur_period) 
                subject, rendered_html = self.render_seed_email_setting('GREENHOUSE', user_profile_row.user.username, seed_row.name, 'Harvest Period')
                content = self.render_seed_step_notification_setting('GREENHOUSE', user_profile_row.user.username, seed_row.name, 'Harvest Period')
                send_email_task.apply_async(args=[user_row.email, subject, rendered_html], eta=scheduled_time)
                send_websocket_data.apply_async(args=[user_id, {'type': 'Seed_Step', 'content': content}], eta=scheduled_time)
                
                # when drying_period, this service will send message to user
                cur_period += seed_row.drying_period
                scheduled_time = timezone.now() + timedelta(days=cur_period) 
                subject, rendered_html = self.render_seed_email_setting('WAREHOUSE', user_profile_row.user.username, seed_row.name, 'Drying Period')
                content = self.render_seed_step_notification_setting('GREENHOUSE', user_profile_row.user.username, seed_row.name, 'Drying Period')
                send_email_task.apply_async(args=[user_row.email, subject, rendered_html], eta=scheduled_time)
                send_websocket_data.apply_async(args=[user_id, {'type': 'Seed_Step', 'content': content}], eta=scheduled_time)

                # when curing_period, this service will send message to user
                cur_period += seed_row.curing_period
                scheduled_time = timezone.now() + timedelta(days=cur_period) 
                subject, rendered_html = self.render_seed_email_setting('WAREHOUSE', user_profile_row.user.username, seed_row.name, 'Curing Period')
                content = self.render_seed_step_notification_setting('GREENHOUSE', user_profile_row.user.username, seed_row.name, 'Curing Period')
                send_email_task.apply_async(args=[user_row.email, subject, rendered_html], eta=scheduled_time)
                send_websocket_data.apply_async(args=[user_id, {'type': 'Seed_Step', 'content': content}], eta=scheduled_time)

                # when packing_period, this service will send message to user
                cur_period += seed_row.packing_period
                scheduled_time = timezone.now() + timedelta(days=cur_period) 
                subject, rendered_html = self.render_seed_email_setting('WAREHOUSE', user_profile_row.user.username, seed_row.name, 'Packing Period')
                content = self.render_seed_step_notification_setting('GREENHOUSE', user_profile_row.user.username, seed_row.name, 'Pakcing Period')
                send_email_task.apply_async(args=[user_row.email, subject, rendered_html], eta=scheduled_time)
                send_websocket_data.apply_async(args=[user_id, {'type': 'Seed_Step', 'content': content}], eta=scheduled_time)

                purchased_item.save()
                seed_row.stock = calc_round(seed_row.stock - cart_item.purchased_amount)
                seed_row.purchased_count = calc_round(seed_row.purchased_count + cart_item.purchased_amount)
                seed_row.save()
            user_profile_row.balance = calc_round(user_profile_row.balance - total_value)
            user_profile_row.pandami_balance = calc_round(user_profile_row.pandami_balance - total_pga_value)
            user_profile_row.save()
        except (SeedCart.DoesNotExist):
            return Response({"type": "failure", "detail": "cart does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except (Seed.DoesNotExist):
            return Response({"type": "failure", "detail": "seed does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'type':'success', 'balance': user_profile_row.balance, 'pga_balance': user_profile_row.pandami_balance}, status=status.HTTP_200_OK)
    def render_seed_notification_setting(self, type, seed_name):
        notification_setting = NotificationSetting.objects.filter(type=type).first()
        context = Context({
            'SEED_NAME': seed_name,
        })
        template = Template(notification_setting.content)
        return template.render(context)
    def render_seed_step_notification_setting(self, house, user_name, seed_name, step):
        notification_setting = NotificationSetting.objects.filter(type='Seed_Step').first()
        template = Template(notification_setting.content)
        context = Context({
            'HOUSE': house,
            'NAME':  user_name,
            'SEED_NAME': seed_name,
            'STEP': step
        })
        return template.render(context)
    def render_seed_email_setting(self, house, user_name, seed_name, step):
        email_setting_house = EmailSetting.objects.filter(email_code='SEED_STEP').first()
        template = Template("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <!--[if !mso]><!-->
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <!--<![endif]-->
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title></title></head><body>
     """ + email_setting_house.email_body + """ </body></html>""")
        context = Context({
            'HOUSE': house,
            'NAME':  user_name,
            'SEED_NAME': seed_name,
            'STEP': step
        })
        return email_setting_house.subject, template.render(context)
