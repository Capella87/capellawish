import logging
from typing import override

from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from list.models import ListModel
from list.serializers import ListSerializer, ListDetailSerializer, ListItemSerializer
from wishlist.models import WishItem
from wishlist.pagination import WishListPagination, WishItemListPagination
from wishlist.serializers import WishListItemSerializer


# Create your views here.

logger = logging.getLogger(__name__)

class ListView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ListSerializer
    pagination_class = WishListPagination
    parser_classes = (MultiPartParser, JSONParser)

    @override
    def get_queryset(self):
        return (
            ListModel.objects
            .filter(user_id=self.request.user.pk)
            .only(*['uuid', 'title', 'description', 'image', 'updated_at'])
        )

    # Search for all lists created by user
    def get(self, request: Request) -> Response:
        qs = self.get_queryset()

        paginated = self.paginate_queryset(queryset=qs)
        serialized = self.serializer_class(instance=paginated, many=True)

        return self.get_paginated_response(data=serialized.data)

    # Create a new list for items
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PublicListView(APIView):
    pass


class ListDetailView(GenericAPIView):
    serializer_class = ListDetailSerializer
    lookup_field = 'uuid'
    # TODO: Open for anonymouse users when user set the settings
    permission_classes = [IsAuthenticated]
    queryset = ListModel.objects.filter(is_deleted=False)

    def get(self, request: Request, uuid: str) -> Response:
        target = get_object_or_404(self.get_queryset(),
                                   uuid=uuid,
                                   is_deleted=False,
                                   user=request.user)
        serialized = self.serializer_class(instance=target)

        return Response(data=serialized.data, status=status.HTTP_200_OK)

    def patch(self, request: Request, uuid: str) -> Response:
        target = get_object_or_404(self.get_queryset(),
                                   uuid=uuid,
                                   is_deleted=False,
                                   user=request.user)
        serialized = self.serializer_class(instance=target, data=request.data, partial=True)
        serialized.is_valid(raise_exception=True)
        serialized.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, uuid: str) -> Response:
        target = get_object_or_404(ListModel.objects.only('uuid', 'is_deleted', 'items'),
                                   uuid=uuid,
                                   is_deleted=False,
                                   user=request.user)
        target.items.clear()
        target.is_deleted = True
        target.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


# Note: This view must be APIView because GenericAPIView requires queryset configuration which is not needed for actions
class ListItemView(APIView):
    # TODO: Follow user preferences for permissions
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, uuid: str) -> Response:
        target = get_object_or_404(ListModel.objects.only('uuid', 'items', 'is_deleted'),
                                   uuid=uuid,
                                   is_deleted=False,
                                   user_id=request.user.pk)
        queryset = (
            target.items.filter(user_id=request.user.pk, deleted_at__isnull=True)
            .order_by('-created_at')
            .only(*WishListItemSerializer.Meta.fields)
        )

        if request.query_params.get('starred', None):
            queryset = queryset.filter(is_starred=True)
        paginator = WishItemListPagination()
        paginated = paginator.paginate_queryset(queryset=queryset, request=request, view=self)
        serialized = WishListItemSerializer(instance=paginated, many=True)

        return paginator.get_paginated_response(data=serialized.data)

    def post(self, request: Request, uuid: str) -> Response:
        target = get_object_or_404(ListModel.objects.only('uuid', 'items', 'is_deleted'),
                                   uuid=uuid,
                                   is_deleted=False,
                                   user_id=request.user.pk)

        serializer = ListItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Concurrency
        try:
            with transaction.atomic():
                retrieved = WishItem.objects.select_for_update().in_bulk(id_list=serializer.validated_data.get('items', []),
                                                                     field_name='uuid')
                target.items.add(*retrieved.values())
                target.save()
        except IntegrityError:
            transaction.rollback()
            logger.exception('Integrity Error occurred')
            raise APIException(code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, uuid: str) -> Response:
        target = get_object_or_404(ListModel.objects.only('uuid', 'items', 'is_deleted'),
                                        uuid=uuid,
                                        is_deleted=False,
                                        user_id=request.user.pk)

        serializer = ListItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Concurrency
        # TODO: Filter already deleted items
        # TODO: When the item is deleted, how to set a relation....
        try:
            with transaction.atomic():
                retrieved = target.items.select_for_update().in_bulk(id_list=serializer.validated_data.get('items', []),
                                                                     field_name='uuid')
                target.items.remove(*retrieved.values())
        except IntegrityError:
            transaction.rollback()
            logging.exception('Integrity Error occurred')
            raise APIException(code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_204_NO_CONTENT)
