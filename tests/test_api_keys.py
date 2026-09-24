import pytest


@pytest.mark.django_db
def test_create_api_key(api_client, admin_headers):
    resp = api_client.post('/api/v1/api-keys/', {'name': 'Client A'}, format='json', **admin_headers)
    assert resp.status_code == 201
    assert 'key' in resp.data
    assert 'key_hash' not in resp.data


@pytest.mark.django_db
def test_list_api_keys(api_client, admin_headers):
    api_client.post('/api/v1/api-keys/', {'name': 'Client B'}, format='json', **admin_headers)
    resp = api_client.get('/api/v1/api-keys/', **admin_headers)
    assert resp.status_code == 200
    for item in resp.data['results']:
        assert 'key_hash' not in item
        assert 'key' not in item


@pytest.mark.django_db
def test_revoke_api_key(api_client, admin_headers):
    create_resp = api_client.post('/api/v1/api-keys/', {'name': 'Client C'}, format='json', **admin_headers)
    key_id = create_resp.data['id']
    resp = api_client.delete(f'/api/v1/api-keys/{key_id}/', **admin_headers)
    assert resp.status_code == 204


@pytest.mark.django_db
def test_missing_admin_header_rejected(api_client):
    resp = api_client.post('/api/v1/api-keys/', {'name': 'Client D'}, format='json')
    assert resp.status_code == 403


@pytest.mark.django_db
def test_wrong_admin_header_rejected(api_client):
    resp = api_client.post(
        '/api/v1/api-keys/', {'name': 'Client E'}, format='json', HTTP_X_ADMIN_KEY='wrong-key'
    )
    assert resp.status_code == 403
