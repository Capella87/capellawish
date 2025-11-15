from typing import Any, Generator

import pytest
from rest_framework.test import APIClient

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
    :return: None
    """
    settings.LOGGING['loggers']['django']['handlers'] = ['console']
