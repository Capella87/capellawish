from typing import override

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth import password_validation
from django.contrib.auth.models import User

from django.utils.translation import gettext_lazy as _

class WishListUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email: str, username: str, password: str | None = None, **extra_fields) -> AbstractUser:
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a valid username')
        extra_fields['is_staff'] = False
        extra_fields['is_superuser'] = False

        email = self.normalize_email(email)
        username = self.model.normalize_username(username)

        new_user = self.model(email=email, username=username, **extra_fields)

        password_validation.validate_password(password, new_user)
        new_user.set_password(password)

        new_user.save(using=self._db)
        return new_user

    def create_superuser(self, email: str, username: str, password: str = None, **extra_fields) -> AbstractUser:
        created_user = self.create_user(email, username, password, **extra_fields)
        created_user.is_superuser = created_user.is_staff = True
        created_user.save(using=self._db)

        return created_user


# Create your models here.

class WishListUser(AbstractUser):

    username_validator = UnicodeUsernameValidator()

    id = models.AutoField(primary_key=True)
    email = models.EmailField(_('email address'), unique=True, blank=False, editable=True)
    is_verified_user = models.BooleanField(_('verified user by email or phone verification'), default=False)
    username = models.CharField(
        _('username'),
        max_length=200,
        unique=True,
        editable=True,
        help_text=_(
            'Required. 200 characters or fewer. Letters, digits and @/./+/-/_ only.'
        ),
        validators=[username_validator],
        error_messages={
            "unique": _('A user with that username already exists.'),
        },
    )
    alias_name = models.CharField(max_length=150, blank=True, editable=True, unique=False)
    middle_name = models.CharField(_('middle name'), max_length=150, blank=True, editable=True)
    is_superuser = models.BooleanField(_('superuser status'), default=False)
    date_updated = models.DateTimeField(_('date updated'), auto_now=True)

    profile_image = models.ImageField(_('profile image'),
                                      upload_to='users/profile/',
                                      blank=True, null=True)
    bio = models.TextField(_('bio'), blank=True, editable=True)
    birthday = models.DateField(_('date of birth'), null=True, blank=True, editable=True) # Optional

    ## TODO: Passkey and 2FA

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    USERNAME_VALIDATOR = UnicodeUsernameValidator()
    objects = WishListUserManager()
