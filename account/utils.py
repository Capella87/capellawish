from allauth.account.utils import user_pk_to_url_str
from allauth.utils import build_absolute_uri
from dj_rest_auth.app_settings import api_settings
from django.contrib.auth.models import AbstractUser
from django.http import HttpRequest
from django.urls import reverse

from account.models import WishListUser


def password_reset_url_generator(request: HttpRequest, user: WishListUser | AbstractUser, key):
    path = reverse('account:password_reset_confirm',
                   # args=[user_pk_to_url_str(user)],
                   current_app='account',
                   query={
                       'uid': user_pk_to_url_str(user),
                       'key': str(key),
                   })
    if api_settings.PASSWORD_RESET_USE_SITES_DOMAIN:
        url = build_absolute_uri(None, path)
    else:
        url = build_absolute_uri(request, path)
    url = url.replace('%3F', '?')

    return url
