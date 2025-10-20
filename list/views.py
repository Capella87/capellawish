from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from list.models import ListModel
from list.serializers import ListSerializer, ListDetailSerializer
from wishlist.pagination import WishListPagination


# Create your views here.

class ListView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ListSerializer
    pagination_class = WishListPagination
    parser_classes = (MultiPartParser, JSONParser)

    # Search for all lists created by user
    def get(self, request: Request) -> Response:
        targets = (ListModel.objects
                   .filter(user_id=request.user.id))

        paginated = self.paginate_queryset(queryset=targets)
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


class ListDetailView(GenericAPIView):
    serializer_class = ListDetailSerializer

    # TODO: Open for anonymouse users when user set the settings
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, uuid: str) -> Response:
        # TODO: Paginate items per 30 with customized pagination logic
        target = get_object_or_404(ListModel.objects,
                                   uuid=uuid,
                                   is_deleted=False,
                                   user=request.user)
        if not target:
            return Response(data={'status': 'error', 'message': 'list not found'},
                            status=status.HTTP_404_NOT_FOUND)
        serialized = self.serializer_class(instance=target)

        return Response(data=serialized.data, status=status.HTTP_200_OK)
