from typing import Any, override

from django.db import IntegrityError
from django.shortcuts import render
from django.template.context_processors import request
from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from wishlist.models import WishItem
from wishlist.pagination import WishItemListPagination
from wishlist.serializers import WishListItemSerializer, WishListItemDetailSerializer


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
                .only(*WishListItemDetailSerializer.Meta.fields)
                .order_by('-updated_at')) ## TODO: Add ordering options with query params

        starred = request.query_params.get('starred', None)
        if starred:
            objs = objs.filter(is_starred=True)

        paginated = self.paginate_queryset(queryset=objs, request=request, view=self)
        serialized = WishListItemSerializer(instance=paginated, many=True)

        return self.get_paginated_response(data=serialized.data)

    @extend_schema(
        request=WishListItemDetailSerializer,
        responses={201: WishListItemDetailSerializer},
        description="Create a new wishlist item for the authenticated user.",
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        '''
        Create a new wishlist item for the authenticated user
        :param request:
        :param args:
        :param kwargs:
        :return:
        '''

        serializer = WishListItemDetailSerializer(data=request.data)

        ## TODO: Filter duplicate titles for the same user.
        if not serializer.is_valid(raise_exception=True):
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)



        instance = serializer.save(user=request.user)
        return Response(data=WishListItemDetailSerializer(instance).data, status=status.HTTP_201_CREATED)


class WishListItemDetailView(APIView):
    '''
    View to manage a specific wishlist item.
    '''
    ## TODO: Allow others when user sets it to public
    permission_classes = [IsAuthenticated]
    serializer_class = WishListItemDetailSerializer

    def get(self, request: Request, id: str, *args, **kwargs) -> Response:
        requested_item = get_object_or_404(WishItem.objects.only(*WishListItemDetailSerializer.Meta.fields),
                                           id=id,
                                           deleted_at__isnull=True,
                                           user=request.user)
        if not requested_item:
            return Response(data={'status': 'error', 'message': 'Item not found'},
                            status=status.HTTP_404_NOT_FOUND)

        serialized = WishListItemDetailSerializer(instance=requested_item)
        return Response(data=serialized.data, status=status.HTTP_200_OK)


    def put(self, request: Request, id: str, *args, **kwargs) -> Response:
        # Updated items, deleted items, and added items should be handled here.
        target = get_object_or_404(WishItem.objects.all(),
                                   id=id,
                                   deleted_at__isnull=True,
                                   user__id=request.user.id)

        # Merge the existing data with the new data
        serializer = WishListItemDetailSerializer(instance=target, data=request.data, partial=True)
        if not serializer.is_valid(raise_exception=True):
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            instance = serializer.save()
        except IntegrityError as e:
            return Response(data={'status': 'error', 'message': 'Duplicate links are not allowed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(data=WishListItemDetailSerializer(instance).data, status=status.HTTP_200_OK)


    def delete(self, request: Request, id: str, *args, **kwargs) -> Response:
        target = get_object_or_404(WishItem.objects.only('id', 'deleted_at'),
                                   id=id,
                                   deleted_at__isnull=True,
                                   user=request.user)
        if not target:
            return Response(data={'status': 'error', 'message': 'Item not found'},
                            status=status.HTTP_404_NOT_FOUND)

        target.deleted_at = timezone.now()
        target.save(update_fields=['deleted_at'])

        return Response(status=status.HTTP_204_NO_CONTENT)
