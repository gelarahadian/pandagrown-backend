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
from rest_framework import filters, viewsets, pagination
from rest_framework.response import Response
from rest_framework.views import APIView
from user_agents import parse
import json

from base.models import EmailSetting
from basic_auth.authentication import JWTAuthentication
from payment.models import TransactionLog
from shop.models import SeedUser
from user.models import Referrer, UserProfile, UserAgent
from market.models import Market
from market.serializers import MarketSerializer

User = get_user_model()

class MarketPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class MarketViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = Market.objects.all()
    serializer_class = MarketSerializer
    pagination_class = MarketPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]  # Add OrderingFilter and SearchFilter backends
    search_fields = ['name']  # Specify the fields to search for
    def get_permissions(self):
        if self.action in ['get']:
            # Apply custom authentication only for POST, DELETE, UPDATE, PATCH
            return [JWTAuthentication()]
        else:
            # Use default authentication for other actions
            return super().get_permissions()
    def get_queryset(self):
        queryset = Market.objects.all()
        sort_param = self.request.query_params.get('sort', None)
        if sort_param:
            # Determine the field and direction for sorting
            sort_fields = sort_param.split(',')
            ordering = []
            for field in sort_fields:
                if field.startswith('-'):
                    ordering.append(f"-{field[1:].strip()}")
                else:
                    ordering.append(field.strip())

            # Apply sorting to the queryset
            queryset = queryset.order_by(*ordering)
        queryset = queryset.filter(name__icontains=self.request.query_params.get('search', ''))
        return queryset
