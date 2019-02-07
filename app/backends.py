from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveModelBackend(ModelBackend):
    """
    Custom authentication backend to enable authenticating with case insensitive usernames
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username:
            username = username.lower()
        return super().authenticate(request, username, password, **kwargs)