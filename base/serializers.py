
from rest_framework import serializers
from base.models import EmailSetting, CurrencySetting, FAQCategory, FAQList, NotificationSetting, Testimonial, SocialSetting, SiteSetting

class EmailSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailSetting
        fields = '__all__'

class CurrencySettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencySetting
        fields = '__all__'

class FAQCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQCategory
        fields = '__all__'

class FAQListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(read_only=True)
    category_in_use = serializers.IntegerField(read_only=True)
    class Meta:
        model = FAQList
        fields = ['id', 'category', 'title', 'content', 'category_name', 'category_in_use']

class NotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = '__all__'

class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = '__all__'

class SocialSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialSetting
        fields = '__all__'

class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = '__all__'