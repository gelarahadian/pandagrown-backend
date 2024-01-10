from django.db import models

# Create your models here.
class Market(models.Model):
    name = models.CharField(max_length=128)
    buy_price = models.FloatField(default=0)
    size = models.CharField(max_length=128)
    stock = models.FloatField(default=0)
    benefit = models.IntegerField(default=0)
    benefit_type = models.CharField(blank=True, null=True)
    cover_img = models.ImageField(upload_to='market/cover/', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'market'