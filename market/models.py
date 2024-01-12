from django.db import models

from user.models import User

# Create your models here.
class Market(models.Model):
    name = models.CharField(max_length=128)
    buy_price = models.FloatField(default=0)
    size = models.CharField(max_length=128)
    stock = models.FloatField(default=0)
    benefit = models.IntegerField(default=0)
    benefit_type_choices = (
        (0, 'reduce'),
        (1, 'increase')
    )
    benefit_type = models.SmallIntegerField(choices=benefit_type_choices, default=0)
    unit_choices = (
        (0, 'day'),
        (1, 'percentage')
    )
    unit = models.SmallIntegerField(choices=unit_choices, default=0)
    cover_img = models.ImageField(upload_to='market/cover/', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'market'

class MarketUser(models.Model):
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='market_item', unique=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_market', unique=False)
    purchased_amount = models.FloatField(default=0)
    purchased_at = models.DateTimeField(auto_now_add=True)
    payment_method_choices = (
        (0, 'pga'),
        (1, 'usd')
    )
    payment_method = models.SmallIntegerField(choices=payment_method_choices, default=0)
    price_sum = models.FloatField(default=0)
    status_choices = (
        (0, 'purchased'),
        (1, 'ordered')
    )
    status = models.IntegerField(choices=status_choices, default=0)
    status_choices = (
        (0, 'not set'),
        (1, 'set')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'market_user'

class MarketChart(models.Model):
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='item_chart', unique=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_chart', unique=False)
    purchased_amount = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'market_chart'

class MarketOrder(models.Model):
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='item_order', unique=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_order', unique=False)
    purchase = models.ForeignKey(MarketUser, on_delete=models.CASCADE, related_name='puchase_market', unique=False)
    status_choices = (
        (0, 'pending'),
        (1, 'completed'),
        (2, 'rejected')
    )
    status = models.IntegerField(choices=status_choices, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'market_order'