from django.contrib import admin
from . import models

# Register your models here.

@admin.register(models.WishListUser)
class WishListUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'username', 'alias_name', 'first_name', 'last_name', 'is_active',
                    'is_staff', 'is_superuser', 'created_at', 'updated_at')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'alias_name')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'created_at')
    ordering = ('id',)
    readonly_fields = ('created_at', 'updated_at')

    list_display_links = ('email', 'username', 'alias_name')
    list_per_page = 20

