from typing import override

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, AbstractUser


class WishListUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email: str, username: str, password: str = None, **extra_fields) -> AbstractBaseUser:
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a valid username')
        email = self.normalize_email(email)

        new_user = WishListUser(email=email, username=username, **extra_fields)
        new_user.set_password(password)
        new_user.save(using=self._db)
        return new_user

    def create_superuser(self, email: str, username: str, password: str = None, **extra_fields) -> AbstractBaseUser:
        created_user = self.create_user(email, username, password, **extra_fields)
        created_user.is_superuser = created_user.is_staff = True
        created_user.save(using=self._db)

        return created_user


# Create your models here.

class WishListUser(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True, blank=False, editable=True)
    username = models.CharField(unique=True, blank=False, editable=True)
    first_name = models.CharField(max_length=150, blank=True, editable=True)
    last_name = models.CharField(max_length=150, blank=True, editable=True)
    alias_name = models.CharField(max_length=150, blank=True, editable=True, unique=False)
    surname = models.CharField(max_length=150, blank=True, editable=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    objects = WishListUserManager()
