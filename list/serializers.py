from django.db import models
from django.db.models import QuerySet
from rest_framework import serializers

from list.models import ListModel


class ListSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = ListModel
        fields = ['uuid', 'title', 'description', 'image', 'updated_at', 'item_count']

    def get_item_count(self, obj):
        return obj.items.count()


class ListDetailSerializer(serializers.ModelSerializer):
    # TODO: Pagination for nested items:

    class Meta:
        model = ListModel
        fields = ['uuid', 'title', 'description', 'image', 'updated_at', 'item_count']
