from datetime import datetime

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase, CreateError

from core import models


class FdbSession(object):
    session_key = None
    session_data = None
    expire_date = None

    def __init__(self, session_key):
        self.session_key = session_key


class SessionStore(SessionBase):
    def load(self):
        s = models.get_active_session_by_key(settings.DB, self.session_key, datetime.now())
        if s:
            return self.decode(s)
        else:
            self.create()
            return {}

    def exists(self, session_key):
        return bool(models.get_active_session_by_key(settings.DB, session_key, datetime.now()))

    def create(self):
        while True:
            self._session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                continue
            self.modified = True
            self._session_cache = {}
            return

    def save(self, must_create=False):
        if self.session_key is None:
            self._session_key = self._get_new_session_key()
        s = FdbSession(session_key=self.session_key)
        s.session_data = self.encode(self._get_session(no_load=must_create))
        s.expire_date = self.get_expiry_date()
        models.save_session(settings.DB, s)

    def delete(self, session_key=None):
        if session_key is None:
            if self.session_key is None:
                return
            session_key = self.session_key
        models.delete_session(settings.DB, session_key)

