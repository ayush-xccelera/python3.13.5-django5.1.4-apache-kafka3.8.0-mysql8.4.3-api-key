# Order Management API

Django + Django REST Framework backend for managing client orders, authenticated via API keys,
with Kafka event publishing on order shipment and Swagger/OpenAPI documentation.

## Overview

Clients authenticate with an `X-API-Key` header. Each order belongs to the client that created it
(identified by the API key). Orders progress through a status workflow:
`PENDING -> CONFIRMED -> SHIPPED -> DELIVERED`, with `CANCELLED` reachable from `PENDING` or
`CONFIRMED`. When an order transitions to `SHIPPED`, an `ORDER_SHIPPED` event is published to the
Kafka topic `order-events`.

API keys themselves are managed via an admin-only endpoint gated by an `X-Admin-Key` header
(separate from client API keys).

## Setup

1. Python 3.13.5, MySQL 8.4.3.
2. Create/edit `.env_37f2c7be-75bb-4cae-beb4-ce442a7fa284` (already provided) with:
   - `SECRET_KEY`, `DEBUG`
   - `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
   - `ADMIN_API_KEY` (generated automatically; used only for `/api/v1/api-keys` management)
   - `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_ORDER_EVENTS_TOPIC`
3. Run:
   ```bash
   chmod +x start.sh
   PORT=25495 ./start.sh
   ```
   This creates a virtualenv, installs dependencies, runs migrations, and starts the server on
   port 25495 (overridable via `$PORT`).
4. Seed sample data:
   ```bash
   python3 manage.py seed
   ```

## Environment Variables

| Variable | Purpose |
|---|---|
| SECRET_KEY | Django secret key |
| DEBUG | Debug mode toggle |
| DB_ENGINE / DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT | MySQL connection |
| ADMIN_API_KEY | Required header value (`X-Admin-Key`) for API key management endpoints |
| KAFKA_BOOTSTRAP_SERVERS | Kafka broker address(es) |
| KAFKA_ORDER_EVENTS_TOPIC | Topic name for ORDER_SHIPPED events |
| PORT | HTTP port (default 25495) |

## Endpoints

All business endpoints require header `X-API-Key: <client key>`.
API key management endpoints require header `X-Admin-Key: <ADMIN_API_KEY>` instead.

| Method | Path | Description |
|---|---|---|
| POST | /api/v1/api-keys/ | Create a new client API key (admin only) |
| GET | /api/v1/api-keys/ | List API keys (admin only) |
| DELETE | /api/v1/api-keys/{id}/ | Revoke an API key (admin only) |
| POST | /api/v1/orders/ | Create an order |
| GET | /api/v1/orders/ | List caller's orders (paginated: `limit`, `offset`) |
| GET | /api/v1/orders/{id}/ | Retrieve one of caller's orders |
| PUT | /api/v1/orders/{id}/ | Update an order (only while PENDING) |
| PATCH | /api/v1/orders/{id}/status/ | Change order status (validated transitions) |
| DELETE | /api/v1/orders/{id}/ | Delete an order (only while PENDING or CANCELLED) |
| GET | /api/v1/docs | Swagger UI |
| GET | /api/v1/schema | Raw OpenAPI schema |

### Status transitions

```
PENDING -> CONFIRMED
PENDING -> CANCELLED
CONFIRMED -> SHIPPED
CONFIRMED -> CANCELLED
SHIPPED -> DELIVERED
```

## Kafka

On `PENDING/CONFIRMED -> SHIPPED` (i.e. any transition landing on `SHIPPED`), an `ORDER_SHIPPED`
event is published to topic `order-events` containing: order ID, owning client ID, product name,
quantity, and shipped timestamp. Publishing happens after the DB transaction commits.

## Tests

```bash
pip install -r requirements.txt
pytest -v
```

## Project Tree

```
config/            Django project settings, urls, wsgi/asgi
orders/            App: models, serializers, views, urls, auth, permissions, kafka_utils
orders/management/ seed command
tests/             pytest-django test suite
requirements.txt
start.sh / start.bat
.env_37f2c7be-75bb-4cae-beb4-ce442a7fa284
```
