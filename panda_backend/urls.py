from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from basic_auth.authentication import SwaggerTokenAuthentication
from websocket_app.routing import websocket_urlpatterns

schema_view = get_schema_view(
   openapi.Info(
      title="PandaGrown-API",
      default_version='v1',
      description="This is PandaGrown API Doc.",
      contact=openapi.Contact(email="dream.dev1992@gmail.com"),
      license=openapi.License(name="RAS Dev Group"),
   ), 
   public=True,
   permission_classes=(permissions.AllowAny,),
   authentication_classes=(SwaggerTokenAuthentication, )
)

urlpatterns = [
    path('admin/', include('admin_api.urls')),
    path('auth/', include('basic_auth.urls')),
    path('user/', include('user.urls')),
    path('base/', include('base.urls')),
    path('shop/', include('shop.urls')),
    path('payment/', include('payment.urls')),
    path('market/', include('market.urls')),
    path('inventory/', include('inventory.urls')),
   #  path('notifications/', include(url_patterens)),
    path('ws/', include(websocket_urlpatterns)),

   
    path('swagger(<format>.json|.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.MEDIA_URL_ABSOLUTE, document_root=settings.MEDIA_ROOT) + static(settings.PAPER_URL_ABSOLUTE, document_root=settings.PAPER_ROOT)

