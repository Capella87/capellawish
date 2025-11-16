import logging

import pytest
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK
from rest_framework.test import APIClient

from account.models import WishListUser
from wishlist.models import WishItem

logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_create_wishlist_item(authenticated_client: APIClient, sample_wishlist_data: dict) -> None:
    response = authenticated_client.post('/api/item/',
                                         data=sample_wishlist_data,
                                         content_type='application/json')
    assert response.status_code == HTTP_201_CREATED
    data = response.data

    assert response.data['title'] == data['title']
    assert response.data['description'] == data['description']
    assert response.data['is_starred'] == data['is_starred']
    assert response.data['is_public'] == data['is_public']

    assert response.data['sources'][0]['source_url'] == data['sources'][0]['source_url']
    assert response.data['sources'][0]['source_name'] == data['sources'][0]['source_name']

@pytest.mark.django_db
def test_retrieve_wishlist_item_detail_by_uuid(authenticated_client: APIClient,
                                               admin_user: WishListUser,
                                               sample_wishlist_item: dict) -> None:
    target = WishItem.objects.get(uuid=sample_wishlist_item['uuid'])
    assert target is not None
    uuid = target.uuid
    response = authenticated_client.get(f'/api/item/{uuid}')

    assert response.status_code == HTTP_200_OK
    assert response.data['title'] == target.title
    assert response.data['description'] == target.description
    assert response.data['is_starred'] == target.is_starred
    assert response.data['is_public'] == target.is_public

@pytest.mark.django_db
def test_retrieve_wishlist_items(authenticated_client: APIClient,
                                 admin_user: WishListUser,
                                 sample_wishlist_item: dict) -> None:
    targets = WishItem.objects.filter(user_id=admin_user.pk)
    assert targets is not None
    response = authenticated_client.get(f'/api/item/')

    assert response.status_code == HTTP_200_OK
    assert len(response.data['results']) > 0
