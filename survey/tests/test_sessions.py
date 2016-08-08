from django.test import TestCase
from django.conf import settings


class SessionsTest(TestCase):

    def test_django_sessions_is_loaded(self):
        self.assertTrue( 'django.contrib.sessions' in settings.INSTALLED_APPS)
        self.assertTrue('django.contrib.sessions.middleware.SessionMiddleware' in settings.MIDDLEWARE_CLASSES)

    def test_session_expires_on_browser_close(self):
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)

    def test_session_expires_after_30_mins(self):
        self.assertEquals(settings.SESSION_COOKIE_AGE, 60*30)

    def test_session_is_saved_on_every_request_to_avoid_session_expiry_if_the_user_is_active(self):
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
