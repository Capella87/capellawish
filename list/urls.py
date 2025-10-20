from django.urls import path
from rest_framework.urls import urlpatterns

from list.views import ListView, ListDetailView

urlpatterns = [
    path('', ListView.as_view(), name='list'),
    path('<str:uuid>', ListDetailView.as_view(), name='list-details'),
]
