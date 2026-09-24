import os

import django
import pytest
from django.conf import settings
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_headers():
    return {'HTTP_X_ADMIN_KEY': settings.ADMIN_API_KEY}


@pytest.fixture
def api_key_raw(db, api_client, admin_headers):
    """Creates an API key via the admin endpoint and returns the raw key."""
    resp = api_client.post(
        '/api/v1/api-keys/',
        {'name': 'Test Client'},
        format='json',
        **admin_headers,
    )
    assert resp.status_code == 201, resp.content
    return resp.data['key']


@pytest.fixture
def auth_headers(api_key_raw):
    return {'HTTP_X_API_KEY': api_key_raw}
