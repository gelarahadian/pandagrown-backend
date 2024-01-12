import csv
import os
from datetime import time
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage, get_connection
from django.db.models import Sum, F, ExpressionWrapper, EmailField, CharField, Q
from django.http import HttpResponse
from django.http import HttpRequest
from django.template import Template, Context
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import views, permissions, status
import json
from time import time

from payment.models import TransactionLog
from .serializers import ObtainTokenSerializer
from base.models import EmailSetting
from basic_auth.authentication import JWTAuthentication
from panda_backend.utils import PandaPagination, PandaListView, PandaUpdateView, calc_round
from shop.models import SeedUser
from user.models import UserProfile
from user.serializers import UserSerializer
from websocket_app.models import Notifications
import logging
logger = logging.getLogger(__name__)

User = get_user_model()
class AdminBackupView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ObtainTokenSerializer
    @swagger_auto_schema(
        request_body=ObtainTokenSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response('OK', ObtainTokenSerializer),
            status.HTTP_400_BAD_REQUEST: openapi.Response('Bad Request'),
        }
    )
    def save_user_csv(request, queryset):
        model = queryset.model
        model_fields = model._meta.fields + model._meta.many_to_many
        field_names = ['id', 'user_email', 'user_name', 'balance',  'pandami_balance']

        userfilePath = 'static/users' + str(int(time()) * 1000) + '.csv'
        with open(userfilePath, mode='w+') as user_file:
            # the csv writer
            writer = csv.writer(user_file, delimiter=";")
            # Write a first row with header information
            writer.writerow(field_names)
            # Write data rows
            for row in queryset:
                values = []
                for field in field_names:
                    value = getattr(row, field)
                    if callable(value):
                        try:
                            value = value() or ''
                        except:
                            value = 'Error retrieving value'
                    if value is None:
                        value = ''
                    values.append(value)
                writer.writerow(values)
        return 'ok'
    def save_seed_user_csv(request, queryset):
        model = queryset.model
        model_fields = model._meta.fields + model._meta.many_to_many
        field_names = ['user_email', 'seed_name', 'purchased_amount', 'purchased_at',  'method_silica', 'method_botanicare', 'method_rhizo']

        userfilePath = 'static/user_seeds' + str(int(time()) * 1000) + '.csv'
        with open(userfilePath, mode='w+') as user_file:
            # the csv writer
            writer = csv.writer(user_file, delimiter=";")
            # Write a first row with header information
            writer.writerow(field_names)
            # Write data rows
            for row in queryset:
                values = []
                for field in field_names:
                    value = getattr(row, field)
                    if callable(value):
                        try:
                            value = value() or ''
                        except:
                            value = 'Error retrieving value'
                    if value is None:
                        value = ''
                    values.append(value)
                writer.writerow(values)
        return 'ok'
    def save_tx_user_csv(request, queryset):
        model = queryset.model
        model_fields = model._meta.fields + model._meta.many_to_many
        field_names = [ 'user_email', 'amount', 'coin_amount', 'created_at', 'tx_hash']

        userfilePath = 'static/user_deposits' + str(int(time()) * 1000) + '.csv'
        with open(userfilePath, mode='w+') as user_file:
            # the csv writer
            writer = csv.writer(user_file, delimiter=";")
            # Write a first row with header information
            writer.writerow(field_names)
            # Write data rows
            for row in queryset:
                values = []
                for field in field_names:
                    value = getattr(row, field)
                    if callable(value):
                        try:
                            value = value() or ''
                        except:
                            value = 'Error retrieving value'
                    if value is None:
                        value = ''
                    values.append(value)
                writer.writerow(values)
        return 'ok'
    def post(self, request, *args, **kwargs):
        queryset = UserProfile.objects.all();
        user_email = ExpressionWrapper(
            F('user__email'),
            output_field=EmailField()
        )
        user_name = ExpressionWrapper(
            F('user__username'),
            output_field=CharField()
        )
        queryset = queryset.annotate(
            user_email=user_email,
            user_name=user_name,
        )
        data = self.save_user_csv(queryset)

        queryset1 = SeedUser.objects.all()
        seed_name = ExpressionWrapper(
            F('seed__name'),
            output_field=CharField()
        )
        queryset1 = queryset1.annotate(
            seed_name=seed_name,
            user_email=user_email,
            user_name=user_name
        )
        data1 = self.save_seed_user_csv(queryset1)

        queryset2 = TransactionLog.objects.all()
        or_conditions = []
        or_conditions.append(Q(method=0))
        if or_conditions:
            combined_query = Q()
            for condition in or_conditions:
                combined_query |= condition
            # Execute the combined query
            queryset2 = queryset2.filter(combined_query)
        user_email = ExpressionWrapper(
            F('user__email'),
            output_field=EmailField()
        )
        user_name = ExpressionWrapper(
            F('user__username'),
            output_field=CharField()
        )
        queryset2 = queryset2.annotate(
            user_email=user_email,
            user_name=user_name,
        )
        data2 = self.save_tx_user_csv(queryset2)
        response = HttpResponse(data, content_type='text/csv')
        return response
class AdminLoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ObtainTokenSerializer
    @swagger_auto_schema(
        request_body=ObtainTokenSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response('OK', ObtainTokenSerializer),
            status.HTTP_400_BAD_REQUEST: openapi.Response('Bad Request'),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        user = get_superuser_by_email(email)
        if user is None:
            return Response({'type': 'failure', 'message': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(password):
            return Response({'type': 'failure', 'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        if user.status != 1:
            return Response({'type': 'failure', 'message': 'User is not active'}, status=status.HTTP_400_BAD_REQUEST)
        # Generate the JWT token
        jwt_token = JWTAuthentication.create_jwt(user)
        update_user_login_state(user, request, 1)
        return Response({'type': 'success', 'token': jwt_token})
class SupportAdminLoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ObtainTokenSerializer

    @swagger_auto_schema(
        request_body=ObtainTokenSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response('OK', ObtainTokenSerializer),
            status.HTTP_400_BAD_REQUEST: openapi.Response('Bad Request'),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        user = get_supportuser_by_email(email)
        if user is None:
            return Response({'type': 'failure', 'message': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(password):
            return Response({'type': 'failure', 'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        if user.status != 1:
            return Response({'type': 'failure', 'message': 'User is not active'}, status=status.HTTP_400_BAD_REQUEST)
        # Generate the JWT token
        jwt_token = JWTAuthentication.create_jwt(user)
        update_user_login_state(user, request, 1)
        return Response({'type': 'success', 'token': jwt_token})
class UserLoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ObtainTokenSerializer
    @swagger_auto_schema(
        request_body=ObtainTokenSerializer,
        responses={
            200: openapi.Response('OK', ObtainTokenSerializer),
            400: openapi.Response('Bad Request'),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        user = User.objects.filter(email=email).first()
        
        if user is None:
            return Response({'type': 'failure', 'message': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(password):
            return Response({'type': 'failure', 'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        if user.status == 2:
            return Response({'type': 'failure', 'message': 'User is not active', 'user_id': user.id}, status=status.HTTP_400_BAD_REQUEST)
        if user.status == 3:
            return Response({'type': 'failure', 'message': 'User is suspended', 'user_id': user.id}, status=status.HTTP_400_BAD_REQUEST)
        # Generate the JWT token
        response_data = update_user_login_state(user, request, 0)
        return HttpResponse(response_data, content_type='application/json; charset=utf-8')
    
# register user
class UserRegisterView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'email', 'password'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Response('OK'),
            400: openapi.Response('Bad Request'),
            403: openapi.Response('Forbidden'),
        }
    )
    def post(self, request, referr_id=None, format=None):
        data = request.data # holds username and password (in dictionary)
        username = data["name"]
        email = data["email"]

        if username == "" or email == "":
            return Response({"type": "failure", "detail": "username or email cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        else:
            check_email =  User.objects.filter(email=email).count()
            if check_email:
                message = "A user with that email address already exist!"
                return Response({"type": "failure", "detail": message}, status=status.HTTP_403_FORBIDDEN)
            else:
                user = {"email": email, "password": make_password(data["password"]), 'username': username, "first_name": username, "status": 2}
                user = User(**user)
                user.save()
                profile = { 'user_id': user.pk, 'balance': 0, 'pandami_balance': 0}
                if referr_id is not None:
                    referr_id = force_str(urlsafe_base64_decode(referr_id))
                    profile = { 'user_id': user.pk, 'balance': 0, 'referer_id': referr_id}
                    referer = UserProfile.objects.filter(user_id=referr_id).first()
                    referer.pandami_balance = referer.pandami_balance + 50
                    referer.save()
                profile = UserProfile(**profile)
                profile.save()
                if send_verify_email(user, 'SIGNUP') == True:
                    return Response({'type':'success', 'user_id': user.id, 'profile_id': profile.id}, status=status.HTTP_200_OK)
                else:
                    return Response({'type':'failure', 'detail': 'email setting is not set up'}, status=status.HTTP_200_OK)

class UserListView(PandaListView):
    authentication_classes = [JWTAuthentication]
    queryset = User.objects.all()
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
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserVerifyEmailView(APIView):
    def post(self, request):
        User = get_user_model()
        user_id = request.data['user_id']
        token = request.data['token']
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(user_id)))
            if user.activation_code == token:
                user.email_verified_at = timezone.now()
                user.status = 1
                user.save()
                response_data = update_user_login_state(user, request, 0)
                return HttpResponse(response_data, content_type='application/json; charset=utf-8')
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            pass
        return HttpResponse('Invalid verification link')

class UserVerificationEmailView(APIView):
    def set_activation_code(user, token):
        user.activation_code = token
        user.save()
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_id'],
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        ),
        responses={
            200: openapi.Response('OK'),
            400: openapi.Response('Bad Request'),
            403: openapi.Response('Forbidden'),
        }
    )
    def post(self, request):
        user_id = request.data['user_id']
        user = User.objects.get(pk=user_id)
        if user.email_verified_at is not None:
            return Response({'type':'failure', 'detail': 'You have been already signed up'}, status=status.HTTP_200_OK)
        difference_time = timezone.now() - user.updated_at
        if difference_time.seconds < settings.SERVICE_EMAIL_RESEND_TIME_SECONDS:
            return Response({'type':'failure', 'detail': 'You can resend email after ' + str(settings.SERVICE_EMAIL_RESEND_TIME_SECONDS - difference_time.seconds) + 's.'}, status=status.HTTP_200_OK)
        if send_verify_email(user, 'SIGNUP') == True:
            return Response({'type':'success'}, status=status.HTTP_200_OK)
        else:
            return Response({'type':'failure', 'detail': 'email setting is not set up'}, status=status.HTTP_200_OK)
    
class TokenVerifyView(APIView):
    def post(self, request):
        return Response({'valid': True}, status=200)

class RefreshTokenView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['is_refresh_token'],
            properties={
                'is_refresh_token': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            },
        ),
        responses={
            200: openapi.Response('OK'),
            400: openapi.Response('Bad Request'),
            403: openapi.Response('Forbidden'),
        }
    )
    def post(self, request):
        user, payload = JWTAuthentication().authenticate(request)
        return Response({'valid': True, 'token': JWTAuthentication.create_jwt(user), 'refresh_token': JWTAuthentication.create_jwt(user, True)} , status=200)
    
class ResetPasswordView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_id', 'password'],
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Response('OK'),
            400: openapi.Response('Bad Request'),
            403: openapi.Response('Forbidden'),
        }
    )
    def post(self, request):
        User = get_user_model()
        user = User.objects.get(pk=request.data['user_id'])
        user.password = make_password(request.data['password'])
        user.save()
        return Response({'type':'success'}, status=status.HTTP_200_OK)

class ForgotPasswordVerifyView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_id', 'token'],
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'token': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Response('OK'),
            400: openapi.Response('Bad Request'),
            403: openapi.Response('Forbidden'),
        }
    )
    def post(self, request):
        User = get_user_model()
        user_id = request.data['user_id']
        token = request.data['token']
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(user_id)))
            if user.forgot_password_code == token:
                profile = UserProfile.objects.filter(user_id=user.id).first()
                return Response({'type':'success', 'user_id': user.id, 'profile_id': profile.id}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            pass
        
        return HttpResponse('Invalid verification link')
    
class ForgotPasswordView(APIView):
    def set_forgot_password_code(user, token):
        user.forgot_password_code = token
        user.save()
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Response('OK'),
            400: openapi.Response('Bad Request'),
            403: openapi.Response('Forbidden'),
        }
    )
    def post(self, request):
        # user_id = force_str(urlsafe_base64_decode(request.data['user_id']))
        user_email = request.data['email']
        user = User.objects.get(email=user_email)
        difference_time = timezone.now() - user.updated_at
        if difference_time.seconds < settings.SERVICE_EMAIL_RESEND_TIME_SECONDS:
            return Response({'type':'failure', 'detail': 'You can resend email after ' + str(settings.SERVICE_EMAIL_RESEND_TIME_SECONDS - difference_time.seconds) + 's.'}, status=status.HTTP_200_OK)
        if send_verify_email(user, 'FORGOT_PASSWORD') == True:
            return Response({'type':'success'}, status=status.HTTP_200_OK)
        else:
            return Response({'type':'failure', 'detail': 'Email setting is not set up'}, status=status.HTTP_200_OK)
    
def send_verify_email(user, email_code):
    # Generate token for user
    token = default_token_generator.make_token(user)
    
    # Encode user id for verification URL
    encoded_user_id = urlsafe_base64_encode(force_bytes(user.pk))
    # Get email setting for verification email
    email_setting = EmailSetting.objects.filter(email_code=email_code).first()
    if email_setting is None:
        return False
    # Construct verification URL with token and encoded user id
    if email_code == 'SIGNUP':
        context = Context({
            'LASTNAME': user.username,
            'VERIFY_LINK': f"{settings.HOST_URL}verify/{encoded_user_id}/{token}/",  
        })
        user.activation_code = token
        user.save()
    elif email_code == 'FORGOT_PASSWORD':
        context = Context({
            'LASTNAME': user.username,
            'RESET_LINK': f"{settings.HOST_URL}password-reset/{encoded_user_id}/{token}/",
            
        })
        user.forgot_password_code = token
        user.save()
    # Render email body HTML template with verification URL

    connection = get_connection()
    connection.debugging = True
    email_header = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <!--[if !mso]><!-->
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <!--<![endif]-->
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title></title>
  <style type="text/css">
.ReadMsgBody { width: 100%; background-color: #ffffff; }
.ExternalClass { width: 100%; background-color: #ffffff; }
.ExternalClass, .ExternalClass p, .ExternalClass span, .ExternalClass font, .ExternalClass td, .ExternalClass div { line-height: 100%; }
html { width: 100%; }
body { -webkit-text-size-adjust: none; -ms-text-size-adjust: none; margin: 0; padding: 0; }
table { border-spacing: 0; table-layout: fixed; margin: 0 auto;border-collapse: collapse; }
table table table { table-layout: auto; }
.yshortcuts a { border-bottom: none !important; }
img:hover { opacity: 0.9 !important; }
a { color: #ff646a; text-decoration: none; }
.textbutton a { font-family: \'open sans\', arial, sans-serif !important;}
.btn-link a { color:#FFFFFF !important;}
.mainbtn a {text-decoration-line: none; background: rgb(5, 144, 51); color: rgb(255, 255, 255); padding: 10px 30px; border-radius: 20px; cursor: pointer;}
@media only screen and (max-width: 480px) {
body { width: auto !important; }
*[class="table-inner"] { width: 90% !important; text-align: center !important; }
*[class="table-full"] { width: 100% !important; text-align: center !important; }
/* image */
img[class="img1"] { width: 100% !important; height: auto !important; }
}
</style>
</head>

<body>
  <table bgcolor="#f2f2f2" width="100%" border="0" align="center" cellpadding="0" cellspacing="0">
    <tr>
      <td height="50"></td>
    </tr>
    <tr>
      <td align="center" style="text-align:center;vertical-align:top;font-size:0;">
        <table align="center" border="0" cellpadding="0" cellspacing="0">
          <tr>
            <td align="center" width="500">
              
              <table class="table-inner" width="95%" border="0" align="center" cellpadding="0" cellspacing="0">
                <tr>
                  <td bgcolor="#059033" style="border-top-left-radius:6px; border-top-right-radius:6px;text-align:center;vertical-align:top;font-size:0;" align="center">
                    <table width="90%" border="0" align="center" cellpadding="0" cellspacing="0">
                      <tr>
                        <td height="20"></td>
                      </tr>
                      <tr>
                        <td height="20"></td>
                      </tr>
                      <tr>
                        <td height="20"></td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
              
              """
    email_footer = """<table align="center" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td height="20"></td>
                </tr>               
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    <tr>
      <td height="30"></td>
    </tr>
  </table>
</body>

</html>"""
    main_body = """<table class="table-inner" width="95%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td bgcolor="#FFFFFF" align="center" style="font-family: \'Open Sans\', Arial, sans-serif; color:#3b3b3b; font-size:14px; letter-spacing: 0.5px;"><table align="center" width="90%" border="0" cellspacing="0" cellpadding="0">
                      <tr>
                        <td>""" + email_setting.email_body + """</td>
                      </tr></table>
                  </td>
                </tr>
                <tr>
                  <td height="45" align="center" bgcolor="#f4f4f4" style="border-bottom-left-radius:6px;border-bottom-right-radius:6px;">
                    <table align="center" width="90%" border="0" cellspacing="0" cellpadding="0">
                      <tr>
                        <td height="10"></td>
                      </tr>
                      <!--preference-->
                      <tr>
                        <td class="preference-link" align="center" style="font-family: \'Open sans\', Arial, sans-serif; color:#bbb; font-size:12px;font-style: italic;">
                          POWERED 
                          <a href="https://pandagrown.com/" style="color: #059033;">BY PANDAGROWN.COM</a>
                        </td>
                      </tr>
                      <!--end preference-->
                      <tr>
                        <td height="10"></td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>"""
    if email_code == 'FORGOT_PASSWORD':
        mail_template = email_setting.email_body
    else :
        mail_template = email_header + main_body + email_footer
    template = Template(mail_template)
    rendered_html = template.render(context)

    # Send verification email to user
    email = EmailMessage(
        subject=email_setting.subject,
        body=rendered_html,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email],
        connection=connection
    )
    email.content_subtype = 'html'
    email.send()

    return True
    
def get_superuser_by_email(email):
    return User.objects.filter(email=email, status=1, is_superuser=True, is_supportuser=False).first()
def get_supportuser_by_email(email):
    return User.objects.filter(email=email, status=1, is_supportuser=True).first()
def update_user_login_state(user, request, user_type):
    user.last_login_dt = timezone.now()
    user.last_login_ip = get_requester_ip(request)
    user.save()
    jwt_token = JWTAuthentication.create_jwt(user)
    if user_type == 0:
        user_profile = UserProfile.objects.filter(user_id=user.id).first()
        if user_profile.avatar.name == 'avatar/avatar.jpg':
            if user_profile.gender == '0':
                user_profile.avatar = 'avatar/female.png'
            else:
                user_profile.avatar = 'avatar/male.png'
        avatar_url = user_profile.avatar.url if user_profile.avatar else None
        full_avatar_url = request.build_absolute_uri(avatar_url) if avatar_url else None
        notifications = Notifications.objects.filter(user_id=user.id).filter(is_read=False).count()
        user_plants_count = calc_round(SeedUser.objects.filter(user_id=user.id).count())
        user_harvest_amount = calc_round(SeedUser.objects.filter(user_id=user.id, status=1).aggregate(sum_value=Sum(F('seed__harvest_rate') * F('purchased_amount') / 100))['sum_value'])
        user_profit = calc_round(SeedUser.objects.filter(user_id=user.id, status=1, payment_method=1).aggregate(sum_value=Sum(F('profit')))['sum_value']) or 0
        user_profit_pga = calc_round(SeedUser.objects.filter(user_id=user.id, status=1, payment_method=0).aggregate(sum_value=Sum(F('profit')))['sum_value'])
        response_data = json.dumps({
            'type': 'success', 
            'token': jwt_token, 
            'refresh_token': JWTAuthentication.create_jwt(user, True),
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
    else:
        response_data = json.dumps({
            'type': 'success', 
            'token': jwt_token, 
            'refresh_token': JWTAuthentication.create_jwt(user, True),
            'user_id': user.id,
        }, ensure_ascii=False).encode('utf-8')
    return response_data

def get_requester_ip(request: HttpRequest):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # If the request is coming through a proxy server
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
