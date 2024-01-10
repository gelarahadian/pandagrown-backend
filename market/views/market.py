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
from market.serializers import MarketSerializer

User = get_user_model()

class MarketListView(PandaListView):
    authentication_classes = [JWTAuthentication]
    ordering = [ '-created_at']
    queryset = User.objects.order_by(*ordering).all()
    serializer_class = MarketSerializer
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
