from django.urls import path
from rest_framework.urls import urlpatterns

from list.views import ListView

urlpatterns = [
    path('', ListView.as_view(), name='list'),
]
