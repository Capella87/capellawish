from django.db import models
from django.db.models import QuerySet
from rest_framework import serializers

from list.models import ListModel
from wishlist.serializers import WishListItemSerializer


class ListSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = ListModel
        fields = ['uuid', 'title', 'description', 'image', 'updated_at', 'item_count']
        read_only_fields = ['uuid', 'updated_at', 'item_count']

    def get_item_count(self, obj):
        return obj.items.count()


class ListDetailSerializer(serializers.ModelSerializer):
    # TODO: Pagination for nested items:
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = ListModel
        fields = ['uuid', 'title', 'description', 'image', 'updated_at', 'item_count',
                  'created_at', 'allow_completion_by_other', 'allow_anonymous_completion', 'is_shared']
        read_only_fields = ['uuid', 'created_at', 'updated_at', 'item_count']

    def get_item_count(self, obj):
        return obj.items.count()


class ListItemSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.UUIDField(),
                                  allow_empty=True)

    class Meta:
        fields = ['items']
