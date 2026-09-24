import pytest


ORDER_PAYLOAD = {
    'product_name': 'Wireless Mouse',
    'quantity': 2,
    'total_amount': '39.98',
}


@pytest.mark.django_db
def test_create_order(api_client, auth_headers):
    resp = api_client.post('/api/v1/orders/', ORDER_PAYLOAD, format='json', **auth_headers)
    assert resp.status_code == 201
    assert resp.data['status'] == 'PENDING'
    assert resp.data['product_name'] == 'Wireless Mouse'


@pytest.mark.django_db
def test_create_order_missing_header_401(api_client):
    resp = api_client.post('/api/v1/orders/', ORDER_PAYLOAD, format='json')
    assert resp.status_code == 401


@pytest.mark.django_db
def test_create_order_invalid_quantity(api_client, auth_headers):
    payload = dict(ORDER_PAYLOAD, quantity=0)
    resp = api_client.post('/api/v1/orders/', payload, format='json', **auth_headers)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_create_order_invalid_amount(api_client, auth_headers):
    payload = dict(ORDER_PAYLOAD, total_amount='0')
    resp = api_client.post('/api/v1/orders/', payload, format='json', **auth_headers)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_list_orders(api_client, auth_headers):
    api_client.post('/api/v1/orders/', ORDER_PAYLOAD, format='json', **auth_headers)
    resp = api_client.get('/api/v1/orders/', **auth_headers)
    assert resp.status_code == 200
    assert resp.data['count'] >= 1


@pytest.mark.django_db
def test_retrieve_order(api_client, auth_headers):
    create_resp = api_client.post('/api/v1/orders/', ORDER_PAYLOAD, format='json', **auth_headers)
    order_id = create_resp.data['id']
    resp = api_client.get(f'/api/v1/orders/{order_id}/', **auth_headers)
    assert resp.status_code == 200
    assert resp.data['id'] == order_id


@pytest.mark.django_db
def test_retrieve_order_wrong_owner_404(api_client, auth_headers, api_client2_headers):
    create_resp = api_client.post('/api/v1/orders/', ORDER_PAYLOAD, format='json', **auth_headers)
    order_id = create_resp.data['id']
    resp = api_client.get(f'/api/v1/orders/{order_id}/', **api_client2_headers)
    assert resp.status_code == 404


@pytest.mark.django_db
def test_update_order_pending(api_client, auth_headers):
    create_resp = api_client.post('/api/v1/orders/', ORDER_PAYLOAD, format='json', **auth_headers)
    order_id = create_resp.data['id']
    update_payload = dict(ORDER_PAYLOAD, product_name='Updated Mouse')
    resp = api_client.put(f'/api/v1/orders/{order_id}/', update_payload, format='json', **auth_headers)
    assert resp.status_code == 200
    assert resp.data['product_name'] == 'Updated Mouse'


@pytest.mark.django_db
def test_status_transition_valid(api_client, auth_headers):
    create_resp = api_client.post('/api/v1/orders/', ORDER_PAYLOAD, format='json', **auth_headers)
    order_id = create_resp.data['id']
    resp = api_client.patch(f'/api/v1/orders/{order_id}/status/', {'status': 'CONFIRMED'}, format='json', **auth_headers)
    assert resp.status_code == 200
    assert resp.data['status'] == 'CONFIRMED'


@pytest.mark.django_db
def test_status_transition_invalid(api_client, auth_headers):
    create_resp = api_client.post('/api/v1/orders/', ORDER_PAYLOAD, format='json', **auth_headers)
    order_id = create_resp.data['id']
    resp = api_client.patch(f'/api/v1/orders/{order_id}/status/', {'status': 'SHIPPED'}, format='json', **auth_headers)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_update_order_after_confirmed_rejected(api_client, auth_headers):
    create_resp = api_client.post('/api/v1/orders/', ORDER_PAYLOAD, format='json', **auth_headers)
    order_id = create_resp.data['id']
    api_client.patch(f'/api/v1/orders/{order_id}/status/', {'status': 'CONFIRMED'}, format='json', **auth_headers)
    resp = api_client.put(f'/api/v1/orders/{order_id}/', ORDER_PAYLOAD, format='json', **auth_headers)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_delete_order_pending(api_client, auth_headers):
    create_resp = api_client.post('/api/v1/orders/', ORDER_PAYLOAD, format='json', **auth_headers)
    order_id = create_resp.data['id']
    resp = api_client.delete(f'/api/v1/orders/{order_id}/', **auth_headers)
    assert resp.status_code == 204


@pytest.mark.django_db
def test_delete_order_confirmed_rejected(api_client, auth_headers):
    create_resp = api_client.post('/api/v1/orders/', ORDER_PAYLOAD, format='json', **auth_headers)
    order_id = create_resp.data['id']
    api_client.patch(f'/api/v1/orders/{order_id}/status/', {'status': 'CONFIRMED'}, format='json', **auth_headers)
    resp = api_client.delete(f'/api/v1/orders/{order_id}/', **auth_headers)
    assert resp.status_code == 400


@pytest.fixture
def api_client2_headers(api_client, admin_headers):
    resp = api_client.post('/api/v1/api-keys/', {'name': 'Client Two'}, format='json', **admin_headers)
    return {'HTTP_X_API_KEY': resp.data['key']}


def _make_delivered_order(api_client, auth_headers):
    create_resp = api_client.post('/api/v1/orders/', ORDER_PAYLOAD, format='json', **auth_headers)
    order_id = create_resp.data['id']
    api_client.patch(f'/api/v1/orders/{order_id}/status/', {'status': 'CONFIRMED'}, format='json', **auth_headers)
    api_client.patch(f'/api/v1/orders/{order_id}/status/', {'status': 'SHIPPED'}, format='json', **auth_headers)
    api_client.patch(f'/api/v1/orders/{order_id}/status/', {'status': 'DELIVERED'}, format='json', **auth_headers)
    return order_id


@pytest.mark.django_db
def test_return_requested_from_delivered_valid(api_client, auth_headers):
    order_id = _make_delivered_order(api_client, auth_headers)
    resp = api_client.patch(
        f'/api/v1/orders/{order_id}/status/',
        {'status': 'RETURN_REQUESTED', 'reason': 'Item defective'},
        format='json', **auth_headers,
    )
    assert resp.status_code == 200
    assert resp.data['status'] == 'RETURN_REQUESTED'
    assert resp.data['return_reason'] == 'Item defective'


@pytest.mark.django_db
def test_return_requested_missing_reason_400(api_client, auth_headers):
    order_id = _make_delivered_order(api_client, auth_headers)
    resp = api_client.patch(
        f'/api/v1/orders/{order_id}/status/',
        {'status': 'RETURN_REQUESTED'},
        format='json', **auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_return_requested_empty_reason_400(api_client, auth_headers):
    order_id = _make_delivered_order(api_client, auth_headers)
    resp = api_client.patch(
        f'/api/v1/orders/{order_id}/status/',
        {'status': 'RETURN_REQUESTED', 'reason': '   '},
        format='json', **auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_return_requested_from_non_delivered_invalid(api_client, auth_headers):
    create_resp = api_client.post('/api/v1/orders/', ORDER_PAYLOAD, format='json', **auth_headers)
    order_id = create_resp.data['id']
    resp = api_client.patch(
        f'/api/v1/orders/{order_id}/status/',
        {'status': 'RETURN_REQUESTED', 'reason': 'Changed my mind'},
        format='json', **auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_refunded_from_return_requested_valid(api_client, auth_headers):
    order_id = _make_delivered_order(api_client, auth_headers)
    api_client.patch(
        f'/api/v1/orders/{order_id}/status/',
        {'status': 'RETURN_REQUESTED', 'reason': 'Item defective'},
        format='json', **auth_headers,
    )
    resp = api_client.patch(
        f'/api/v1/orders/{order_id}/status/',
        {'status': 'REFUNDED'},
        format='json', **auth_headers,
    )
    assert resp.status_code == 200
    assert resp.data['status'] == 'REFUNDED'


@pytest.mark.django_db
def test_refunded_from_non_return_requested_invalid(api_client, auth_headers):
    order_id = _make_delivered_order(api_client, auth_headers)
    resp = api_client.patch(
        f'/api/v1/orders/{order_id}/status/',
        {'status': 'REFUNDED'},
        format='json', **auth_headers,
    )
    assert resp.status_code == 400
