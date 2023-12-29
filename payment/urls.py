from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DepositPandami, DepositCoinbase, WebhookCoinbase, TransactionLogAPIView, RequestWithdraw, ManageWithdraw

router = DefaultRouter()

urlpatterns = [
    # Deposit
    path('<int:user_id>/deposit/pandami/', DepositPandami.as_view(), name='deposit-pandami'),
    path('<int:user_id>/deposit/coinbase/', DepositCoinbase.as_view(), name='deposit-coinbase'),
    path('deposit/coinbase/confirm', WebhookCoinbase.as_view(), name='deposit-coinbase-confirm'),
    path('transaction/log/', TransactionLogAPIView.as_view(), name='transaction-log-list'),
    path('<int:user_id>/withdraw/request/', RequestWithdraw.as_view(), name='request-withdraw'),
    path('<int:transaction_log_id>/withdraw/manage/', ManageWithdraw.as_view(), name='manage-withdraw'),
]