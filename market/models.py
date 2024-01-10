from django.db import models

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