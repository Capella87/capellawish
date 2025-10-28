import logging
from typing import override
from django.db import IntegrityError
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from django.utils import timezone

from wishlist.models import WishItem
from wishlist.pagination import WishItemListPagination
from wishlist.serializers import WishListItemSerializer, WishListItemDetailSerializer


# Create your views here.

logger = logging.getLogger(__name__)


class WishListView(GenericAPIView):
    """
    View to manage the wishlist items.
    """
    pagination_class = WishItemListPagination
    permission_classes = [IsAuthenticated]
    serializer_class = WishListItemSerializer
    parser_classes = (MultiPartParser, JSONParser)

    @override
    def get_queryset(self) -> QuerySet:
        return (WishItem.objects
                .filter(deleted_at__isnull=True)
                .filter(user_id=self.request.user.pk)
                .only(*self.get_serializer_class().Meta.fields))

    def get(self, request: Request, *args, **kwargs) -> Response:
        '''
        Retrieve the list of wishlist items for the authenticated user.
        :param request: rest_framework.request.Request class instance.
        :param args:
        :param kwargs:
        :return:
        '''

        ## TODO: Add ordering options with query params
        qs = self.get_queryset().order_by('-updated_at')

        starred = request.query_params.get('starred', None)
        if starred:
            qs = qs.filter(is_starred=True)

        paginated = self.paginate_queryset(queryset=qs)
        serialized = self.get_serializer(instance=paginated, many=True)

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
        # TODO: Prevent duplicates

        serializer = WishListItemDetailSerializer(data=request.data)

        ## TODO: Filter duplicate titles for the same user.
        if not serializer.is_valid(raise_exception=True):
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(user=request.user)

        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class WishListItemDetailView(GenericAPIView):
    """
    View to manage a specific wishlist item.
    """
    ## TODO: Allow others when user sets it to public
    permission_classes = [IsAuthenticated]
    serializer_class = WishListItemDetailSerializer

    def get(self, request: Request, id: str, *args, **kwargs) -> Response:
        requested_item = get_object_or_404(WishItem.objects.only(*self.get_serializer_class().Meta.fields),
                                           id=id,
                                           deleted_at__isnull=True,
                                           user=request.user)

        serializer = self.get_serializer(instance=requested_item)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def put(self, request: Request, id: str, *args, **kwargs) -> Response:
        # Updated items, deleted items, and added items should be handled here.
        target = get_object_or_404(WishItem.objects.all(),
                                   id=id,
                                   deleted_at__isnull=True,
                                   user__id=request.user.id)

        # Merge the existing data with the new data
        serializer = self.get_serializer(instance=target, data=request.data, partial=True)
        if not serializer.is_valid(raise_exception=True):
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
        except IntegrityError as e:
            logger.exception('Integrity Error occurred')
            raise APIException('Internal server error')

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: Request, id: str, *args, **kwargs) -> Response:
        target = get_object_or_404(WishItem.objects.only('id', 'deleted_at'),
                                   id=id,
                                   deleted_at__isnull=True,
                                   user=request.user)

        target.deleted_at = timezone.now()
        target.save(update_fields=['deleted_at'])

        return Response(status=status.HTTP_204_NO_CONTENT)
