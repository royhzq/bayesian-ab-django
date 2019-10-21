from django.urls import path
from .views import *
from .api import *
urlpatterns = [
    path('', homepage, name='homepage'),
    path('dashboard', dashboard, name='dashboard'),
    path('clear_stats', clear_stats, name='clear_stats'),
    path('api/experiment/response', ABResponse.as_view(), name='ABResponse'),
    path('api/experiment/simulation', RunSimulation.as_view(), name='RunSimulation'),
    path('api/sim_page_views', SimPageVisitsAPI.as_view(), name= 'SimPageVisits'),
]