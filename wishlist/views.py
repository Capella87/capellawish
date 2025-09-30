from typing import Any, override

from django.shortcuts import render
from django.template.context_processors import request
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from wishlist.models import WishItem
from wishlist.pagination import WishItemListPagination
from wishlist.serializers import WishListItemSerializer, WishListItemCreateSerializer


# Create your views here.

class WishListView(APIView, WishItemListPagination):
    """
    View to manage the wishlist items.
    """
    pagination_class = WishItemListPagination
    permission_classes = [IsAuthenticated]
    serializer_class = WishListItemSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        '''
        Retrieve the list of wishlist items for the authenticated user.
        :param request: rest_framework.request.Request class instance.
        :param args:
        :param kwargs:
        :return:
        '''

        objs = (WishItem.objects
                .filter(deleted_at__isnull=True)
                .filter(user=self.request.user)
                .only(WishListItemSerializer.Meta.fields)
                .order_by('-updated_at')) ## TODO: Add ordering options with query params
        paginated = self.paginate_queryset(queryset=objs, request=request, view=self)
        serialized = WishListItemSerializer(instance=paginated, many=True)

        return self.get_paginated_response(data=serialized.data)

    def post(self, request: Request, *args, **kwargs) -> Response:
        '''
        Create a new wishlist item for the authenticated user
        :param request:
        :param args:
        :param kwargs:
        :return:
        '''

        serializer = WishListItemCreateSerializer(data=request.data)
        if not serializer.is_valid(raise_exception=True):
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        result = serializer.save(user=request.user)
        return Response(data=result, status=status.HTTP_201_CREATED)
