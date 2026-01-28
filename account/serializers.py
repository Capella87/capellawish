import logging
from typing import override

from allauth.account.internal.flows.email_verification import send_verification_email_for_user
from allauth.account.utils import setup_user_email, has_verified_email
from dj_rest_auth.serializers import PasswordResetSerializer, PasswordResetConfirmSerializer
from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import AbstractUser
from rest_framework import serializers
from allauth.account import app_settings as allauth_settings

from account.models import WishListUser
from account.utils import password_reset_url_generator

logger = logging.getLogger(__name__)


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

    def save(self, **kwargs) -> AbstractUser:
        user = super().save(**kwargs)
        request = self.context.get('request', None)
        setup_user_email(request, user, [])

        # Send a confirmation email if email verification is required
        if allauth_settings.EMAIL_VERIFICATION == allauth_settings.EmailVerificationMethod.MANDATORY:
            if not has_verified_email(user):
                res = send_verification_email_for_user(request, user)
                if not res:
                    raise serializers.ValidationError('Failed to send verification email. It may be due to rate limiting.')
            else:
                raise serializers.ValidationError('Email verification failed.')
        return user

    class Meta:
        model = WishListUser
        fields = ['email', 'username', 'first_name', 'last_name',
                  'alias_name', 'middle_name', 'password', 'password2', 'birthday']


class UserAccountSerializer(serializers.ModelSerializer):

    # Ensure read-only fields are not modified
    def check_readonly_data(self, data: dict) -> None:
        for field in self.Meta.read_only_fields:
            if field in data:
                raise serializers.ValidationError(f'The field \'{field}\' is read-only and cannot be modified.')

    @override
    def validate(self, attrs: dict) -> dict:
        self.check_readonly_data(self.initial_data)
        return attrs

    class Meta:
        model = WishListUser
        fields = ['email', 'username', 'first_name', 'last_name', 'alias_name', 'middle_name',
                  'is_staff', 'is_superuser', 'bio', 'profile_image', 'birthday']
        read_only_fields = ['email', 'username', 'is_staff', 'is_superuser', 'profile_image']


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
        request = self.context.get('request', None)
        if not request:
            raise serializers.ValidationError('Failed to retrieve the user.')
        user = request.user

        if not user.check_password(value):
            raise serializers.ValidationError('The old password is incorrect.')
        return value

    @override
    def update(self, instance: AbstractUser, validated_data: dict) -> AbstractUser:
        new_password = validated_data.pop('password')
        password_validation.validate_password(new_password, instance)
        instance.set_password(new_password)
        instance.save()
        password_validation.password_changed(new_password, instance)

        return instance


    class Meta:
        model = WishListUser
        fields = ['old_password', 'password', 'password2']


class JWTTokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class JWTTokenWithExpirationSerializer(JWTTokenSerializer):
    access_expiration = serializers.DateTimeField()
    refresh_expiration = serializers.DateTimeField()


class EmailConfirmationSerializer(serializers.Serializer):
    key = serializers.CharField()


class ResendEmailConfirmationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=allauth_settings.SIGNUP_FIELDS['email']['required'])


class ResetPasswordSerializer(PasswordResetSerializer):
    @override
    def save(self):
        if 'allauth' in settings.INSTALLED_APPS:
            from allauth.account.forms import default_token_generator
        else:
            from django.contrib.auth.tokens import default_token_generator
        request = self.context.get('request', None)
        opts = {
            'use_https': request.is_secure(),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),
            'request': request,
            'token_generator': default_token_generator,
            'url_generator': password_reset_url_generator
        }
        opts.update(self.get_email_options())
        self.reset_form.save(**opts)


class ResetPasswordConfirmSerializer(PasswordResetConfirmSerializer):
    new_password1 = serializers.CharField(max_length=200, required=True, allow_blank=False, write_only=True)
    new_password2 = serializers.CharField(max_length=200, required=True, allow_blank=False, write_only=True)

    set_password_from_class = SetPasswordForm
