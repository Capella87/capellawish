import secrets
from typing import Any, Generator

import pytest
from allauth.account.models import EmailAddress
from pytest_django import DjangoDbBlocker
from rest_framework.status import HTTP_201_CREATED
from rest_framework.test import APIClient
from account.models import WishListUser


# Note: You must grant CREATEDB role to the client user of database (Postgres).
# e.g) ALTER ROLE capellauser CREATEDB;
@pytest.fixture(scope='function')
def api_client() -> Generator[APIClient, Any, None]:
    """
    Provides a DRF APIClient instance for testing. (DRF one is the extension of Django one)
    :return: APIClient instance
    """
    yield APIClient()

@pytest.fixture(autouse=True)
def disable_file_logging(settings: dict) -> None:
    """
    Disables file logging during unit tests.
    :param settings: Django settings dictionary
    :return:
    """
    settings.LOGGING['loggers']['django']['handlers'] = ['console']

@pytest.fixture(autouse=True, scope='session')
def admin_user(django_db_setup: Any, django_db_blocker: DjangoDbBlocker) -> WishListUser:
    """
    Creates a user with admin privileges for testing.
    :param django_db_setup: Method to set up the test database
    :param django_db_blocker: Django DB blocker for managing DB access
    :return: WishListUser instance with admin rights
    """
    from django.conf import settings as django_settings
    client = APIClient()
    django_settings.ACCOUNT_EMAIL_VERIFICATION = 'none'

    username = 'admin'
    email = 'admin@example.com'
    password = secrets.token_urlsafe(16)
    with django_db_blocker.unblock():
        client.post('/api/auth/signup/',
                    data={'email': email, 'password': password, 'password2': password, 'username': username },
                    content_type='application/json',
                    HTTP_USER_AGENT='Mozilla/5.0 pytest-agent/1.0')
        created_user = WishListUser.objects.get(email=email)
        created_user.is_active = True
        created_user.is_staff = True
        created_user.is_superuser = True
        created_user.save()

        email_obj = EmailAddress.objects.get(email=email)
        email_obj.verified = True
        email_obj.save()

    return created_user

@pytest.fixture(autouse=True, scope='function')
def authenticated_client(api_client: APIClient, admin_user: WishListUser) -> APIClient:
    """
    Provides an authenticated APIClient instance for testing.
    :param api_client: A normal and unauthenticated APIClient instance
    :param admin_user: A WishListUser instance to authenticate with (Admin)
    :return: The authenticated APIClient instance
    """
    api_client.force_authenticate(admin_user)
    return api_client

@pytest.fixture
def sample_wishlist_data() -> dict:
    """
    Provides sample data for creating a wishlist item.
    :return: A WishListItem data dictionary
    """
    data = {
        'title': 'Sample Product',
        'description': 'This is a sample.',
        'is_public': False,
        'is_completed': False,
        'is_starred': False,
        'sources': [
            {
                'source_url': 'https://example.com',
                'source_name': 'SampleMarket',
            }
        ]
    }
    return data

@pytest.fixture
def sample_wishlist_item(authenticated_client: APIClient, sample_wishlist_data: dict) -> dict:
    """
    Creates and provides a sample WishListItem for testing.
    :param authenticated_client: An authenticated APIClient instance
    :param sample_wishlist_data: A sample item data dictionary
    :return: The created WishListItem data dictionary
    """
    response = authenticated_client.post('/api/item/',
                                         data=sample_wishlist_data,
                                         content_type='application/json')
    assert response.status_code == HTTP_201_CREATED
    return response.data
