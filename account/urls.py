from django.urls import path, re_path
from django.views.generic import TemplateView

from account.views import UserAccountSignUpView, UserAccountView, UserPasswordView, EmailConfirmationView, \
    ResendEmailConfirmationView
from dj_rest_auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView,
)

app_name = 'account'

urlpatterns = [
# path('api/auth/', include('dj_rest_auth.urls')),
    re_path(r'account/?$', UserAccountView.as_view(), name='user'),
    re_path(r'password/change/?$', UserPasswordView.as_view(), name='password_change'),
    re_path(r'signup/?$', UserAccountSignUpView.as_view(), name='sign_up'),
    re_path(r'account/confirm-email/?$', EmailConfirmationView.as_view(), name='account_confirm_email'),
    re_path(r'account/resend-email/?$', ResendEmailConfirmationView.as_view(), name='rest_resend_email'),

    # re_path(
    #     r'^account/confirm-email/(?P<key>[-:\w]+)/$', TemplateView.as_view(),
    #     name='',
    # ),
    re_path(
        r'account/email-verification-sent/?$', TemplateView.as_view(),
        name='account_email_verification_sent',
    ),


    # dj-rest-auth URLs
    re_path(r'login/?$', LoginView.as_view(), name='rest_login'),
    # URLs that require a user to be logged in with a valid session / token.
    re_path(r'logout/?$', LogoutView.as_view(), name='rest_logout'),
    re_path(r'password/reset/?$', PasswordResetView.as_view(), name='rest_password_reset'),
    re_path(r'password/reset/confirm/?$', PasswordResetConfirmView.as_view(), name='rest_password_reset_confirm'),
]

from dj_rest_auth.app_settings import api_settings as rest_auth_settings
if rest_auth_settings.USE_JWT:
    from rest_framework_simplejwt.views import TokenVerifyView
    from dj_rest_auth.jwt_auth import get_refresh_view

    urlpatterns += [
        re_path(r'token/verify/?$', TokenVerifyView.as_view(), name='token_verify'),
        re_path(r'token/refresh/?$', get_refresh_view().as_view(), name='token_refresh'),
    ]
