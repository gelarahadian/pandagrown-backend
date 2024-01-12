from django.db import models
from user.models import User
# Create your models here.
class Notifications(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_user', unique=False)
    content = models.TextField(default='')
    type_choices = (
        (0, 'Purchase'),
        (1, 'Seed_Step'),
        (2, 'Sell_Harvest'),
        (3, 'Withdraw'),
        (4, 'Update_Profile'),
        (5, 'Ticket_Status'),
        (6, 'Deposit_Balance'),
        (7, 'Deposit_PGAToken')
    )
    type = models.IntegerField(choices=type_choices, default=0)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'notifications'