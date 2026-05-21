from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailBackend(ModelBackend):
    """Permite login com email em vez de username."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Tentar por email primeiro
        if username and '@' in username:
            try:
                user = User.objects.get(email__iexact=username)
                if user.check_password(password):
                    return user
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass

        # Fallback: tentar por username
        return super().authenticate(request, username=username, password=password, **kwargs)
