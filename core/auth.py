from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from core import models


class User(object):
    def __init__(self, username):
        self.username = username

    @property
    def id(self):
        return self.username

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def save(self):
        pass

class FoundationDBBackend(object):
    """Authenticate using FoundationDB
    """

    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, username=None, password=None):
        if models.check_password_match(settings.DB, username, password):
            return User(username)
        return None

    def get_user(self, user_id):
        if not user_id:
            return AnonymousUser
        return User(models.get_user(settings.DB, user_id)['username'])
