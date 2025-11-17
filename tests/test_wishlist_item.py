import logging

import pytest
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_204_NO_CONTENT
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

@pytest.mark.django_db
@pytest.mark.parametrize('test_property,test_input,test_expected',
                         [('is_starred', True, True),
                          ('is_public', True, True)])
def test_patch_update_wishlist_item(authenticated_client: APIClient,
                                    admin_user: WishListUser,
                                    sample_wishlist_item: dict,
                                    test_property: str,
                                    test_input: str,
                                    test_expected: str) -> None:
    uuid = sample_wishlist_item['uuid']
    assert WishItem.objects.filter(uuid=uuid).exists()

    data = {test_property: test_input}
    response = authenticated_client.patch(f'/api/item/{uuid}',
                                          data=data,
                                          content_type='application/json')
    modified_target = WishItem.objects.get(uuid=uuid)

    assert response.status_code == HTTP_204_NO_CONTENT
    assert getattr(modified_target, test_property)  == test_expected

@pytest.mark.django_db
def test_delete_wishlist_item(authenticated_client: APIClient,
                              admin_user: WishListUser,
                              sample_wishlist_item: dict) -> None:
    uuid = sample_wishlist_item['uuid']
    assert WishItem.objects.get(uuid=uuid).deleted_at is None
    response = authenticated_client.delete(f'/api/item/{uuid}')

    assert response.status_code == HTTP_204_NO_CONTENT
    assert WishItem.objects.get(uuid=uuid).deleted_at

@pytest.mark.django_db
def test_put_wishlist_item(authenticated_client: APIClient,
                           admin_user: WishListUser,
                           sample_wishlist_item: dict) -> None:
    uuid = sample_wishlist_item['uuid']
    assert WishItem.objects.filter(uuid=uuid).exists()

    old_entity_sources = sample_wishlist_item['sources'][0]
    data = sample_wishlist_item.copy()
    data['sources'] = [{
        'source_name': 'Test Source modified',
        'source_url': 'https://example2.com'
    }]
    response = authenticated_client.put(f'/api/item/{uuid}',
                                        data=data,
                                        content_type='application/json')

    assert response.data['title'] == data['title']
    assert response.data['description'] == data['description']
    assert response.data['is_starred'] == data['is_starred']
    assert response.data['sources'][0]['source_name'] != old_entity_sources['source_name']
    assert response.data['sources'][0]['uuid'] != old_entity_sources['uuid']
