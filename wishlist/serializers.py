from collections import Counter
from typing import override

from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, UUIDField

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
    # Validator for uniqueness
    # Source: https://www.django-rest-framework.org/api-guide/validators/
    # Source 2: https://stackoverflow.com/questions/70774389/django-rest-framwork-how-to-prevent-1062-duplicate-entry
    # title = CharField(max_length=400, validators=[UniqueValidator(queryset=WishItem.objects.all())])

    def validate_sources(self, attrs):
        sources = attrs
        urls = [s.get('source_url') for s in sources if 'source_url' in s]
        payload_dup = [u for u, c in Counter(urls).items() if c > 1]
        if payload_dup:
            raise ValidationError('Duplicate URLs are not allowed.')

        # Check duplicates in database
        if getattr(self, 'instance', None):
            queryset = (ItemSource.objects
                        .only('id', 'source_url', 'wish_item')
                        .filter(wish_item=self.context['instance'], source_url__in=urls))
            existing_sources = [s['id'] for s in sources if 'id' in s]
            if existing_sources:
                queryset = queryset.exclude(id__in=existing_sources).distinct('source_url')
            if queryset.exists():
                rt = queryset.values_list('source_url', flat=True)
                raise ValidationError('Duplicate URLs are not allowed.')
        return attrs

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
            ItemSource.objects.select_for_update().bulk_update(updated_items,
                                                               ['source_url', 'source_name', 'description'])
            if len(current_sources) > 0:
                for src in current_sources.values():
                    src.delete()

        instance.save()
        return instance

    # Source: https://stackoverflow.com/questions/30560470/context-in-nested-serializers-django-rest-framework/58505856#58505856
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sources'].context.update(self.context)

        if getattr(self, 'instance', None):
            self.fields['sources'].context['instance'] = self.instance

    class Meta:
        model = WishItem
        fields = ['id', 'title', 'description', 'is_public', 'is_completed',
                  'is_starred', 'created_at', 'updated_at', 'sources']
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }
