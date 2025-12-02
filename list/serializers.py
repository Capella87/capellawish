from django.db import models
from django.db.models import QuerySet
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from list.models import ListModel
from wishlist.models import BlobImage


class ListSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()
    image = SerializerMethodField()

    class Meta:
        model = ListModel
        fields = ['uuid', 'title', 'description', 'image', 'updated_at', 'item_count']
        read_only_fields = ['uuid', 'updated_at', 'item_count', 'image']

    def get_item_count(self, obj):
        return obj.items.count()

    def get_image(self, obj: BlobImage) -> str | None:
        return None if obj.image is None else self.context.get('request').build_absolute_uri(obj.image.image.url)


class ListDetailSerializer(serializers.ModelSerializer):
    # TODO: Pagination for nested items:
    item_count = serializers.SerializerMethodField()
    image = SerializerMethodField()

    class Meta:
        model = ListModel
        fields = ['uuid', 'title', 'description', 'image', 'updated_at', 'item_count',
                  'created_at', 'allow_completion_by_other', 'allow_anonymous_completion', 'is_shared']
        read_only_fields = ['uuid', 'created_at', 'updated_at', 'item_count', 'image']

    def get_item_count(self, obj):
        return obj.items.count()

    def get_image(self, obj: BlobImage) -> str | None:
        return None if obj.image is None else self.context.get('request').build_absolute_uri(obj.image.image.url)


class ListItemSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.UUIDField(),
                                  allow_empty=True)

    class Meta:
        fields = ['items']
