from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


# Create your views here.

class ListView(APIView):
    permission_classes = [IsAuthenticated]
    pass


class ListDetailView(APIView):
    pass
