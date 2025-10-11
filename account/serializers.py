from typing import override

from django.contrib.auth import password_validation
from django.contrib.auth.models import AbstractUser
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
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


class UserAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishListUser
        fields = ['email', 'username', 'first_name', 'last_name', 'alias_name', 'middle_name']
        read_only_fields = ['email', 'username'] # Restrict changing email and username for now.


class UserPasswordChangeSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(max_length=200, required=True, allow_blank=False, write_only=True)
    password = serializers.CharField(max_length=200, required=True, allow_blank=False, write_only=True)
    password2 = serializers.CharField(max_length=200, required=True, allow_blank=False, write_only=True)

    @override
    def validate(self, attrs: dict) -> dict:
        if not attrs.get('password') == attrs.get('password2'):
            raise serializers.ValidationError('The new passwords do not match.')

        if attrs.get('old_password') == attrs.get('password'):
            raise serializers.ValidationError('The new password must be different from the old password.')
        return attrs

    def validate_old_password(self, value: str) -> str:
        user = self.context.user

        if not user.check_password(value):
            raise serializers.ValidationError('The old password is incorrect.')
        return value

    @override
    def update(self, instance: AbstractUser, validated_data: dict) -> AbstractUser:
        new_password = validated_data.pop('password')
        password_validation.validate_password(new_password, instance)
        instance.set_password(new_password)
        instance.save()

        password_validation.password_changed(instance, new_password)

        return instance


    class Meta:
        model = WishListUser
        fields = ['old_password', 'password', 'password2']
