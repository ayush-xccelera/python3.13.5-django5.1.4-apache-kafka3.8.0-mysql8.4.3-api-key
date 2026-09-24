from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import OrderViewSet, ApiKeyViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'api-keys', ApiKeyViewSet, basename='apikey')

urlpatterns = [
    path('', include(router.urls)),
]
