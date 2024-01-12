from django.db import models

class EmailSetting(models.Model):
    email_code = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=100, blank=True, null=True)
    email_body = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'email_setting'

class CurrencySetting(models.Model):
    icon = models.ImageField(upload_to='currency_icon/', default='')
    name = models.CharField(max_length=30, blank=True, null=True)
    symbol = models.CharField(max_length=20, blank=True, null=True)
    unit = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'currency_setting'

class FAQCategory(models.Model):
    name = models.CharField(max_length=255, blank=False)
    use_choices = (
        (1, 'landing_faq_page'),
        (2, 'user_support'),
        (3, 'both')
    )
    in_use = models.SmallIntegerField(choices=use_choices, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'faq_category'

class FAQList(models.Model):
    category = models.ForeignKey(FAQCategory, on_delete=models.CASCADE, related_name='faq_id', unique=False)
    title = models.CharField(max_length=255, blank=False)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'faq_list'

class NotificationSetting(models.Model):
    type = models.CharField(max_length=20, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'notification_setting'

class Testimonial(models.Model):
    avatar = models.ImageField(upload_to='avatar/', default='avatar/avatar.jpg')
    name = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'testimonial'

class SocialSetting(models.Model):
    icon = models.ImageField(upload_to='social/')
    name = models.CharField(max_length=20, blank=True, null=True)
    link = models.CharField(max_length=256, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'social_setting'

class SiteSetting(models.Model):
    code = models.CharField(max_length=20, blank=True, null=True)
    value = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'site_setting'