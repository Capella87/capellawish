from collections import Counter
from typing import override

from django.db import transaction
from django.db.models import ImageField
from django.db.models.fields.files import ImageFieldFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer, UUIDField
from django.utils import timezone
from hashlib import sha256

from wishlist.models import WishItem, ItemSource, BlobImage
import uuid


class BlobImageSerializer(ModelSerializer):
    """
    Serializer for BlobImage model to represent image data.
    """
    class Meta:
        model = BlobImage
        fields = ['image']
        read_only_fields = ['image']


class BlobImageUploadSerializer(ModelSerializer):
    """
    Serializer for uploading an image to BlobImage model.
    """
    @override
    def create(self, validated_data: dict) -> BlobImage:
        # Hash calculation
        image_binary = validated_data['image']

        hash_obj = sha256()
        for chunk in image_binary.chunks():
            hash_obj.update(chunk)
        sha256_hash = hash_obj.hexdigest()

        blob, _ = BlobImage.objects.get_or_create(
            sha256_hash=sha256_hash,
            defaults={'image': image_binary})
        return blob

    class Meta:
        model = BlobImage
        fields = ['image', 'sha256_hash', 'uploaded_at']
        read_only_fields = ['sha256_hash', 'uploaded_at']


class SourceItemSerializer(ModelSerializer):
    uuid = UUIDField(default=uuid.uuid4, read_only=False) # Will be a trouble if I set read_only to True?
    is_primary = serializers.BooleanField(required=False, read_only=True)

    class Meta:
        model = ItemSource
        fields = ['uuid', 'source_url', 'source_name', 'description', 'is_primary']


class WishListItemSerializer(ModelSerializer):
    uuid = UUIDField(default=uuid.uuid4)
    image = SerializerMethodField(read_only=True)
    primary_source_url = SerializerMethodField(read_only=True)

    def get_primary_source_url(self, obj) -> str | None:
        target = ItemSource.objects.filter(wish_item=obj, is_primary=True).first()
        if not target:
            return None
        return target.source_url

    def get_image(self, obj: BlobImage) -> str | None:
        return None if obj.image is None else self.context.get('request').build_absolute_uri(obj.image.image.url)

    class Meta:
        model = WishItem
        fields = ['uuid', 'title', 'completed_at', 'is_starred', 'updated_at', 'image', 'primary_source_url']
        read_only_fields = [
            'uuid', 'updated_at', 'image', 'primary_source_url'
        ]


class WishListItemDetailSerializer(ModelSerializer):
    image = SerializerMethodField(read_only=True, required=False)
    sources = SourceItemSerializer(many=True, required=False)
    is_completed = serializers.BooleanField(write_only=True, required=False)
    completed_at = serializers.DateTimeField(read_only=True)
    upload_image = serializers.BooleanField(write_only=True, default=False)
    # Validator for uniqueness
    # Source: https://www.django-rest-framework.org/api-guide/validators/
    # Source 2: https://stackoverflow.com/questions/70774389/django-rest-framwork-how-to-prevent-1062-duplicate-entry
    # title = CharField(max_length=400, validators=[UniqueValidator(queryset=WishItem.objects.all())])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sources'].context.update(self.context)

        if getattr(self, 'instance', None):
            self.fields['sources'].context['instance'] = self.instance

    def validate_sources(self, attrs):
        sources = attrs
        urls = [s.get('source_url') for s in sources if 'source_url' in s]
        payload_dup = [u for u, c in Counter(urls).items() if c > 1]
        if payload_dup:
            raise ValidationError('Duplicate URLs are not allowed.')

        # Check duplicates in database
        # TODO: Lock the rows on check
        if getattr(self, 'instance', None):
            queryset = (ItemSource.objects
                        .only('uuid', 'source_url', 'wish_item')
                        .filter(wish_item=self.context['instance'], source_url__in=urls))
            existing_sources = [s['uuid'] for s in sources if 'uuid' in s]
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
        is_completed = validated_data.pop('is_completed', False)
        validated_data.pop('upload_image', False)

        # Get a timestamp referring time zone of the server settings
        completed_at = timezone.now() if is_completed else None

        wish_item = WishItem.objects.create(**validated_data, completed_at=completed_at)

        # TODO: Transaction
        if sources_data:
            item_sources = []
            if len(sources_data) > 0:
                item_sources.append(ItemSource(wish_item=wish_item, is_primary=True, **sources_data[0]))
            item_sources.extend([ItemSource(wish_item=wish_item, is_primary=False, **sources_data[i]) for i in range(1, len(sources_data))])
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
        current_sources = dict((i.uuid, i) for i in instance.sources.all())
        prev_is_completed = instance.completed_at is not None
        new_is_completed = validated_data.pop('is_completed', None)
        validated_data.pop('upload_image')

        if prev_is_completed and not new_is_completed:
            instance.completed_at = None
        elif not prev_is_completed and new_is_completed:
            instance.completed_at = timezone.now()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        new_items = []
        updated_items = []
        for src in sources:
            if 'uuid' in src:
                item = current_sources.pop(src['uuid'])
                for property in src.keys():
                    setattr(item, property, src[property])
                updated_items.append(item)
            else:
                new_items.append(ItemSource(wish_item=instance, **src))

        # TODO: Raise Error if any issue occurs
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

    @override
    def to_representation(self, instance: WishItem):
        ret = super().to_representation(instance)
        return ret

    def get_image(self, obj: BlobImage) -> str | None:
        return None if obj.image is None else self.context.get('request').build_absolute_uri(obj.image.image.url)

    class Meta:
        model = WishItem
        fields = ['uuid', 'title', 'description', 'is_public', 'is_completed', 'completed_at',
                  'is_starred', 'created_at', 'updated_at', 'sources', 'image', 'upload_image']
        read_only_fields = [
            'uuid', 'created_at', 'updated_at', 'image'
        ]


class WishListItemPatchSerializer(ModelSerializer):
    # sources = SourceItemSerializer(many=True, required=False)
    is_completed = serializers.BooleanField(write_only=True, required=False)
    completed_at = serializers.DateTimeField(read_only=True)

    @override
    def update(self, instance: WishItem, validated_data: dict) -> WishItem:
        prev_is_completed = instance.completed_at is not None
        new_is_completed = validated_data.pop('is_completed', None)

        if prev_is_completed and not new_is_completed:
            instance.completed_at = None
        elif not prev_is_completed and new_is_completed:
            instance.completed_at = timezone.now()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    class Meta:
        model = WishItem
        fields = ['uuid', 'title', 'description', 'is_public', 'is_completed', 'completed_at',
                  'is_starred', 'created_at', 'updated_at']
        read_only_fields = [
            'uuid', 'created_at', 'updated_at', 'image'
        ]
