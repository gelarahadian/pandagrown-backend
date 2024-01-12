from django.urls import path
from .views import StatisticView, PlantsListView

urlpatterns = [ 
    path('statistic/', StatisticView.as_view(), name='statistic'),
    path('platns/', PlantsListView.as_view(), name='plants-list')
]