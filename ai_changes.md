COMMIT_MESSAGE: Add order return/refund status transitions with return_reason field and ORDER_REFUNDED Kafka event

## Summary
The project already had an Order entity with basic status transitions and Kafka
shipping events. I was asked to add a return/refund workflow: a new
`return_reason` field, two new statuses (RETURN_REQUESTED, REFUNDED), validation
rules requiring a reason when requesting a return, and a new ORDER_REFUNDED
Kafka event published on refund. I extended the existing model, serializer,
view, and Kafka utility to support this, added a database migration, and wrote
tests covering every new transition and error case.

## Features Added
- Added `RETURN_REQUESTED` and `REFUNDED` values to the `Order.status` choices, alongside the existing PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED values.
- Added a nullable `return_reason` field on `Order`.
- Extended `PATCH /api/v1/orders/{id}/status` (existing endpoint, reused, no new route) to support:
  - `DELIVERED -> RETURN_REQUESTED`: valid only from DELIVERED, requires a non-empty `reason` field in the request body (persisted into `return_reason`). Missing/empty reason returns 400.
  - `RETURN_REQUESTED -> REFUNDED`: valid only from RETURN_REQUESTED, no extra fields required.
  - Any other transition into RETURN_REQUESTED or REFUNDED is rejected with 400 (existing invalid-transition mechanism reused).
- Added `publish_order_refunded` event publisher: on successful `RETURN_REQUESTED -> REFUNDED` transition, publishes an `ORDER_REFUNDED` event to the existing `order-events` Kafka topic, containing order id, owning_client_id, product_name, and refund timestamp.
- Ownership isolation, PENDING-only edit, and PENDING/CANCELLED-only delete rules were left untouched.

## Files Modified
- `orders/models.py` — added STATUS_RETURN_REQUESTED, STATUS_REFUNDED choices and `return_reason` nullable CharField.
- `orders/serializers.py` — added `return_reason` to `OrderSerializer` output; added `reason` write field, new allowed transitions, and validation requiring a non-empty reason for RETURN_REQUESTED in `OrderStatusUpdateSerializer`.
- `orders/views.py` — `change_status` now persists `return_reason` on RETURN_REQUESTED and publishes `ORDER_REFUNDED` via `publish_order_refunded` on REFUNDED.
- `orders/kafka_utils.py` — added `publish_order_refunded(order)` function mirroring the existing `publish_order_shipped`.
- `config/settings.py` — switched the loaded env file to `.env_3e37c41e75831210` (project-standard env file name).
- `tests/test_orders.py` — added tests for return-request/refund happy paths and error cases (missing/empty reason, invalid source status transitions).

## Files Added
- `orders/migrations/0002_order_return_reason_alter_order_status.py` — migration adding `return_reason` field and updated status choices.
- `.env_3e37c41e75831210` — environment file with DB/Kafka/admin config (values templated out in `.env.example` on commit).

## Secrets Extracted
- No new hardcoded secrets were found in the codebase; existing `os.getenv`-based config (SECRET_KEY, ADMIN_API_KEY, DB_*, KAFKA_*) was consolidated into `.env_3e37c41e75831210`.

## DB URLs Resolved
- None — existing local MySQL instance (gen_653f4b4c75ff on localhost:3306) was reachable and reused as-is.

## Test Results Summary
- 24 PASSED, 0 FAILED, 0 SKIPPED (pytest tests/) — includes 6 new tests for the return/refund feature plus all 18 pre-existing order/api-key tests.
- Manual end-to-end curl verification of the full order lifecycle (PENDING -> CONFIRMED -> SHIPPED -> DELIVERED -> RETURN_REQUESTED -> REFUNDED) confirmed correct status codes and payloads, including 400 responses for missing reason and invalid transitions.
