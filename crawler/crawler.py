import logging

import requests

logger = logging.getLogger(__name__)

image_types_and_ext = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/gif': 'gif',
    'image/webp': 'webp',
    'image/avif': 'avif',
}

def retrieve_image(url: str, headers: dict | None = None, timeout: int = 10) -> bytes | None:
    """Retrieve image data from a given URL. (synchronous)"""
    headers = headers or {}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        logger.info('Could not retrieve image from %s: %s', url, e)
        return None
    except requests.exceptions.RequestException as e:


