from django.conf import settings
from django.urls import path, re_path

from account import views
from django.urls import path, include
from rest_framework import urls
from rest_framework import views

from account.views import UserAccountSignUpView, UserAccountView, UserPasswordView
from dj_rest_auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView,
)

app_name = 'account'

urlpatterns = [
# path('api/auth/', include('dj_rest_auth.urls')),
    re_path(r'account/?$', UserAccountView.as_view(), name='user'),
    re_path(r'password/change/?$', UserPasswordView.as_view(), name='password_change'),
    re_path(r'signup/?$', UserAccountSignUpView.as_view(), name='sign_up'),
    # TODO: Email Verification for account activation

    # dj-rest-auth URLs
    re_path(r'login/?$', LoginView.as_view(), name='rest_login'),
    # URLs that require a user to be logged in with a valid session / token.
    re_path(r'logout/?$', LogoutView.as_view(), name='rest_logout'),
    re_path(r'password/reset/?$', PasswordResetView.as_view(), name='rest_password_reset'),
    re_path(r'password/reset/confirm/?$', PasswordResetConfirmView.as_view(), name='rest_password_reset_confirm'),
]

if settings.REST_AUTH and settings.REST_AUTH.get('USE_JWT'):
    from rest_framework_simplejwt.views import TokenVerifyView
    from dj_rest_auth.jwt_auth import get_refresh_view

    urlpatterns += [
        re_path(r'token/verify/?$', TokenVerifyView.as_view(), name='token_verify'),
        re_path(r'token/refresh/?$', get_refresh_view().as_view(), name='token_refresh'),
    ]
