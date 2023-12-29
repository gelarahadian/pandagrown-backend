from django.db.models import F, ExpressionWrapper, CharField, IntegerField
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, response

from base.serializers import FAQListSerializer
from base.models import FAQList

class FAQListView(generics.ListAPIView):
    serializer_class = FAQListSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'category_in_use',
                openapi.IN_QUERY,
                description="Filter FAQs by category in use (1 or 2)",
                type=openapi.TYPE_INTEGER,
                enum=[1, 2],
            ),
        ],
        responses={
            200: openapi.Response('OK'),
            400: openapi.Response('Bad Request'),
            403: openapi.Response('Forbidden'),
        }
    )
    def get(self, request, *args, **kwargs):
        queryset = FAQList.objects.order_by('category').all()
        category_name = ExpressionWrapper(
            F('category__name'),
            output_field=CharField()
        )
        category_in_use = ExpressionWrapper(
            F('category__in_use'),
            output_field=IntegerField()
        )
        queryset = queryset.annotate(
            category_name=category_name,
            category_in_use=category_in_use
        )
        category_in_use = int(self.request.query_params.get('category_in_use', 3))
        if category_in_use > 0 and category_in_use < 3:
            queryset = queryset.filter(category_in_use=category_in_use)
        
        serializer = self.serializer_class(queryset, many=True)
        return response.Response(serializer.data)
