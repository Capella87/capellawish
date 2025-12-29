from typing import override

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailConfirmationHMAC, EmailConfirmationMixin, EmailAddress
from allauth.core.internal.httpkit import get_frontend_url
from allauth.utils import build_absolute_uri
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest
from django.urls import reverse
from post_office import mail
from rest_framework.request import Request


class DjangoPostOfficeAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter that uses django-post-office to send emails asynchronously.
    """

    def get_support_email(self) -> str:
        return settings.SUPPORT_EMAIL if settings.SUPPORT_EMAIL else ''

    @override
    def send_mail(self, template_prefix: str, email: str, context: dict) -> None:
        ctx = {
            'current_site': get_current_site(self.request),
            'request': self.request,
            'email': email,
            'support_email': self.get_support_email()
        }
        ctx.update(context)
        message = self.render_mail(template_prefix, email, ctx)

        # TODO: Set priority to 'high' after configuring Celery.
        # Currently sending email immediately is too slow for user experience. (~4-5 seconds per request)
        mail.send(sender=message.from_email,
                  recipients=message.to,
                  subject=message.subject,
                  message=message.body,
                  headers=message.extra_headers,
                  priority='high',
                  render_on_delivery=False)

    @override
    def get_email_confirmation_url(self, request: HttpRequest | Request, emailconfirmation: EmailConfirmationHMAC | EmailConfirmationMixin) -> str:
        url = get_frontend_url(request, 'account:account_confirm_email', key=emailconfirmation.key)
        if not url:
            # query: Available on Django 5.2
            url = reverse('account:account_confirm_email', query={'key': emailconfirmation.key})
            url = build_absolute_uri(request, url)
        return url


def get_or_sync_user_email(user: AbstractBaseUser, email: str) -> EmailAddress:
    email_queryset = EmailAddress.objects.filter(user_id=user.pk, email=email)
    if not email_queryset.exists():
        email_entry, _ = EmailAddress.objects.get_or_create(user_id=user.pk, email=email, defaults={
            'verified': False,
            'primary': False,
        })
    else:
        email_entry = email_queryset.first()

    return email_entry
