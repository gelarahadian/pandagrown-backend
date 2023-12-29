from channels.auth import get_user

from panda_backend.utils import PandaPagination, PandaListView, PandaUpdateView, PandaDeleteView, calc_round
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.core import serializers
from django.core.mail import EmailMessage, get_connection
from django.db.models import F, ExpressionWrapper, CharField, Subquery, OuterRef, EmailField, Sum
from django.http import HttpResponse
from django.http import HttpRequest
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template import Template, Context
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from user_agents import parse
import json

from base.models import EmailSetting
from basic_auth.authentication import JWTAuthentication
from payment.models import TransactionLog
from shop.models import SeedUser
from user.models import Referrer, UserProfile, UserAgent
from user.serializers import UserSerializer, UserAgentSerializer

User = get_user_model()

class UserListView(PandaListView):
    authentication_classes = [JWTAuthentication]
    ordering = [ '-is_superuser', 'is_supportuser', '-created_at']
    queryset = User.objects.order_by(*ordering).all()
    serializer_class = UserSerializer
    pagination_class = PandaPagination
    def list(self, request, *args, **kwargs): 
        self.pagination_class.page_size = request.query_params.get('page_size', self.pagination_class.page_size)
        queryset = self.filter_queryset(self.get_queryset())
        # Get the total count before pagination
        total_count = queryset.count()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data, total_count=total_count)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class UserListSupportView(PandaListView):
    authentication_classes = [JWTAuthentication]
    ordering = [ '-is_superuser', 'is_supportuser', '-created_at']
    queryset = User.objects.filter(is_superuser='f').order_by(*ordering).all()
    serializer_class = UserSerializer
    pagination_class = PandaPagination
    def list(self, request, *args, **kwargs):
        self.pagination_class.page_size = request.query_params.get('page_size', self.pagination_class.page_size)
        queryset = self.filter_queryset(self.get_queryset())
        # Get the total count before pagination
        total_count = queryset.count()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data, total_count=total_count)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class UserUpdateView(PandaUpdateView):
    authentication_classes = [JWTAuthentication]
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserDeleteView(PandaDeleteView):
    authentication_classes = [JWTAuthentication]
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ReferrLinkView(APIView):
    authentication_classes = [JWTAuthentication]
    def get(self, request, user_id, format=None):
        try:
            user = User.objects.get(pk=user_id)
            join_url = get_joinref_link(user)
            return HttpResponse(json.dumps({'type': 'success', 'link': join_url}), content_type='application/json; charset=utf-8')
        except(User.DoesNotExist):
            return HttpResponse(json.dumps({'type': 'failure'}), content_type='application/json; charset=utf-8') 

class ReferrsView(APIView):
    authentication_classes = [JWTAuthentication]
    def get(self, request, user_id, format=None):
        try:
            referr_name = ExpressionWrapper(
                F('user__username'),
                output_field=CharField()
            )
            referr_email = ExpressionWrapper(
                F('user__email'),
                output_field=EmailField()
            )
            referr_country = ExpressionWrapper(
                F('country'),
                output_field=CharField()
            )
            referrs = UserProfile.objects.annotate(referr_name = referr_name, referr_email=referr_email, referr_country = referr_country).filter(referer_id=user_id)
            result = []
            for referr in referrs:
                result.append({'name': referr.referr_name, 'referr_country': referr.referr_country, 'referr_email': referr.referr_email})
            return HttpResponse(json.dumps({'type': 'success', 'referrs': result}), content_type='application/json; charset=utf-8')
        except(User.DoesNotExist):
            return HttpResponse(json.dumps({'type': 'failure'}), content_type='application/json; charset=utf-8')    
        
class ReferrEmailView(APIView):
    authentication_classes = [JWTAuthentication]
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'friends': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                ),
            },
        ),
        responses={
            200: openapi.Response('OK'),
            400: openapi.Response('Bad Request'),
            403: openapi.Response('Forbidden'),
        }
    )
    def post(self, request, user_id, format=None):
        try:
            user = User.objects.get(pk=user_id)
            join_url = get_joinref_link(user)
            connection = get_connection()
            connection.debugging = True
            email_setting = EmailSetting.objects.filter(email_code='REFERRAL').first()
            if email_setting is None:
                return HttpResponse(json.dumps({'type': 'failure', 'detail': 'email setting does not exist'}), content_type='application/json; charset=utf-8')  
            friends = request.data.get('friends')
            for friend in friends:
                context = Context({
                    'USERNAME': friend['name'],
                    'REFERR_LINK': join_url,  
                    'REFERR_NAME': user.username
                })
                template = Template(email_setting.email_body)
                rendered_html = template.render(context)
                # Send verification email to user
                email = EmailMessage(
                    subject=email_setting.subject,
                    body=rendered_html,
                    from_email=settings.EMAIL_HOST_USER,
                    to=[friend['email']],
                    connection=connection
                )
                email.content_subtype = 'html'
                email.send()
            return HttpResponse(json.dumps({'type': 'success', 'link': join_url}), content_type='application/json; charset=utf-8')
        except(User.DoesNotExist):
            return HttpResponse(json.dumps({'type': 'failure', 'detail': 'user does not exist'}), content_type='application/json; charset=utf-8')  
class UserAgentViewSet(viewsets.ModelViewSet):
    queryset = UserAgent.objects.order_by('-id').all()
    serializer_class = UserAgentSerializer
    lookup_field = 'pk'
    http_method_names = ['get', 'post', 'head', 'put', 'delete', 'patch', 'partial_update']
    def get_serializer_class(self):
        return UserAgentSerializer
    def get_queryset(self):
        return UserAgent.objects.order_by('-id').all()
    def create(self, request, *args, **kwargs):
        ip, browser_info, url = get_user_agent(request)
        user_agent = {'ip': ip, 'browser_info': browser_info, 'url': url}
        user_agent = UserAgent(**user_agent)
        user_agent.save()
        return HttpResponse(json.dumps({'type': 'success'}), content_type='application/json; charset=utf-8')
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return HttpResponse(json.dumps({'type': 'success'}), content_type='application/json; charset=utf-8')
class UserReportView(APIView):
    authentication_classes = [JWTAuthentication]
    def get(self, request, user_id, format=None):
        try:
            # the usd balance which user own.
            user_profile = UserProfile.objects.filter(user_id=user_id).first()
            # the total of investment which was made by purchased seed.
            invest_fund = SeedUser.objects.filter(user_id=user_id, status=0).aggregate(sum_value=Sum(F('seed__buy_price') * F('purchased_amount')))['sum_value']
            # the total of profit from the purchased seeds
            total_profit = SeedUser.objects.filter(user_id=user_id, status=0).aggregate(sum_value=Sum(F('profit')))['sum_value']
            # the total of PGA which user used for purchasing items when he bought seed.
            total_silica_value = SeedUser.objects.filter(user_id=user_id, status=0).aggregate(sum_value=Sum(F('method_silica') * settings.SERVICE_SILICA_FEE))['sum_value']
            total_botanicare_value = SeedUser.objects.filter(user_id=user_id, status=0).aggregate(sum_value=Sum(F('method_botanicare') * settings.SERVICE_BOTANICARE_FEE))['sum_value']
            total_rhizo_value = SeedUser.objects.filter(user_id=user_id, status=0).aggregate(sum_value=Sum(F('method_rhizo') * settings.SERVICE_RHIZO_FEE))['sum_value']
            total_pga_purchased = total_silica_value + total_botanicare_value + total_rhizo_value
            # total of PGA deposits by user
            total_pga_deposit = TransactionLog.objects.filter(user_id=user_id, type_id=0, method=0, status=1).aggregate(sum_value=Sum(F('coin_amount')))['sum_value']
            # the total of user withdrawal PGA successfully
            total_pga_withdraw = TransactionLog.objects.filter(user_id=user_id, method=1, status=1, withdrawal_currency=0).aggregate(sum_value=Sum(F('coin_amount')))['sum_value']

            result = {'usd_balance': user_profile.balance, 'invest_fund': calc_round(invest_fund), 'total_profit': calc_round(total_profit), 'total_pga_purchased': calc_round(total_pga_purchased), 'total_pga_deposit': calc_round(total_pga_deposit), 'total_pga_withdraw': calc_round(total_pga_withdraw)}
            return HttpResponse(json.dumps({'type': 'success', 'data': result}), content_type='application/json; charset=utf-8')
        except(UserProfile.DoesNotExist):
            return HttpResponse(json.dumps({'type': 'failure', 'detail': 'bad request'}), content_type='application/json; charset=utf-8')


def get_current_page_url(request):
    # Use the request object to build the full URL
    current_url = request.build_absolute_uri()

    return current_url

def get_user_agent(request: HttpRequest):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # If the request is coming through a proxy server
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    url = get_current_page_url(request)
    # Get the user agent string from the request headers
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    # Parse the user agent string using the user-agents library
    user_agent = parse(user_agent_string)

    # Extract browser information
    browser_info = {
        'browser': user_agent.browser.family,
        'browser_version': user_agent.browser.version_string,
        'os': user_agent.os.family,
        'os_version': user_agent.os.version_string,
    }
    # return ip, user_agent.browser.family + user_agent.browser.version_string + user_agent.os.family + user_agent.os.version_string
    return ip, user_agent_string, url

def get_joinref_link(user):
    # Generate token for user
    # Encode user id for verification URL
    encoded_user_id = urlsafe_base64_encode(force_bytes(user.pk))
    join_url = f"{settings.HOST_URL}joinref/{encoded_user_id}/"
    return join_url