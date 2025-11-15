import logging

import pytest
from rest_framework.test import APIClient

logger = logging.getLogger(__name__)

@pytest.mark.django_db
def test_send_get_request(api_client: APIClient) -> None:
    response = api_client.get('/api/', HTTP_USER_AGENT='Mozilla/5.0 pytest-agent/1.0')
    logger.info(response.data)

    assert response.status_code == 200
    assert response.data.get('user_agent', None) is not None

@pytest.mark.django_db
def test_send_post_request(api_client: APIClient) -> None:
    title = 'TEST'
    description = 'This is a test description.'

    payload = {
        'title': title,
        'description': description
    }
    user_agent = 'Mozilla/5.0 pytest-agent/1.0'
    response = api_client.post('/api/', data=payload,
                               content_type='application/json',
                               HTTP_USER_AGENT=user_agent)
    logger.info(response.data)

    assert response.status_code == 200
    assert response.data.get('user_agent', None) is not None
    assert response.data.get('title', None) == title
    assert response.data.get('description', None) == description
