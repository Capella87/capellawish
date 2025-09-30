from django.contrib import admin
from . import models

# Register your models here.

@admin.register(models.WishListUser)
class WishListUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'username', 'alias_name', 'first_name', 'last_name', 'is_active',
                    'is_staff', 'is_superuser', 'date_joined', 'date_updated')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'alias_name')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    ordering = ('id',)
    readonly_fields = ('date_joined', 'date_updated')

    list_display_links = ('email', 'username', 'alias_name')
    list_per_page = 20

