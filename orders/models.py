from django.db import models


class ApiKey(models.Model):
    """A client identity, authenticated via a hashed API key."""

    key_hash = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"ApiKey({self.name})"


class Order(models.Model):
    """An order placed by a client, identified by the API key that created it."""

    STATUS_PENDING = 'PENDING'
    STATUS_CONFIRMED = 'CONFIRMED'
    STATUS_SHIPPED = 'SHIPPED'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_RETURN_REQUESTED = 'RETURN_REQUESTED'
    STATUS_REFUNDED = 'REFUNDED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_RETURN_REQUESTED, 'Return Requested'),
        (STATUS_REFUNDED, 'Refunded'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    return_reason = models.CharField(max_length=500, null=True, blank=True)
    owning_client = models.ForeignKey(
        ApiKey, on_delete=models.CASCADE, related_name='orders'
    )
    created_timestamp = models.DateTimeField(auto_now_add=True)
    updated_timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_timestamp']

    def __str__(self):
        return f"Order({self.id}, {self.product_name}, {self.status})"
