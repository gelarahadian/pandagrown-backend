from django.db.models import Sum, F
from rest_framework.views import APIView
from rest_framework.response import Response
from shop.models import SeedUser, Seed
from shop.serializers import SeedSerializer
from payment.models import TransactionLog
# Create your views here.
class StatisticView(APIView):
    def get(self, request, format=None):
        invest_people_count = SeedUser.objects.values('user').distinct().count()
        invest_fund = SeedUser.objects.filter(status=0).aggregate(sum_value=Sum(F('seed__buy_price') * F('purchased_amount')))['sum_value']
        return_paid = TransactionLog.objects.filter(status=1, method=1).aggregate(sum_value=Sum(F('amount')))['sum_value']
        hemps_planted = SeedUser.objects.filter(status=0).aggregate(sum_value=Sum(F('purchased_amount')))['sum_value']
        panda_amount = TransactionLog.objects.filter(status=1, method=0, type_id=1).aggregate(sum_value=Sum(F('amount')))['sum_value']
        return Response({'invest_people': invest_people_count, 'invest_fund': invest_fund, 'return_paid': return_paid, 'hemps_planted': hemps_planted, 'panda_amount': panda_amount})

class PlantsListView(APIView):
    def get(self, request, format=None):
        seeds = Seed.objects.order_by('-purchased_count')
        serializer = SeedSerializer(seeds, many=True)
        return Response(serializer.data)