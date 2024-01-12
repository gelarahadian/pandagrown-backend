from django.urls import path, include
from rest_framework.routers import DefaultRouter

from basic_auth.views import AdminBackupView
from .views import email, currency, faq_category, faq_list, notification_setting, faq, testimonial, social_setting, site_setting

router_email = DefaultRouter()
router_email.register(r'', email.EmailViewSet)

router_currency = DefaultRouter()
router_currency.register(r'', currency.CurrencyViewSet)

router_faq_category = DefaultRouter()
router_faq_category.register(r'', faq_category.FAQCategoryViewSet)

router_faq_list = DefaultRouter()
router_faq_list.register(r'', faq_list.FAQListViewSet)

router_notification_setting = DefaultRouter()
router_notification_setting.register(r'', notification_setting.NotificationSettingViewSet)

router_tertimonial = DefaultRouter()
router_tertimonial.register(r'', testimonial.TestimonialViewSet)

router_site_setting = DefaultRouter()
router_site_setting.register(r'', site_setting.SiteSettingViewSet)

router_social_setting = DefaultRouter()
router_social_setting.register(r'', social_setting.SocialSettingViewSet)

urlpatterns = [
    # EmailSetting
    path('email/', include(router_email.urls)),
    
    # CurrencySetting
    path('currency/', include(router_currency.urls)),

    # FAQ Category
    path('faq/', faq.FAQListView.as_view(), name='faq'),
    path('faq/category/', include(router_faq_category.urls)),

    # FAQ List
    path('faq/list/', include(router_faq_list.urls)),

    # NotificationSetting
    path('notification/', include(router_notification_setting.urls)),

    # Testimonial 
    path('testimonial/', include(router_tertimonial.urls)),

    # Site Setting
    path('site_setting/', include(router_site_setting.urls)),

    # Social Setting
    path('social/', include(router_social_setting.urls)),

    # Backup Important informations
    path('backup/', AdminBackupView.as_view(), name="last-backup"),
]