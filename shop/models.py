from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from user.models import User

class Seed(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    buy_price = models.FloatField(default=0)
    harvest_rate = models.FloatField(default=0)
    stock = models.FloatField(default=0)
    cover_img = models.ImageField(upload_to='seed/cover/')
    vegetation_mass_period = models.IntegerField(default=0)
    flowering_preharvest_period = models.IntegerField(default=0)
    harvest_period = models.IntegerField(default=0)
    drying_period = models.IntegerField(default=0)
    curing_period = models.IntegerField(default=0)
    packing_period = models.IntegerField(default=0)
    purchased_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'seed'

class SeedMedia(models.Model):
    seed = models.ForeignKey(Seed, unique=False, on_delete=models.CASCADE, related_name='seed_media')
    start_day = models.IntegerField(default=0)
    end_day = models.IntegerField(default=0)
    growing_img = ArrayField(models.CharField(max_length=1000))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'seed_media'

class SeedUser(models.Model):
    seed = models.ForeignKey(Seed, on_delete=models.CASCADE, related_name='seed_user', unique=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchase_user', unique=False)
    purchased_amount = models.FloatField(default=0)
    profit = models.FloatField(default=0)
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
    method_silica = models.SmallIntegerField(choices=status_choices, default=0)
    method_botanicare = models.SmallIntegerField(choices=status_choices, default=0)
    method_rhizo = models.SmallIntegerField(choices=status_choices, default=0)
    est_harvest_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'seed_user'
    @property
    def current_period(self):
        current_time = timezone.now()
        current_period = current_time - self.purchased_at
        return current_period.days
    # Setter method for current_period (optional)
    @current_period.setter
    def current_period(self, value):
        # This method is optional and can be omitted if the field is read-only
        pass

class SeedCart(models.Model):
    seed = models.ForeignKey(Seed, on_delete=models.CASCADE, related_name='cart_seed', unique=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_user', unique=False)
    status_choices = (
        (0, 'not set'),
        (1, 'set')
    )
    method_silica = models.SmallIntegerField(choices=status_choices, default=0)
    method_botanicare = models.SmallIntegerField(choices=status_choices, default=0)
    method_rhizo = models.SmallIntegerField(choices=status_choices, default=0)
    purchased_amount = models.FloatField(default=0)
    payment_method_choices = (
        (0, 'pga'),
        (1, 'usd')
    )
    payment_method = models.SmallIntegerField(choices=payment_method_choices, default=0)
    price_sum = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'seed_cart'

class SeedOrder(models.Model):
    seed = models.ForeignKey(Seed, on_delete=models.CASCADE, related_name='seed_order', unique=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='order_user', unique=False)
    purchase = models.ForeignKey(SeedUser, on_delete=models.CASCADE, related_name='purchased_seed', unique=False)
    status_choices = (
        (0, 'pending'),
        (1, 'completed'),
        (2, 'rejected')
    )
    status = models.IntegerField(choices=status_choices, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'seed_sell_order'