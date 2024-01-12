from django.db import models
from user.models import User

# Create your models here.
class Inventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_user', unique=False)
    buy_price = models.FloatField(default=0)
    stock = models.FloatField(default=0)
    cover_img = models.ImageField(upload_to='market/cover/')
    for_sale = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'inventory'