from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import User


class AccountTests(TestCase):
    def test_signup_sends_verification_and_logs_in(self):
        response = self.client.post(reverse("account_signup"), {
            "username": "reza", "email": "reza@example.com",
            "password1": "Str0ng-pass-123", "password2": "Str0ng-pass-123",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="reza").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("confirm-email", mail.outbox[0].body)

    def test_password_reset_email(self):
        User.objects.create_user("sara", "sara@example.com", "Str0ng-pass-123")
        self.client.post(reverse("account_reset_password"), {"email": "sara@example.com"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/password/reset/key/", mail.outbox[0].body)

    def test_login_with_email(self):
        User.objects.create_user("sara", "sara@example.com", "Str0ng-pass-123")
        response = self.client.post(reverse("account_login"), {"login": "sara@example.com",
                                                                "password": "Str0ng-pass-123"})
        self.assertEqual(response.status_code, 302)

    def test_profile_requires_login(self):
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 302)

    def test_auth_pages_render_in_site_layout(self):
        for name in ("account_login", "account_signup", "account_reset_password"):
            response = self.client.get(reverse(name))
            self.assertContains(response, 'dir="rtl"')

    def test_social_buttons_only_when_configured(self):
        self.assertNotContains(self.client.get(reverse("account_login")), "GitHub")
        providers = {"github": {"APPS": [{"client_id": "id", "secret": "s", "key": ""}]}}
        with override_settings(SOCIALACCOUNT_PROVIDERS=providers):
            self.assertContains(self.client.get(reverse("account_login")), "GitHub")

    def test_edit_profile_notification_preference(self):
        user = User.objects.create_user("n", "n@example.com", "pass-12345-x")
        self.client.force_login(user)
        self.client.post(reverse("accounts:edit_profile"), {"first_name": "نیما", "email_notifications": ""})
        user.refresh_from_db()
        self.assertFalse(user.email_notifications)
        self.assertEqual(user.first_name, "نیما")
