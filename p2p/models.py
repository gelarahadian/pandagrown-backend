from django.db import models
from user.models import User
from inventory.models import Inventory

# Create your models here.
class P2p(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_p2p', unique=False)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='p2p_inventory', unique=False)
    
    class Meta:
        db_table = 'p2p'