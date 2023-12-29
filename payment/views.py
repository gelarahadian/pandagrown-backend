from coinbase_commerce.client import Client
from coinbase_commerce.error import SignatureVerificationError, WebhookInvalidPayload
from coinbase_commerce.webhook import Webhook
from django.conf import settings
from django.db.models import F, Q, ExpressionWrapper, EmailField, CharField
from django.http import HttpResponse
from django.template import Template, Context
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from payment.models import TransactionLog
from base.models import CurrencySetting, EmailSetting
from django.db.models import Case, When, Value, CharField, F, Subquery
import logging
import os

from .serializers import TransactionLogSerializer
from basic_auth.authentication import JWTAuthentication
from base.models import NotificationSetting
from user.models import UserProfile
from panda_backend.async_tasks import send_websocket_data, send_email_task
from panda_backend.utils import calc_round


log_file_path = 'static/log.txt'  # Path to the log file

class DepositCoinbase(APIView):
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'amount',
            openapi.IN_QUERY,
            description='The deposit amount',
            type=openapi.TYPE_NUMBER
        )
    ])
    def get(self, request, user_id, format=None):
        client = Client(api_key=settings.COINBASE_COMMERCE_API_KEY)
        amount = request.query_params.get('amount')
        transaction_item = TransactionLog(
            user_id=user_id,
            amount=amount,
            method=0,
            type_id=1,
            status=0 # pending
        )
        transaction_item.save()
        product = {
            'name': 'Deposit',
            'description': 'Pandagrown Deposit.',
            'local_price': {
                'amount': amount,
                'currency': 'USD'
            },
            'pricing_type': 'fixed_price',
            'redirect_url': settings.HOST_URL + 'deposit/coinbase/success/' + str(amount) + '/',
            'cancel_url': settings.HOST_URL + 'deposit/coinbase/cancel/',
            'metadata': {
                'customer_id': user_id,
                'order_id': transaction_item.pk,
                'amount': amount,
            },
        }
        charge = client.charge.create(**product)
        return Response({'type':'success', 'url': charge.hosted_url}, status=status.HTTP_200_OK)

class DepositPandami(APIView):
    authentication_classes = [JWTAuthentication]
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'coin_amount',
            openapi.IN_QUERY,
            description='The deposit coin amount',
            type=openapi.TYPE_NUMBER
        ),
        openapi.Parameter(
            'address',
            openapi.IN_QUERY,
            description='wallet address',
            type=openapi.TYPE_STRING
        ),
    ])
    def post(self, request, user_id, format=None):
        try:
            coin_amount = float(request.data.get('coin_amount'))
            address = request.data.get('address')
            tx_hash = request.data.get('tx_hash')
            user_profile_row = UserProfile.objects.filter(user_id=user_id).first()
            user_profile_row.pandami_balance += calc_round(coin_amount)
            user_profile_row.save()
            transaction_item = TransactionLog(
                user_id=user_id,
                coin_amount=coin_amount,
                method=0,
                type_id=0,
                address=address,
                tx_hash=tx_hash,
                status=1 # success
            )
            transaction_item.save()
            notification_setting = NotificationSetting.objects.filter(type='Deposit_PGAToken').first()
            context = Context({
                'NAME': user_profile_row.user.username,
                'BALANCE': user_profile_row.pandami_balance
            })
            template = Template(notification_setting.content)
            content = template.render(context)
            send_websocket_data.apply_async(args=[user_profile_row.user.pk, {'type': 'Deposit_PGAToken', 'content': content}])

            email_seeting_deposit = EmailSetting.objects.filter(email_code='DEPOSIT').first()
            template_email = Template("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <!--[if !mso]><!-->
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <!--<![endif]-->
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title></title></head><body>
     """ + email_seeting_deposit.email_body + """ </body></html>""")
            context_email = Context(
                {
                    'BALANCE': coin_amount,
                    'UNIT': 'PGA'
                }
            )
            send_email_task.apply_async(args=[user_profile_row.user.email, email_seeting_deposit.subject, template_email.render(context_email)])

        except (UserProfile.DoesNotExist):
            return Response({'type':'failure', 'detail': 'user profile does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'type':'success'}, status=status.HTTP_200_OK)

class WebhookCoinbase(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = self.setup_logger()

    def setup_logger(self):
        log_file_dir = os.path.dirname(log_file_path)
        if not os.path.exists(log_file_dir):
            os.makedirs(log_file_dir)

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.ERROR)
        file_handler = logging.FileHandler(log_file_path)
        logger.addHandler(file_handler)

        return logger
    def post(self, request):
        request_data = request.body.decode('utf-8')
        request_sig = request.headers.get('X-CC-Webhook-Signature', None)
        webhook_secret = settings.COINBASE_COMMERCE_WEBHOOK_SHARED_SECRET

        try:
            event = Webhook.construct_event(request_data, request_sig, webhook_secret)

            user_id = event['data']['metadata']['customer_id']
            order_id = event['data']['metadata']['order_id']
            amount = event['data']['metadata']['amount']
            tx_hash = event['data']['hosted_url']
            user_profile = UserProfile.objects.filter(user_id=user_id).first()
            seed_order_item = TransactionLog.objects.get(pk=order_id)
            if event['type'] == 'charge:confirmed':
                seed_order_item.status = 1
                seed_order_item.tx_hash = tx_hash
                seed_order_item.save()
                user_profile.balance = calc_round(user_profile.balance + float(amount))
                user_profile.save()
                notification_setting = NotificationSetting.objects.filter(type='Deposit_Balance').first()
                context = Context({
                    'NAME': user_profile.user.username,
                    'BALANCE': user_profile.balance
                })
                template = Template(notification_setting.content)
                content = template.render(context)
                send_websocket_data.apply_async(args=[user_profile.user.pk, {'type': 'Deposit_Balance', 'content': content}])
                email_seeting_deposit = EmailSetting.objects.filter(email_code='DEPOSIT').first()
                template_email = Template("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <!--[if !mso]><!-->
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <!--<![endif]-->
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title></title></head><body>
     """ + email_seeting_deposit.email_body + """ </body></html>""")
                context_email = Context(
                    {
                        'BALANCE': amount,
                        'UNIT': 'USD'
                    }
                )
                send_email_task.apply_async(args=[user_profile.user.email, email_seeting_deposit.subject, template_email.render(context_email)])
            elif event['type'] == 'charge:cancelled':
                seed_order_item.status = 2
                seed_order_item.save()
            elif event['type'] == 'charge:failed':
                seed_order_item.status = 3
                seed_order_item.save()
            elif event['type'] == 'charge:pending':
                seed_order_item.status = 0
                seed_order_item.save()
        except (SignatureVerificationError, WebhookInvalidPayload, UserProfile.DoesNotExist, TransactionLog.DoesNotExist) as e:
            self.logger.exception(e)
            return HttpResponse(str(e), status=400)

        return HttpResponse('ok', status=200)

class TransactionLogAPIView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    serializer_class = TransactionLogSerializer
    def get_queryset(self):
        queryset = TransactionLog.objects.all()
        user_id = self.request.query_params.get('user_id', None)
        method_deposit = self.request.query_params.get('deposit', -1)
        method_withdraw = self.request.query_params.get('withdraw', -1)
        status = self.request.query_params.get('status', -1)
        or_conditions = []
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if int(method_deposit) == 1:
            or_conditions.append(Q(method=0))
        elif int(method_deposit) == 0:
            queryset = queryset.exclude(method=0)
        if int(method_withdraw) == 1:
            or_conditions.append(Q(method=1) & Q(status=1))
        elif int(method_withdraw) == 0:
            queryset = queryset.exclude(Q(method=1) & Q(status=1))
        if int(status) == 0:
            or_conditions.append(Q(method=1) & Q(status=0))
        elif int(status) == 1:
            queryset = queryset.exclude(Q(method=1) & Q(status=0))
        if or_conditions:
            combined_query = Q()
            for condition in or_conditions:
                combined_query |= condition
            # Execute the combined query
            queryset = queryset.filter(combined_query)
        user_email = ExpressionWrapper(
            F('user__email'),
            output_field=EmailField()
        )
        user_name = ExpressionWrapper(
            F('user__username'),
            output_field=CharField()
        )
        queryset = queryset.annotate(
            user_email = user_email,
            user_name = user_name,
        )
        queryset = queryset.extra(select={'name': 'SELECT name FROM currency_setting WHERE id = transaction_log.type_id'})
        queryset = queryset.extra(select={'icon': 'SELECT icon FROM currency_setting WHERE id = transaction_log.type_id'})
        queryset = queryset.extra(select={'unit': 'SELECT unit FROM currency_setting WHERE id = transaction_log.type_id'})
        return queryset
class RequestWithdraw(APIView):
    authentication_classes = [JWTAuthentication]
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'amount',
            openapi.IN_QUERY,
            description='The deposit amount',
            type=openapi.TYPE_NUMBER
        ),
        openapi.Parameter(
            'coin_amount',
            openapi.IN_QUERY,
            description='The deposit coin amount',
            type=openapi.TYPE_NUMBER
        ),
        openapi.Parameter(
            'currency',
            openapi.IN_QUERY,
            description='Coin type',
            type=openapi.TYPE_NUMBER
        ),
        openapi.Parameter(
            'address',
            openapi.IN_QUERY,
            description='wallet address',
            type=openapi.TYPE_STRING
        ),
    ])
    def post(self, request, user_id, format=None):
        try:
            amount = float(request.data.get('amount'))
            coin_amount = float(request.data.get('coin_amount'))
            balance_method = int(request.data.get('balance_method'))
            currency = request.data.get('currency')
            address = request.data.get('address')
            pga_price = float(request.data.get('pga_price'))
            user_profile_row = UserProfile.objects.filter(user_id=user_id).first()
            withdrawal_usd = amount
            if balance_method == 0:
                withdrawal_usd *= pga_price
            if (withdrawal_usd < settings.WITHDRAWAL_MIN):
                return Response({'type': 'failure', 'detail': 'your amount is less than min-withdrawal'},
                                status=status.HTTP_400_BAD_REQUEST)
            if (balance_method == 1):
                fee = settings.SERVICE_FEE
                if (user_profile_row.balance < amount):
                    return Response({'type': 'failure', 'detail': 'Lack of usd balance'},
                                    status=status.HTTP_400_BAD_REQUEST)
            else:
                fee = 0
                if (user_profile_row.pandami_balance < amount):
                    return Response({'type': 'failure', 'detail': 'Lack of pga balance'},
                                    status=status.HTTP_400_BAD_REQUEST)


            pending_rows_cnt = TransactionLog.objects.filter(user_id=user_id, method=1, status=0).count()
            if (pending_rows_cnt > 0):
                return Response({'type':'failure', 'detail': 'Duplicated of request. You can only request withdraw at once.'}, status=status.HTTP_400_BAD_REQUEST)
            transaction_item = TransactionLog(
                user_id=user_id,
                amount=calc_round(amount - fee),
                coin_amount=round(coin_amount * (1 - fee / amount), 6),
                withdrawal_currency=balance_method,
                type_id=currency,
                method=1,
                address=address,
                status=0 # pending
            )
            transaction_item.save()
        except (UserProfile.DoesNotExist):
            return Response({'type':'failure', 'detail': 'user profile does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'type':'success'}, status=status.HTTP_200_OK)

class ManageWithdraw(APIView):
    authentication_classes = [JWTAuthentication]
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
    def patch(self, request, transaction_log_id, format=None):
        try:
            transaction_log_item = TransactionLog.objects.get(pk=transaction_log_id)
            user_profile_row = UserProfile.objects.filter(user_id=transaction_log_item.user.pk).first()
            if (request.data.get('tx_link') == ''):
                return Response({'type':'failure', 'detail': 'Tx_hash must be set'}, status=status.HTTP_400_BAD_REQUEST)

            if (int(request.data.get('status')) == 1):
                if (int(transaction_log_item.withdrawal_currency) == 1):
                    amount = float(transaction_log_item.amount) + float(settings.SERVICE_FEE)
                    user_profile_row.balance = calc_round((float)(user_profile_row.balance) - (float)(amount))
                else:
                    amount = float(transaction_log_item.amount)
                    user_profile_row.pandami_balance = calc_round((float)(user_profile_row.pandami_balance) - (float)(amount))

            elif ((int(request.data.get('status')) == 0 or int(request.data.get('status')) == 2) and transaction_log_item.status == 1):
                # if previous status is success and current status is pending or rejected, user's balance should be increased
                if (int(transaction_log_item.withdrawal_currency) == 1):
                    amount = float(transaction_log_item.amount) + float(settings.SERVICE_FEE)
                    user_profile_row.balance = calc_round((float)(user_profile_row.balance) + (float)(amount))
                else:
                    amount = float(transaction_log_item.amount)
                    user_profile_row.pandami_balance = calc_round((float)(user_profile_row.pandami_balance) + (float)(amount))
            user_profile_row.save()
            transaction_log_item.status = request.data.get('status')
            transaction_log_item.tx_hash = request.data.get('tx_link')
            transaction_log_item.save()
            # to get notification setting and to render notification content(websocket client data content)
            notification_setting = NotificationSetting.objects.filter(type='Withdraw').first()
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
            send_websocket_data.apply_async(args=[user_profile_row.user.pk, {'type': 'Withdraw', 'content': content}])

            email_setting_withdrawal = EmailSetting.objects.filter(email_code='WITHDRAWAL').first()
            template_email = Template("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <!--[if !mso]><!-->
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <!--<![endif]-->
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title></title></head><body>
     """ + email_setting_withdrawal.email_body + """ </body></html>""")
            currency = CurrencySetting.objects.filter(id=transaction_log_item.type_id).first()
            context_email = Context(
                {
                    'AMOUNT': transaction_log_item.coin_amount,
                    'UNIT': currency.unit,
                    'ADDRESS': transaction_log_item.address,
                    'TX_LINK': transaction_log_item.tx_hash,
                    'TX_SHORT': transaction_log_item.tx_hash[0:30] + '...'
                }
            )
            send_email_task.apply_async(
                args=[user_profile_row.user.email, email_setting_withdrawal.subject, template_email.render(context_email)])

        except (TransactionLog.DoesNotExist, UserProfile.DoesNotExist):
            return Response({"type": "failure", "detail": "transaction log does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except (NotificationSetting.DoesNotExist):
            return Response({"type": "failure", "detail": "notification setting does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'type':'success'}, status=status.HTTP_200_OK)
