from django.shortcuts import render
from rest_framework import status
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from list.models import ListModel
from list.serializers import ListSerializer
from wishlist.pagination import WishListPagination


# Create your views here.

class ListView(APIView, WishListPagination):
    permission_classes = [IsAuthenticated]
    serializer_class = ListSerializer
    parser_classes = (MultiPartParser, JSONParser)

    # Search for all lists created by user
    def get(self, request: Request) -> Response:
        targets = (ListModel.objects
                   .filter(user_id=request.user.id))

        paginated = self.paginate_queryset(queryset=targets, request=request, view=self)
        serialized = self.serializer_class(instance=paginated, many=True)

        return self.get_paginated_response(data=serialized.data)

    # Create a new list for items
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(user=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PublicListView(APIView):
    pass


class ListDetailView(APIView):
    pass
