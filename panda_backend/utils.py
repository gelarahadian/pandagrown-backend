from rest_framework.pagination import PageNumberPagination
from rest_framework import generics, status
from rest_framework.response import Response
import math

from basic_auth.authentication import JWTAuthentication

class PandaPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 100
    def get_page_number(self, request, paginator):
        page_number = request.query_params.get('page')
        if page_number is not None:
            try:
                page_number = int(page_number)
            except ValueError:
                page_number = 1
        return page_number

class PandaListView(generics.ListAPIView):
    def get_paginated_response(self, data, total_count):
        return Response({
            'total_count': total_count,
            'data': data
        })

class PandaCreateView(generics.CreateAPIView):
    authentication_classes = [JWTAuthentication]

class PandaDetailView(generics.RetrieveAPIView):
    lookup_field = 'pk'
    
class PandaUpdateView(generics.UpdateAPIView):
    authentication_classes = [JWTAuthentication]
    lookup_field = 'pk'
    def put(self, request, *args, **kwargs):
        self_row = self.get_object()
        serializer = self.get_serializer(self_row, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
class PandaDeleteView(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    lookup_field = 'pk'
    def delete(self, request, *args, **kwargs):
        self_row = self.get_object()
        self_row.delete()
        return Response(status=204)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'type':'success'}, status=status.HTTP_200_OK)

# def calc_profit(income_amount):
#     rate1 = 0
#     minRate1 = 0.096
#     maxRate2 = 0.25
#     minRateXA2 = 100
#     maxRateXA2 = 10000
#     minRateX1 = math.sqrt(math.sqrt(minRateXA2))
#     minRateX2 = math.sqrt(math.sqrt(maxRateXA2))
#     if income_amount >= minRateXA2:
#         income_amount = income_amount
#         if income_amount > maxRateXA2:
#             income_amount = maxRateXA2
#         a1 = math.sqrt(math.sqrt(income_amount))
#         rate1 = (a1 - minRateX1) * (maxRate2 - minRate1) / (minRateX2 - minRateX1) + minRate1
#     return rate1 * income_amount

def calc_profit(income_amount, payment_method):
    rate1 = 0
    if (payment_method == 1):
        if income_amount <= 100:
            rate1 = 0.24
        elif income_amount <= 1000:
            rate1 = 0.21
        elif income_amount <= 5000:
            rate1 = 0.19
        elif income_amount <= 10000:
            rate1 = 0.16
        else:
            rate1 = 0.15
    else:
        if income_amount <= 100:
            rate1 = 0.27
        elif income_amount <= 300:
            rate1 = 0.24
        elif income_amount <= 1000:
            rate1 = 0.21
        elif income_amount <= 2500:
            rate1 = 0.19
        else:
            rate1 = 0.16
    profit = income_amount * rate1
    return profit
def calc_bonus(income_amount, payment_method):
    rate1 = 0
    if (payment_method == 1):
        if income_amount <= 100:
            rate1 = 0.24
        elif income_amount <= 1000:
            rate1 = 0.21
        elif income_amount <= 5000:
            rate1 = 0.19
        elif income_amount <= 10000:
            rate1 = 0.16
        else:
            rate1 = 0.15
    else:
        if income_amount <= 100:
            rate1 = 0.27
        elif income_amount <= 300:
            rate1 = 0.24
        elif income_amount <= 1000:
            rate1 = 0.21
        elif income_amount <= 2500:
            rate1 = 0.19
        else:
            rate1 = 0.16
    return rate1

def calc_round(value):
    if value is None:
        value = 0
    value = float(value)
    return round(value, 2)