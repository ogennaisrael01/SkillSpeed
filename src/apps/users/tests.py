from .services.helpers import _genrate_url_for_account_verification, create_otp_for_user, _hash_otp_code
from .services.templates_service import genrate_context_for_otp
from .helpers import _send_email_to_user
from .services.email_service import _send_mail_base

from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

import os

User = get_user_model()
BaseURL = getattr(settings, "BASE_URL")

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.getenv("DJANGO_SETTINGS_MODULE", "core.settings.base"))


class TestUserAuth(TestCase):

    def setUp(self):
        user = User.objects.create(email="testuser@example.com",
                                   password="test-password")

    def test_url_generation(self):
        code = "23455"
        result = _genrate_url_for_account_verification(code)
        url = BaseURL + f"api/v1/auth/verify/?code={code}"
        self.assertEqual(url, result)

    def test_create_otp_for_user(self):
        user = get_object_or_404(User, email="testuser@example.com")
        result = create_otp_for_user(user)
        self.assertIsNotNone(result)

    def test_verification_context(self):
        code = "098847"
        uri = url = BaseURL + f"api/v1/auth/verify/?code={code}"
        email = 'test-user@example.com'
        result = genrate_context_for_otp(code, uri, email)
        self.assertIsNotNone(result.get("verification_url"))

    def test_send_email_to_user(self):
        context = {
            "code": "303030",
            "email": "testuser@example.com",
            "verification_url": "http://example.com/verify",
            "subject": "Test Email",
            "template_name": "test_template.html"
        }
        result = _send_email_to_user(context)
        self.assertTrue(result)

    def test_send_email_base(self):
        context = {
            "code": "303030",
            "to_email": "testuser@example.com",
            "verification_url": "http://example.com/verify",
            "subject": "Test Email",
            "template_name": "users/otp_template.html"
        }

        result = _send_mail_base(context)
        print(result)
