from typing import override

from rest_framework.serializers import ModelSerializer, Serializer
from wishlist.models import WishItem, ItemSource


class SourceItemSerializer(Serializer):
    class Meta:
        model = ItemSource
        fields = ['source_url', 'source_name', 'description']


class WishlistSerializer(ModelSerializer):
    sources = SourceItemSerializer(many=True)

    @override(ModelSerializer.create)
    def create(self, validated_data: dict) -> WishItem:
        """
        Create and return a new `WishItem` instance, given the validated data.
        :param validated_data: The validated data for creating the WishItem.
        :return: The created WishItem instance.
        """
        sources = validated_data.pop('sources', [])
        wish_item = WishItem.objects.create(**validated_data)
        for data in sources:
            item, _ = ItemSource.objects.get_or_create(**data)
            wish_item.sources.add(item)
        return wish_item

    @override(ModelSerializer.update)
    def update(self, instance, validated_data: dict) -> WishItem:
        """
        Update and return an existing `WishItem` instance, given the validated data.
        :param instance: The existing WishItem instance to be updated.
        :param validated_data: The validated data for updating the WishItem.
        :return: The updated WishItem instance.
        """
        sources = validated_data.pop('sources', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if len(sources) > 0:
            instance.sources.clear()
            for source_data in sources:
                item, _ = ItemSource.objects.get_or_create(**source_data)
                instance.sources.add(item)
        return instance

    class Meta:
        model = WishItem
        fields = ['title', 'description', 'is_public', 'is_completed', 'is_starred', 'sources']
