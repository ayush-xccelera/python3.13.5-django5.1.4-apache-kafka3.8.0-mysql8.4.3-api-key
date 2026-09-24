import secrets

from django.conf import settings
from rest_framework.permissions import BasePermission


class IsAdminApiKey(BasePermission):
    """Grants access only when 'X-Admin-Key' header matches ADMIN_API_KEY."""

    def has_permission(self, request, view):
        provided = request.META.get('HTTP_X_ADMIN_KEY')
        expected = getattr(settings, 'ADMIN_API_KEY', '')
        if not provided or not expected:
            return False
        return secrets.compare_digest(provided, expected)
