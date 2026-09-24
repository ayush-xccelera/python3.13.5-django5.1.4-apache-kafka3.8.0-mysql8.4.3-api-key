import hashlib

from django.core.management.base import BaseCommand
from django.db import transaction

from orders.models import ApiKey, Order


class Command(BaseCommand):
    help = 'Seed the database with sample API keys and orders (idempotent).'

    def handle(self, *args, **options):
        with transaction.atomic():
            demo_key_raw = 'abc123xyz'
            demo_key_hash = hashlib.sha256(demo_key_raw.encode()).hexdigest()
            client1, _ = ApiKey.objects.get_or_create(
                key_hash=demo_key_hash,
                defaults={'name': 'Demo Client 1', 'is_active': True},
            )

            second_key_raw = 'demo-client-two-key'
            second_key_hash = hashlib.sha256(second_key_raw.encode()).hexdigest()
            client2, _ = ApiKey.objects.get_or_create(
                key_hash=second_key_hash,
                defaults={'name': 'Demo Client 2', 'is_active': True},
            )

            sample_orders = [
                {'product_name': 'Wireless Mouse', 'quantity': 2, 'total_amount': '39.98', 'status': Order.STATUS_PENDING, 'owning_client': client1},
                {'product_name': 'Mechanical Keyboard', 'quantity': 1, 'total_amount': '89.99', 'status': Order.STATUS_CONFIRMED, 'owning_client': client1},
                {'product_name': 'USB-C Hub', 'quantity': 3, 'total_amount': '59.97', 'status': Order.STATUS_SHIPPED, 'owning_client': client1},
                {'product_name': '27-inch Monitor', 'quantity': 1, 'total_amount': '249.99', 'status': Order.STATUS_PENDING, 'owning_client': client2},
                {'product_name': 'Laptop Stand', 'quantity': 2, 'total_amount': '45.00', 'status': Order.STATUS_CANCELLED, 'owning_client': client2},
            ]

            for data in sample_orders:
                Order.objects.get_or_create(
                    product_name=data['product_name'],
                    owning_client=data['owning_client'],
                    defaults={
                        'quantity': data['quantity'],
                        'total_amount': data['total_amount'],
                        'status': data['status'],
                    },
                )

        self.stdout.write(self.style.SUCCESS('Seed data created (or already present).'))
