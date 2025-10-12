from typing import override

from django.db import transaction
from rest_framework.serializers import ModelSerializer, Serializer, UUIDField
from wishlist.models import WishItem, ItemSource
import uuid

class SourceItemSerializer(ModelSerializer):
    id = UUIDField(default=uuid.uuid4, read_only=False)

    class Meta:
        model = ItemSource
        fields = ['id', 'source_url', 'source_name', 'description']

class WishListItemSerializer(ModelSerializer):
    class Meta:
        model = WishItem
        fields = ['id', 'title', 'is_completed', 'is_starred', 'updated_at']

class WishListItemDetailSerializer(ModelSerializer):
    sources = SourceItemSerializer(many=True, required=False)

    @override
    def create(self, validated_data: dict) -> WishItem:
        """
        Create and return a new `WishItem` instance, given the validated data.
        :param validated_data: The validated data for creating the WishItem.
        :return: The created WishItem instance.
        """
        sources_data = validated_data.pop('sources', [])
        wish_item = WishItem.objects.create(**validated_data)
        if sources_data:
            item_sources = [ItemSource(wish_item=wish_item, **sd) for sd in sources_data]
            ItemSource.objects.bulk_create(item_sources)
        return wish_item

    @override
    def update(self, instance: WishItem, validated_data: dict) -> WishItem:
        """
        Update and return an existing `WishItem` instance, given the validated data.
        :param instance: The existing WishItem instance to be updated.
        :param validated_data: The validated data for updating the WishItem.
        :return: The updated WishItem instance.
        """
        sources = validated_data.pop('sources', [])
        current_sources = dict((i.id, i) for i in instance.sources.all())

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        new_items = []
        updated_items = []
        for src in sources:
            if 'id' in src:
                item = current_sources.pop(src['id'])
                for property in src.keys():
                    setattr(item, property, src[property])
                updated_items.append(item)
            else:
                new_items.append(ItemSource(wish_item=instance, **src))

        with transaction.atomic():
            ItemSource.objects.bulk_create(new_items)
            ItemSource.objects.bulk_update(updated_items, ['source_url', 'source_name', 'description'])
            if len(current_sources) > 0:
                for src in current_sources.values():
                    src.delete()

        instance.save()
        return instance

    class Meta:
        model = WishItem
        fields = ['id', 'title', 'description', 'is_public', 'is_completed',
                  'is_starred', 'created_at', 'updated_at', 'sources']
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }
