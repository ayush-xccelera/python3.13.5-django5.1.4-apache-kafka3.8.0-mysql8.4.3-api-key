import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_producer = None


def _get_producer():
    global _producer
    if _producer is None:
        try:
            from kafka import KafkaProducer
            _producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                request_timeout_ms=5000,
            )
        except Exception as exc:  # pragma: no cover - broker may be unreachable
            logger.warning("Kafka producer unavailable: %s", exc)
            _producer = False
    return _producer or None


def publish_order_shipped(order):
    """Publish an ORDER_SHIPPED event to the order-events topic. Call only after commit."""
    producer = _get_producer()
    if producer is None:
        logger.warning("Skipping ORDER_SHIPPED publish: no Kafka producer available.")
        return False

    payload = {
        "event": "ORDER_SHIPPED",
        "order_id": order.id,
        "owning_client_id": order.owning_client_id,
        "product_name": order.product_name,
        "quantity": order.quantity,
        "shipped_timestamp": order.updated_timestamp.isoformat(),
    }
    try:
        producer.send(settings.KAFKA_ORDER_EVENTS_TOPIC, value=payload)
        producer.flush(timeout=5)
        return True
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to publish ORDER_SHIPPED event: %s", exc)
        return False
