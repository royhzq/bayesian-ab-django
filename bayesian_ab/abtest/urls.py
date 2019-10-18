from django.urls import path
from .views import *
from .api import *
urlpatterns = [
    path('', homepage, name='homepage'),
    path('clear_stats', clear_stats, name='clear_stats'),
    path('api/experiment/response', ABResponse.as_view(), name='ABResponse'),
]