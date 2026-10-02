"""Browser tests: run the real JavaScript/HTMX in Chromium against a live server.

Requires `pip install -r requirements-dev.txt` and `python -m playwright install chromium`.
Skipped automatically when Playwright or a browser isn't available.
Run only these: python manage.py test tests_e2e
"""

import os
import re
from unittest import SkipTest

from allauth.account.models import EmailAddress
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.cache import cache
from django.test import override_settings, tag

from accounts.models import User
from interactions.models import Comment, Like, TopicFollow
from magazine.models import Category
from magazine.tests import make_article
from newsletter.models import Subscriber

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

ARTICLE_BODY = """## مقدمه

متن مقدمه برای تست.

## یک نمونه کد

```python
print("hello")
```

### جمع‌بندی

""" + ("پاراگراف طولانی برای اسکرول. " * 400)


@tag("e2e")
@override_settings(ADMIN_REQUIRE_MFA=False)
class BrowserTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        if sync_playwright is None:
            if os.environ.get("REQUIRE_E2E"):
                raise RuntimeError("REQUIRE_E2E is set but playwright is not installed")
            raise SkipTest("playwright is not installed")
        # Playwright's sync API runs an event loop; Django's ORM is still used synchronously.
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        try:
            cls.browser = cls.playwright.chromium.launch()
        except Exception as exc:  # no browser installed
            cls.playwright.stop()
            super().tearDownClass()
            if os.environ.get("REQUIRE_E2E"):
                raise
            raise SkipTest(f"Chromium not available: {exc}") from exc

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(name="هوش مصنوعی", slug="ai", icon="🤖", show_on_home=True)
        self.article = make_article(self.category, title="راهنمای پایتون برای هوش مصنوعی", body=ARTICLE_BODY,
                                    excerpt="خلاصه", is_featured=True)
        self.context = self.browser.new_context(viewport={"width": 1280, "height": 900})
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda exc: self.errors.append(str(exc)))
        self.page.on("console", lambda msg: msg.type == "error" and self.errors.append(msg.text))

    def tearDown(self):
        self.context.close()

    # --- helpers ---

    def url(self, path):
        return self.live_server_url + path

    def login(self, user):
        self.client.force_login(user)
        self.context.add_cookies([{
            "name": "sessionid", "value": self.client.cookies["sessionid"].value, "url": self.live_server_url,
        }])

    def verified_user(self, username="reader", **extra):
        user = User.objects.create_user(username, f"{username}@example.com", "pass-12345-x", **extra)
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        return user

    def assert_no_js_errors(self):
        self.assertEqual(self.errors, [], "JavaScript errors on the page")

    def assert_no_horizontal_scroll(self):
        overflow = self.page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        self.assertLessEqual(overflow, 1, "page scrolls horizontally")

    # --- layout ---

    def test_pages_render_without_errors_or_sideways_scroll(self):
        paths = ["/", self.article.get_absolute_url(), "/category/ai/", "/search/?q=پایتون",
                 "/ai-daily/", "/accounts/login/", "/accounts/signup/"]
        for width in (1280, 390):
            self.page.set_viewport_size({"width": width, "height": 900})
            for path in paths:
                with self.subTest(path=path, width=width):
                    self.page.goto(self.url(path))
                    expect(self.page.get_by_role("banner")).to_be_visible()  # the site header
                    expect(self.page.locator("main")).to_be_visible()
                    self.assert_no_horizontal_scroll()
        self.assert_no_js_errors()

    def test_cards_are_compact_rows_on_phones(self):
        make_article(self.category, title="مطلب دوم", body="متن", excerpt="خلاصه")
        self.page.set_viewport_size({"width": 390, "height": 900})
        self.page.goto(self.url("/category/ai/"))
        card = self.page.locator("main article.card").first
        thumb = card.locator("a").first.bounding_box()
        box = card.bounding_box()
        self.assertLess(thumb["width"], box["width"] / 2)  # thumbnail beside the text, not above it
        self.page.set_viewport_size({"width": 1280, "height": 900})
        thumb = card.locator("a").first.bounding_box()
        self.assertGreater(thumb["width"], card.bounding_box()["width"] * 0.9)  # full-width cover on desktop

    def test_theme_toggle_persists(self):
        self.page.goto(self.url("/"))
        html = self.page.locator("html")
        was_dark = "dark" in (html.get_attribute("class") or "")
        self.page.click("[data-theme-toggle]")
        expected = re.compile(r"\bdark\b")
        if was_dark:
            expect(html).not_to_have_class(expected)
        else:
            expect(html).to_have_class(expected)
        self.page.reload()
        if was_dark:
            expect(html).not_to_have_class(expected)
        else:
            expect(html).to_have_class(expected)

    def test_categories_dropdown(self):
        self.page.goto(self.url("/"))
        menu = self.page.locator("[data-dropdown-menu]")
        expect(menu).to_be_hidden()
        self.page.click("[data-dropdown-toggle]")
        expect(menu).to_be_visible()
        expect(menu).to_contain_text("هوش مصنوعی")
        self.page.evaluate("document.body.click()")  # click outside the menu
        expect(menu).to_be_hidden()

    def test_categories_menu_fits_phone_screen_when_logged_in(self):
        self.login(self.verified_user())  # logged-in header has more buttons, pushing the toggle inward
        for width in (360, 412):
            with self.subTest(width=width):
                self.page.set_viewport_size({"width": width, "height": 800})
                self.page.goto(self.url("/"))
                self.page.click("[data-dropdown-toggle]")
                box = self.page.locator("[data-dropdown-menu]").bounding_box()
                self.assertGreaterEqual(box["x"], 0)
                self.assertLessEqual(box["x"] + box["width"], width)
                self.page.keyboard.press("Escape")
                expect(self.page.locator("[data-dropdown-menu]")).to_be_hidden()

    # --- search ---

    def test_header_search_suggestions(self):
        self.page.goto(self.url("/"))
        box = self.page.locator("header input[name=q]")
        box.fill("python")  # synonym of «پایتون» in the title
        suggestion = self.page.locator("#search-suggest a", has_text=self.article.title)
        expect(suggestion).to_be_visible()
        box.press("Escape")
        expect(self.page.locator("#search-suggest a")).to_have_count(0)

    def test_live_search_page_updates_results(self):
        self.page.goto(self.url("/search/"))
        self.page.fill("#q", "پایتون")
        expect(self.page.locator("#search-results")).to_contain_text(self.article.title)
        self.page.fill("#q", "ناموجود")
        expect(self.page.locator("#search-results")).to_contain_text("نتیجه‌ای دقیقاً مطابق پیدا نشد")
        self.assertIn("q=", self.page.url)  # hx-push-url keeps the URL shareable

    # --- article page ---

    def test_article_toc_code_copy_and_progress(self):
        self.page.goto(self.url(self.article.get_absolute_url()))
        expect(self.page.locator("aside [data-toc] a")).to_have_count(3)
        expect(self.page.locator(".article-body .highlight .copy-btn")).to_have_count(1)
        progress = self.page.locator("#reading-progress")
        start = progress.evaluate("el => parseFloat(el.style.width) || 0")
        self.page.mouse.wheel(0, 3000)
        self.page.wait_for_function("parseFloat(document.getElementById('reading-progress').style.width) > 5")
        self.assertGreater(progress.evaluate("el => parseFloat(el.style.width)"), start)
        self.assert_no_js_errors()

    def test_anonymous_like_redirects_to_login(self):
        self.page.goto(self.url(self.article.get_absolute_url()))
        self.page.click("button[hx-post*='/i/like/']")
        self.page.wait_for_url(re.compile(r"/accounts/login/"))

    def test_like_bookmark_follow_without_reload(self):
        user = self.verified_user()
        self.login(user)
        self.page.goto(self.url(self.article.get_absolute_url()))
        self.page.evaluate("window.__marker = 1")

        like = self.page.locator("button[hx-post*='/i/like/']")
        like.click()
        expect(self.page.locator("button[hx-post*='/i/like/']")).to_have_attribute("aria-pressed", "true")
        self.page.locator("button[hx-post*='/i/bookmark/']").click()
        expect(self.page.locator("button[hx-post*='/i/bookmark/']")).to_contain_text("ذخیره شد")
        self.assertEqual(self.page.evaluate("window.__marker"), 1)  # no full page reload
        self.assertTrue(Like.objects.filter(user=user, article=self.article).exists())

        self.page.goto(self.url("/category/ai/"))
        self.page.locator("button[hx-post*='/i/follow/']").click()
        expect(self.page.locator("button[hx-post*='/i/follow/']")).to_contain_text("دنبال می‌کنید")
        self.assertTrue(TopicFollow.objects.filter(user=user, category=self.category).exists())

    def test_comment_reply_edit_and_delete(self):
        user = self.verified_user()
        self.login(user)
        self.page.goto(self.url(self.article.get_absolute_url()))

        self.page.fill("#comment-form-wrap textarea[name=body]", "دیدگاه آزمایشی من")
        self.page.click("#comment-form-wrap button")
        comment_list = self.page.locator("#comment-list")
        expect(comment_list).to_contain_text("دیدگاه آزمایشی من")
        expect(self.page.locator("#comment-form-wrap textarea[name=body]")).to_have_value("")

        comment = Comment.objects.get()
        box = self.page.locator(f"#comment-{comment.pk}")
        box.locator("summary", has_text="پاسخ").click()
        box.locator("textarea[name=body]").fill("پاسخ به خودم")
        box.locator("button", has_text="ارسال پاسخ").click()
        expect(self.page.locator(f"#replies-{comment.pk}")).to_contain_text("پاسخ به خودم")

        reply = Comment.objects.get(parent=comment)
        reply_box = self.page.locator(f"#comment-{reply.pk}")
        reply_box.locator("button", has_text="ویرایش").click()
        self.page.locator(f"#comment-{reply.pk} textarea[name=body]").fill("پاسخ ویرایش‌شده")
        self.page.locator(f"#comment-{reply.pk} button", has_text="ذخیره").click()
        expect(self.page.locator(f"#comment-{reply.pk}")).to_contain_text("ویرایش‌شده")

        self.page.on("dialog", lambda dialog: dialog.accept())  # hx-confirm
        self.page.locator(f"#comment-{reply.pk} button", has_text="حذف").click()
        expect(self.page.locator(f"#comment-{reply.pk}")).to_have_count(0)
        self.assertFalse(Comment.objects.filter(pk=reply.pk).exists())
        self.assert_no_js_errors()

    # --- newsletter ---

    def test_newsletter_signup_from_footer(self):
        self.page.goto(self.url("/"))
        box = self.page.locator("footer .newsletter-box")
        box.locator("input[name=email]").fill("fan@example.com")
        box.locator("button").click()
        expect(self.page.locator("footer .newsletter-box")).to_contain_text("لینک تأیید")
        self.assertTrue(Subscriber.objects.filter(email="fan@example.com").exists())

    # --- admin ---

    def test_admin_markdown_editor_preview(self):
        admin_user = User.objects.create_superuser("boss", "boss@example.com", "pass-12345-x")
        self.login(admin_user)
        self.page.goto(self.url("/admin/magazine/article/add/"))
        self.page.fill("#id_body", "## تیتر پیش‌نمایش\n\n**پررنگ**")
        self.page.click("[data-md-toggle]")
        preview = self.page.locator(".md-preview")
        expect(preview.locator("h2")).to_have_text("تیتر پیش‌نمایش")
        expect(preview.locator("strong")).to_have_text("پررنگ")

        self.page.fill("#id_body", "ساده")
        self.page.locator("[data-md='bold']").click()
        self.assertIn("**", self.page.input_value("#id_body"))
        self.assert_no_js_errors()

    def test_admin_dashboard_chart(self):
        admin_user = User.objects.create_superuser("boss", "boss@example.com", "pass-12345-x")
        self.login(admin_user)
        self.page.goto(self.url(self.article.get_absolute_url()))  # one view for the chart
        self.page.goto(self.url("/admin/"))
        expect(self.page.locator(".dash-bar")).to_have_count(14)
        self.page.locator(".dash-bar").last.hover()
        expect(self.page.locator(".dash-bar").last.locator(".tip")).to_be_visible()
