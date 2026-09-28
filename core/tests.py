from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .cache import bump_content_version, content_version
from .models import SiteSettings


class SiteSettingsTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_singleton_and_used_in_templates(self):
        settings = SiteSettings.load()
        settings.site_name = "مجله تست"
        settings.telegram_url = "https://t.me/itmag"
        settings.save()
        self.assertEqual(SiteSettings.objects.count(), 1)
        response = self.client.get(reverse("magazine:home"))
        self.assertContains(response, "مجله تست")
        self.assertContains(response, "https://t.me/itmag")

    def test_only_superuser_edits_settings(self):
        staff = User.objects.create_user("s", "s@example.com", "x", is_staff=True)
        self.client.force_login(staff)
        url = reverse("admin:core_sitesettings_change", args=[SiteSettings.load().pk])
        self.assertIn(self.client.get(url).status_code, (302, 403))

    def test_content_version_bumps(self):
        before = content_version()
        bump_content_version()
        self.assertEqual(content_version(), before + 1)

    def test_robots_and_health(self):
        self.assertContains(self.client.get(reverse("robots")), "Sitemap:")
        self.assertContains(self.client.get(reverse("healthz")), "ok")
