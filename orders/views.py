from django.db import transaction
from rest_framework import viewsets, mixins, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Order, ApiKey
from .serializers import (
    OrderSerializer,
    OrderStatusUpdateSerializer,
    ApiKeyCreateSerializer,
    ApiKeyOutSerializer,
)
from .permissions import IsAdminApiKey
from .pagination import DefaultLimitOffsetPagination
from .kafka_utils import publish_order_shipped


class OrderViewSet(viewsets.ModelViewSet):
    """CRUD for orders, scoped to the authenticated client (owning_client)."""

    serializer_class = OrderSerializer
    pagination_class = DefaultLimitOffsetPagination
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    ORDERING_FIELDS = {'created_timestamp', 'updated_timestamp', 'total_amount', 'quantity'}

    def get_queryset(self):
        client = self.request.auth
        qs = Order.objects.filter(owning_client=client)

        ordering = self.request.query_params.get('ordering')
        if ordering:
            field = ordering.lstrip('-')
            if field in self.ORDERING_FIELDS:
                qs = qs.order_by(ordering)
        return qs

    def perform_create(self, serializer):
        client = self.request.auth
        serializer.save(owning_client=client, status=Order.STATUS_PENDING)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != Order.STATUS_PENDING:
            raise ValidationError('Order can only be updated while status is PENDING.')
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status not in (Order.STATUS_PENDING, Order.STATUS_CANCELLED):
            raise ValidationError('Order can only be deleted while status is PENDING or CANCELLED.')
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'], url_path='status')
    def change_status(self, request, pk=None):
        instance = self.get_object()
        serializer = OrderStatusUpdateSerializer(
            data=request.data, context={'order': instance}
        )
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        with transaction.atomic():
            instance.status = new_status
            instance.save(update_fields=['status', 'updated_timestamp'])

        if new_status == Order.STATUS_SHIPPED:
            publish_order_shipped(instance)

        return Response(OrderSerializer(instance).data)


class ApiKeyViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """Administrative management of API keys. Gated by IsAdminApiKey only."""

    queryset = ApiKey.objects.all().order_by('-created_at')
    authentication_classes = []
    permission_classes = [IsAdminApiKey]
    pagination_class = DefaultLimitOffsetPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return ApiKeyCreateSerializer
        return ApiKeyOutSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        out = ApiKeyCreateSerializer(instance)
        return Response(out.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)
