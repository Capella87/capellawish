from django.db import models
from django.db.models import UniqueConstraint
import uuid

from account.models import WishListUser


# Create your models here.

class ListModel(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, auto_created=True)
    title = models.CharField(max_length=200, blank=False)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="lists",
                              blank=True,
                              null=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(WishListUser, on_delete=models.CASCADE)

    # Share properties
    allow_completion_by_other = models.BooleanField(default=False)
    allow_anonymous_completion = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)

    items = models.ManyToManyField('wishlist.WishItem', blank=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'wishitem_list'
        db_table_comment = 'Lists of wishlist items'

        indexes = [
            models.Index(fields=['is_deleted']),
            models.Index(fields=['user']),
            models.Index(fields=['uuid'])
        ]
        ordering = [
            'user',
        ]
        constraints = [
            UniqueConstraint(fields=['user', 'title'], name='unique_list_title')
        ]
