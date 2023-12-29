from django.db import models

from base.models import CurrencySetting
from user.models import User

# Create your models here.
class TransactionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transaction_user', unique=False)
    amount = models.FloatField(default=0)
    coin_amount = models.FloatField(default=0)
    status_choices = (
        (0, 'pending'),
        (1, 'success'),
        (2, 'cancelled'),
        (3, 'failed')
    )
    status = models.IntegerField(choices=status_choices, default=0)
    type_id = models.IntegerField(default=0)
    method_choices = (
        (0, 'deposit'),
        (1, 'withdraw'),
    )
    method = models.IntegerField(choices=method_choices, default=0)
    withdrawal_currency_choices = (
        (-1, 'none'),
        (0, 'pga'),
        (1, 'usd'),
    )
    withdrawal_currency = models.IntegerField(choices=withdrawal_currency_choices, default=-1)
    address = models.CharField(max_length=128, blank=True, null=True)
    tx_hash = models.CharField(max_length=1024, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'transaction_log'