from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings
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


class ErrorPageTests(TestCase):
    def test_500_page_is_self_contained(self):
        from django.test import RequestFactory
        from django.views.defaults import server_error

        response = server_error(RequestFactory().get("/"))
        self.assertEqual(response.status_code, 500)
        html = response.content.decode()
        self.assertIn("متأسفانه مشکلی در", html)
        self.assertIn('dir="rtl"', html)
        self.assertIn("brand/500-robot.webp", html)
        self.assertNotIn("data-dropdown", html)  # standalone page, not the full site layout

    @override_settings(DEBUG=False)
    def test_unhandled_error_uses_500_template(self):
        client = self.client_class(raise_request_exception=False)
        with mock.patch("magazine.views._published", side_effect=RuntimeError("boom")):
            response = client.get(reverse("magazine:home"))
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "Internal Server Error", status_code=500)


class AdminSecurityTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_superuser("boss", "boss@example.com", "pass-12345-x")

    def test_admin_login_goes_through_allauth(self):
        response = self.client.get("/admin/login/?next=/admin/magazine/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(reverse("account_login")))
        self.assertIn("next=%2Fadmin%2Fmagazine%2F", response["Location"])

    @override_settings(ADMIN_REQUIRE_MFA=True)
    def test_staff_must_enable_2fa_for_admin(self):
        from allauth.mfa.models import Authenticator

        self.client.force_login(self.staff)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(reverse("mfa_activate_totp")))
        # The public site stays reachable without 2FA.
        self.assertEqual(self.client.get(reverse("magazine:home")).status_code, 200)

        Authenticator.objects.create(user=self.staff, type=Authenticator.Type.TOTP, data={})
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)

    @override_settings(ADMIN_URL="secret-panel/", ADMIN_REQUIRE_MFA=True)
    def test_custom_admin_url_hides_default_path(self):
        import importlib

        from django.urls import clear_url_caches

        import config.urls

        try:
            importlib.reload(config.urls)
            clear_url_caches()
            self.assertEqual(reverse("admin:index"), "/secret-panel/")
            self.assertEqual(self.client.get("/admin/").status_code, 404)
            self.assertEqual(self.client.get("/admin/login/").status_code, 404)
            response = self.client.get("/secret-panel/")
            self.assertEqual(response.status_code, 302)
            self.assertIn("next=/secret-panel/", response["Location"])
            # The 2FA check follows the configured path.
            self.client.force_login(self.staff)
            response = self.client.get("/secret-panel/")
            self.assertTrue(response["Location"].startswith(reverse("mfa_activate_totp")))
            robots = self.client.get("/robots.txt").content.decode()
            self.assertNotIn("secret-panel", robots)
        finally:
            with override_settings(ADMIN_URL="admin/"):
                importlib.reload(config.urls)
            clear_url_caches()

    def test_2fa_setup_page_renders(self):
        # Log in through allauth: setting up 2FA requires a recent real login.
        self.client.post(reverse("account_login"), {"login": "boss", "password": "pass-12345-x"})
        response = self.client.get(reverse("mfa_activate_totp"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'dir="rtl"')


class BrandingAndPagesTests(TestCase):
    def test_favicon_and_default_share_image(self):
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 301)
        self.assertIn("brand/favicon.ico", response["Location"])
        home = self.client.get(reverse("magazine:home"))
        self.assertContains(home, "brand/og-default.jpg")
        self.assertContains(home, "brand/logo.svg")

    def test_seed_adds_legal_pages_to_footer(self):
        import io

        from django.core.management import call_command

        call_command("seed_magazine", stdout=io.StringIO())
        home = self.client.get(reverse("magazine:home"))
        for slug, title in (("privacy", "حریم خصوصی"), ("terms", "قوانین استفاده")):
            self.assertContains(home, title)
            self.assertEqual(self.client.get(reverse("core:page", args=[slug])).status_code, 200)


class BackupTests(TestCase):
    def test_backup_contains_data_and_media(self):
        import io
        import tempfile
        import zipfile
        from pathlib import Path

        from django.core.management import call_command

        User.objects.create_user("reader", "reader@example.com", "pass-12345-x")
        with tempfile.TemporaryDirectory() as media, tempfile.TemporaryDirectory() as out:
            (Path(media) / "covers").mkdir()
            (Path(media) / "covers" / "a.jpg").write_bytes(b"img")
            with override_settings(MEDIA_ROOT=media):
                for _ in range(3):
                    call_command("backup_site", output_dir=out, keep=2, stdout=io.StringIO())
            backups = sorted(Path(out).glob("itmag-*.zip"))
            self.assertLessEqual(len(backups), 2)
            with zipfile.ZipFile(backups[-1]) as archive:
                names = archive.namelist()
                self.assertIn("data.json", names)
                self.assertIn("media/covers/a.jpg", names)
                self.assertIn("reader@example.com", archive.read("data.json").decode())


class ContactLinksTests(TestCase):
    def test_instagram_and_email_in_footer_and_contact_page(self):
        import io

        from django.core.management import call_command

        call_command("seed_magazine", stdout=io.StringIO())
        settings_obj = SiteSettings.load()
        settings_obj.contact_email = "team@example.com"
        settings_obj.instagram_url = "https://www.instagram.com/example_co/"
        settings_obj.save()
        cache.clear()

        home = self.client.get(reverse("magazine:home"))
        self.assertContains(home, 'href="https://www.instagram.com/example_co/"')
        self.assertContains(home, 'href="mailto:team@example.com"')
        contact = self.client.get(reverse("core:page", args=["contact"]))
        self.assertContains(contact, "example_co")
        self.assertContains(contact, "team@example.com")


class AdminButtonTests(TestCase):
    def test_admin_panel_button_only_for_superusers(self):
        home = reverse("magazine:home")
        self.assertNotContains(self.client.get(home), "data-admin-link")

        author = User.objects.create_user("writer", "writer@example.com", "pass-12345-x", is_staff=True)
        self.client.force_login(author)
        self.assertNotContains(self.client.get(home), "data-admin-link")

        boss = User.objects.create_superuser("boss", "boss@example.com", "pass-12345-x")
        self.client.force_login(boss)
        response = self.client.get(home)
        self.assertContains(response, "data-admin-link")
        self.assertContains(response, f'href="{reverse("admin:index")}"')


@override_settings(ADMIN_REQUIRE_MFA=False)
class AdminThemeTests(TestCase):
    def test_admin_uses_site_theme_and_quick_links(self):
        self.client.force_login(User.objects.create_superuser("boss", "boss@example.com", "pass-12345-x"))
        for url in (reverse("admin:index"), reverse("admin:magazine_article_changelist")):
            response = self.client.get(url)
            self.assertContains(response, "admin/theme.css")
            self.assertContains(response, 'class="itm-logo"')
            self.assertContains(response, reverse("admin:magazine_article_add"))
            self.assertContains(response, 'id="logout-form"')


class NotFoundPageTests(TestCase):
    def test_custom_404_page(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "یافت نشد", status_code=404)
        self.assertContains(response, "brand/404-robot.webp", status_code=404)
        self.assertContains(response, f'action="{reverse("magazine:search")}"', status_code=404)


class ForbiddenPageTests(TestCase):
    def render_403(self, user):
        from django.contrib.sessions.backends.signed_cookies import SessionStore
        from django.core.exceptions import PermissionDenied
        from django.test import RequestFactory
        from django.views.defaults import permission_denied

        request = RequestFactory().get("/secret/")
        request.user, request.session = user, SessionStore()
        return permission_denied(request, PermissionDenied())

    def test_custom_403_page(self):
        from django.contrib.auth.models import AnonymousUser

        response = self.render_403(AnonymousUser())
        self.assertEqual(response.status_code, 403)
        html = response.content.decode()
        self.assertIn("brand/403-robot.webp", html)
        self.assertIn("متأسفانه شما اجازهٔ دسترسی به این صفحه را ندارید.", html)
        self.assertIn(reverse("account_login") + "?next=/secret/", html)  # anonymous: offer login

        member = User.objects.create_user("reader", "reader@example.com", "pass-12345-x")
        html = self.render_403(member).content.decode()
        self.assertNotIn(reverse("account_login") + "?next=", html)  # logged in: offer "back" instead
        self.assertIn("بازگشت به صفحهٔ قبل", html)


class ErrorPreviewTests(TestCase):
    CODES = {
        400: "درخواست ارسال‌شده توسط شما قابل پردازش نیست.",
        401: "برای مشاهدهٔ این صفحه ابتدا باید وارد حساب کاربری خود شوید.",
        403: "متأسفانه شما اجازهٔ دسترسی به این صفحه را ندارید.",
        429: "شما در مدت زمان کوتاهی تعداد زیادی درخواست ارسال کرده‌اید.",
        500: "این خطا ثبت شده است و برای رفع آن بررسی می‌شود.",
        503: "در حال حاضر سرویس موقتاً در دسترس نیست.",
        504: "سرور مقصد در زمان مقرر پاسخی ارسال نکرده است.",
    }

    def test_previews_are_for_admins_only(self):
        url = lambda code: reverse("core:error_preview", args=[code])  # noqa: E731
        for code in self.CODES:
            self.assertEqual(self.client.get(url(code)).status_code, 404)
        self.client.force_login(User.objects.create_user("writer", "w@example.com", "pass-12345-x", is_staff=True))
        self.assertEqual(self.client.get(url(403)).status_code, 404)

        self.client.force_login(User.objects.create_superuser("boss", "b@example.com", "pass-12345-x"))
        for code, text in self.CODES.items():
            with self.subTest(code=code):
                response = self.client.get(url(code))
                self.assertEqual(response.status_code, code)
                self.assertContains(response, text, status_code=code)
                if code not in (400,):  # 400 still uses the 404 illustration
                    self.assertContains(response, f"brand/{code}-robot.webp", status_code=code)
        self.assertEqual(self.client.get(url(418)).status_code, 404)

    def test_401_offers_login_and_signup(self):
        self.client.force_login(User.objects.create_superuser("boss", "b@example.com", "pass-12345-x"))
        response = self.client.get(reverse("core:error_preview", args=[401]))
        self.assertContains(response, reverse("account_signup"), status_code=401)
        self.assertContains(response, reverse("account_login") + "?next=", status_code=401)


class MaintenanceModeTests(TestCase):
    @override_settings(MAINTENANCE_MODE=True)
    def test_visitors_get_503_but_staff_and_login_work(self):
        response = self.client.get(reverse("magazine:home"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response["Retry-After"], "600")
        self.assertContains(response, "brand/503-robot.webp", status_code=503)
        self.assertEqual(self.client.get(reverse("account_login")).status_code, 200)

        self.client.force_login(User.objects.create_user("editor", "e@example.com", "pass-12345-x", is_staff=True))
        self.assertEqual(self.client.get(reverse("magazine:home")).status_code, 200)

    def test_off_by_default(self):
        self.assertEqual(self.client.get(reverse("magazine:home")).status_code, 200)
