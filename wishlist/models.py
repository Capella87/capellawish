import uuid
from typing import override

from django.core import validators
from django.db import models
from account.models import WishListUser

# Create your models here.

class WishItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic fields
    title = models.CharField(max_length=400, blank=False)
    description = models.TextField(blank=True)

    # Image field (optional)
    image = models.ImageField(upload_to='static/items/images/', blank=True, null=True)

    # Status fields
    is_public = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)

    # Timestamp fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(auto_now=False, null=True)

    # custom_fields = models.JSONField(default=dict, blank=True)


    # Logical deletion field
    deleted_at = models.DateTimeField(auto_now=False, null=True)

    # User
    user = models.ForeignKey('account.WishListUser', related_name='wish_item_user', on_delete=models.CASCADE)



class ItemSource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Note: Due to the base of URLField is CharField, using TextField with validator to allow more length than 200
    source_url = models.TextField(blank=False, validators=[validators.URLValidator()])
    source_name = models.CharField(max_length=300, blank=True)
    wish_item = models.ForeignKey(WishItem, related_name='sources', on_delete=models.CASCADE)
    description = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['wish_item', 'source_url'])
        ]
        constraints = [
            models.UniqueConstraint(fields=['source_url', 'wish_item'], name='unique_source_per_item')
        ]
