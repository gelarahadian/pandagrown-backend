from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        # Your implementation here
        return

    def create_superuser(self, email, password=None, **extra_fields):
        # Your implementation here
        # Perform your data insertion operations here
        user = {'email': email, 'password': make_password(password), 'status': 1, 'is_superuser': True}  
        user = User(**user)
        user.save()
        user_profile = { 'user_id': user.pk }
        profile = UserProfile(**user_profile)
        profile.save()
        return
    def create_supportuser(self, email, password=None, **extra_fields):
        # Your implementation here
        # Perform your data insertion operations here
        user = {'email': email, 'password': make_password(password), 'status': 1, 'is_superuser': True, 'is_supportuser': True}
        user = User(**user)
        user.save()
        user_profile = { 'user_id': user.pk }
        profile = UserProfile(**user_profile)
        profile.save()
        return

class User(AbstractUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    status_choices = (
        (1, 'available'),
        (2, 'pending'),
        (3, 'suspended')
    )
    username = models.CharField(max_length=50, unique=False, default="")
    status = models.IntegerField(choices=status_choices, default=1)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    last_login_dt = models.DateTimeField(blank=True, null=True)
    last_login_ip = models.CharField(max_length=20, blank=True, null=True)
    activation_code = models.CharField(max_length=255, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    is_supportuser = models.BooleanField(default=False)
    forgot_password_code = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = UserManager()
    class Meta:
        db_table = 'users'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    def save(self, *args, **kwargs):
        if not self.id:
            self.date_joined = timezone.now()
        return super().save(*args, **kwargs)
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True, on_delete=models.CASCADE)
    f_name = models.CharField(max_length=100, blank=True, null=True)
    l_name = models.CharField(max_length=100, blank=True, null=True)
    
    avatar = models.ImageField(upload_to='avatar/', default='avatar/avatar.jpg')
    country = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    zip = models.CharField(max_length=10, blank=True, null=True)
    area_code = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    telegram = models.CharField(max_length=34, blank=True, null=True)
    balance = models.FloatField(blank=True, null=True)
    pandami_balance = models.FloatField(blank=True, null=True, default=0)
    refer_code = models.CharField(max_length=20, blank=True, null=True)
    referer_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'user_profile'
        
class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='histories', unique=False)
    action = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=50, blank=True, null=True)
    ip = models.CharField(max_length=20, blank=True, null=True)
    level_choices = (
        (0, 'normal'),
        (1, 'waring'),
        (2, 'danger')
    )
    level = models.IntegerField(choices=level_choices, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'user_activity'

class UserAgent(models.Model):
    ip = models.CharField(max_length=20, blank=True, null=True)
    browser_info = models.CharField(max_length=255, blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'user_agent'

class BenefitHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='benefits', unique=False)
    benefit_rate = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'benefit_history'

class TicketDepartment(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'ticket_department'

class Ticket(models.Model):
    user = models.ForeignKey(User, unique=False, on_delete=models.CASCADE, related_name='user_ticket')
    department = models.ForeignKey(TicketDepartment, unique=False, on_delete=models.CASCADE, related_name='ticket_department')
    attach = ArrayField(models.CharField(max_length=1000), default=list)
    attach_origin = ArrayField(models.CharField(max_length=255), default=list)
    subject = models.CharField(max_length=100, blank=True, null=True)
    content = models.TextField(max_length=1000)
    status_choices = (
        (0, 'pending'),
        (1, 'replied'),
        (2, 'closed')
    )
    status = models.IntegerField(choices=status_choices, default=0)
    no = models.TextField(max_length=9, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'ticket'

class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, unique=False, on_delete=models.CASCADE, related_name='message_ticket')
    message = models.TextField(max_length=1000)
    image_description = models.ImageField(upload_to='support/ticket', blank=True, null=True)
    type_choices = (
        (0, 'admin'),
        (1, 'user')
    )
    type = models.IntegerField(choices=type_choices, default=0)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'ticket_reply'

class Referrer(models.Model):
    user = models.ForeignKey(User, unique=False, on_delete=models.CASCADE, related_name='user_referrer')
    referrer = models.ForeignKey(UserProfile, unique=False, on_delete=models.CASCADE, related_name='referrer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'user_referrer'
    