import hashlib
import mimetypes
import re
import secrets
import string
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.core.files import File as DjangoFile
from bs4 import BeautifulSoup, FeatureNotFound
from celery import chain
from celery.utils.log import get_task_logger
from django.db import transaction
from requests import HTTPError

from capellawish.celery import app
from wishlist.models import WishItem, ItemSource, BlobImage

logger = get_task_logger(__name__)


@app.task(bind=True, track_started=True)
def retrieve_data_from_url(self, url: str, id: int, skip_image: bool) -> None:
    retrieved = retrieve_data(url)
    if not retrieved:
        raise ValueError('Failed to retrieve data from url')

    if not retrieved.get('image', None) or skip_image:
        # Call the save task directly
        chain(save_data.s(retrieved, id)).apply_async()
    else:
        if isinstance(retrieved['image'], list):
            image = retrieved['image'][0]
        else:
            image = retrieved['image']

        chain(retrieve_image_from_url.s(image, retrieved),
              save_data.s(id)
              ).apply_async()
    return

@app.task(bind=True, track_started=True)
def retrieve_image_from_url(self, url: str, data: dict) -> dict:
    try:
        image_path = fetch_image(url)
        if not image_path:
            raise Exception('Failed to retrieve image data from URL.')
    except HTTPError as e:
        logger.error('Failed to get image data from URL')
        return data
    except Exception as e:
        logger.exception('Failed to process image data from URL.', e)
        raise e

    data['image'] = str(image_path)
    return data

@app.task(bind=True, track_started=True)
def save_data(self, data: dict, id: int) -> None:
    try:
        with transaction.atomic():
            target = WishItem.objects.select_for_update().get(id=id)
            if not target.title:
                target.title = data['title']
            if not target.description:
                target.description = data['description']
            image_path = data.get('image', None)
            if not target.image and image_path:
                if isinstance(image_path, (str, Path)) and Path(image_path).exists():
                    p = Path(image_path)
                    filename = p.name
                    with open(p, 'rb') as f:
                        hash = hashlib.file_digest(f, 'sha256').hexdigest()

                        existing = BlobImage.objects.filter(sha256_hash=hash).first()
                        if existing:
                            target.image = existing
                        else:
                            django_file = DjangoFile(f, name=filename)
                            blob = BlobImage()
                            blob.image.save(filename, django_file)
                            blob.sha256_hash = hash
                            blob.save()
            target.save()
    except (WishItem.DoesNotExist, ItemSource.DoesNotExist) as exc:
        logger.info(f'WishItem or ItemSource does not exist: {exc}')
        raise exc
    except Exception as exc:
        logger.exception('Failed to save data: %s', exc)
        raise exc
    else:
        if data.get('image', None):
            Path.unlink(data['image'], missing_ok=True)


def parse_opengraph_properties(soup: BeautifulSoup,
                               pattern_str: str | None = None) -> dict | None:
    """Parse OpenGraph properties from a BeautifulSoup object."""
    if not soup:
        logger.info('No valid crawled webpage provided. Cannot extract data.')
        raise ValueError('No valid crawled webpage provided. Cannot extract data.')
    pattern = re.compile(r'^og:' if not pattern_str else fr'{pattern_str}', re.IGNORECASE)
    meta_objects = soup.find_all('meta',
                                 attrs={'property': pattern,
                                        'content': True})
    rt = {}
    for m in meta_objects:
        prop = (m.get('property') or '').strip().removeprefix('og:')
        content = (m.get('content') or '').strip()
        if not prop or not content:
            continue

        existing = rt.get(prop, None)
        if not existing:
            rt[prop] = content
        elif isinstance(existing, list):
            existing.append(content)
        else:
            rt[prop] = [existing, content]
    return rt

def create_soup(response: requests.Response,
                parser: str = 'lxml') -> BeautifulSoup | None:
    """Create a BeautifulSoup object from the HTTP response content."""
    try:
        soup = BeautifulSoup(response.content, parser)
    except FeatureNotFound:
        logger.warning('Parser %s not found. Falling back to \'lxml\'.', parser)
        return BeautifulSoup(response.content, 'lxml')
    except Exception as e:
        logger.exception('Unexpected error while parsing the page: %s', e)
        return None
    return soup

def fetch_page_from_url(url: str,
                        headers: dict | None = None,
                        timeout: int = 10) -> requests.Response | None:
    """Fetches a web page from the given URL with specified headers and timeout."""
    if not headers:
        headers = {}
    if headers.get('user-agent') is None:
        logger.warning('No proper user agent provided. Setting a common one to avoid blocking.')
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0'
        logger.info('Using user agent: %s', user_agent)
        headers.update({'user-agent': user_agent})
    try:
        # Retrieving the data from the URL
        logger.debug(f'Try fetching page from URL {url}')
        page_response = requests.get(url, headers=headers, timeout=timeout)
        page_response.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        logger.exception('Could not retrieve page from %s: %s', url, e)
        return None
    except requests.exceptions.RequestException as e:
        logger.exception('Request exception occurred while retrieving page from %s: %s', url, e)
        return None
    return page_response

def retrieve_data(url: str) -> dict | None:
    """
    Retrieves product data from the given URL from a request user.
    Returns a dictionary with product data or None if retrieval fails.

    Necessary data:
    title, image, type (metadata)

    Optional:
    description, price (metadata)
    """
    fetched_page = fetch_page_from_url(url, headers={'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0'},
                                       timeout=10)
    soup = create_soup(fetched_page, 'lxml')

    try:
        data = {}
        # Try to extract OpenGraph properties
        og_props = parse_opengraph_properties(soup)
        # Note: Parsing tags directly is not implemented yet.
        if not og_props:
            logger.info(f'No OpenGraph properties found in the page: {url}')
    except Exception as e:
        logger.exception('Unexpected error while parsing the page: %s', e)
        return None

    if len(og_props) > 0:
        data.update(og_props)
    return data

def get_filename(url: str) -> str:
    filename = urlparse(url).path.split('/')[-1]
    return filename

def has_file_extension(target: str) -> bool:
    idx = target.rfind('.')
    return False if idx == -1 else True

def guess_filename(url: str, response: requests.Response) -> str:
    rt = get_filename(url)
    if not has_file_extension(rt):
        if len(rt) > 20:
            rand_filename = '_' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
            rt += rand_filename
        ext = mimetypes.guess_extension(response.headers.get('content-type'))
        if not ext:
            ext = '.bin'
        rt += ext
    return rt

def fetch_image(url: str) -> Path | None:
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0'})
    response.raise_for_status()
    filename = guess_filename(url, response)
    final_basepath = Path(__file__).parent.parent / 'data' / 'temp'

    if not Path.exists(final_basepath):
        Path.mkdir(final_basepath)
    final_path = final_basepath / filename

    with open(final_path, 'wb') as f:
        f.write(response.content)
    return final_path
