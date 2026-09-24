import secrets
import hashlib

from decimal import Decimal
from rest_framework import serializers

from .models import Order, ApiKey


class ApiKeyCreateSerializer(serializers.ModelSerializer):
    """Creates a new API key; returns the raw key exactly once."""

    key = serializers.SerializerMethodField()

    class Meta:
        model = ApiKey
        fields = ['id', 'name', 'is_active', 'created_at', 'key']
        read_only_fields = ['id', 'is_active', 'created_at', 'key']

    def get_key(self, obj):
        return getattr(obj, '_raw_key', None)

    def create(self, validated_data):
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        instance = ApiKey.objects.create(key_hash=key_hash, **validated_data)
        instance._raw_key = raw_key
        return instance


class ApiKeyOutSerializer(serializers.ModelSerializer):
    """Never exposes key_hash or the raw key."""

    class Meta:
        model = ApiKey
        fields = ['id', 'name', 'is_active', 'created_at', 'last_used_at']
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'id', 'product_name', 'quantity', 'total_amount', 'status',
            'return_reason', 'owning_client', 'created_timestamp', 'updated_timestamp',
        ]
        read_only_fields = ['id', 'status', 'return_reason', 'owning_client', 'created_timestamp', 'updated_timestamp']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('quantity must be greater than 0.')
        return value

    def validate_total_amount(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('total_amount must be greater than 0.')
        return value

    def validate_product_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('product_name is required.')
        return value


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    reason = serializers.CharField(required=False, allow_blank=True)

    ALLOWED_TRANSITIONS = {
        Order.STATUS_PENDING: [Order.STATUS_CONFIRMED, Order.STATUS_CANCELLED],
        Order.STATUS_CONFIRMED: [Order.STATUS_SHIPPED, Order.STATUS_CANCELLED],
        Order.STATUS_SHIPPED: [Order.STATUS_DELIVERED],
        Order.STATUS_DELIVERED: [Order.STATUS_RETURN_REQUESTED],
        Order.STATUS_RETURN_REQUESTED: [Order.STATUS_REFUNDED],
        Order.STATUS_REFUNDED: [],
        Order.STATUS_CANCELLED: [],
    }

    def validate_status(self, value):
        order = self.context.get('order')
        if order is not None:
            allowed = self.ALLOWED_TRANSITIONS.get(order.status, [])
            if value not in allowed:
                raise serializers.ValidationError(
                    f"Invalid status transition from {order.status} to {value}."
                )
        return value

    def validate(self, attrs):
        if attrs.get('status') == Order.STATUS_RETURN_REQUESTED:
            reason = attrs.get('reason')
            if not reason or not reason.strip():
                raise serializers.ValidationError(
                    {'reason': 'reason is required when requesting a return.'}
                )
        return attrs
