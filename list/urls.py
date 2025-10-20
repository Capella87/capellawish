from django.urls import path
from rest_framework.urls import urlpatterns

from list.views import ListView, ListDetailView, ListItemView

urlpatterns = [
    path('', ListView.as_view(), name='list'),
    path('<str:uuid>/', ListDetailView.as_view(), name='list-details'),
    path('<str:uuid>/items', ListItemView.as_view(), name='list-items'),
]
