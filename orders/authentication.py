import hashlib

from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import ApiKey


class AuthenticatedApiKeyUser(AnonymousUser):
    """Stand-in 'user' for API-key authenticated requests.

    AnonymousUser.is_authenticated is always False, which makes DRF's
    IsAuthenticated permission reject valid API-key requests. This subclass
    reports is_authenticated=True while still not being backed by a real
    Django User/session.
    """

    @property
    def is_authenticated(self):
        return True


class ApiKeyAuthentication(BaseAuthentication):
    """Authenticates requests using the 'X-API-Key' header against ApiKey.key_hash."""

    def authenticate_header(self, request):
        return 'X-API-Key'

    def authenticate(self, request):
        raw_key = request.META.get('HTTP_X_API_KEY')
        if not raw_key:
            return None

        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        try:
            api_key = ApiKey.objects.get(key_hash=key_hash)
        except ApiKey.DoesNotExist:
            raise AuthenticationFailed('Invalid API key.')

        if not api_key.is_active:
            raise AuthenticationFailed('API key is inactive.')

        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=['last_used_at'])

        return (AuthenticatedApiKeyUser(), api_key)
