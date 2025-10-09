from typing import override

from django.contrib.auth.models import AbstractUser
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from account.models import WishListUser


class UserSignUpSerializer(serializers.ModelSerializer):
    """
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True, blank=False, editable=True)
    username = models.CharField(unique=True, blank=False, editable=True)
    first_name = models.CharField(max_length=150, blank=True, editable=True)
    last_name = models.CharField(max_length=150, blank=True, editable=True)
    alias_name = models.CharField(max_length=150, blank=True, editable=True, unique=False)
    middle_name = models.CharField(max_length=150, blank=True, editable=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    """
    password = serializers.CharField(max_length=200, required=True, allow_blank=False, write_only=True)
    password2 = serializers.CharField(max_length=200, required=True, allow_blank=False, write_only=True)

    @override
    def validate(self, attrs: dict) -> dict:
        if not attrs.get('password') == attrs.get('password2'):
            raise serializers.ValidationError('Passwords do not match.')
        return attrs

    @override
    def create(self, validated_data: dict) -> AbstractUser:
        validated_data.pop('password2')
        user = self.Meta.model.objects.create_user(**validated_data)

        return user

    class Meta:
        model = WishListUser
        fields = ['email', 'username', 'first_name', 'last_name',
                  'alias_name', 'middle_name', 'password', 'password2']
