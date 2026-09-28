from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from interactions.models import Bookmark, Comment, Like, ReadingHistory, TopicFollow

from .models import Article, Category, Tag
from .rendering import estimate_reading_time, render_markdown


def make_article(category, **kwargs):
    defaults = {
        "title": "مقاله آزمایشی",
        "body": "## مقدمه\n\nمتن\n\n```python\nprint('hi')\n```",
        "status": Article.Status.PUBLISHED,
        "published_at": timezone.now(),
    }
    defaults.update(kwargs)
    return Article.objects.create(category=category, **defaults)


class RenderingTests(TestCase):
    def test_toc_uses_unicode_ids(self):
        html, toc = render_markdown("## مقدمه\n\n### نکات مهم")
        self.assertEqual([t["id"] for t in toc], ["مقدمه", "نکات-مهم"])
        self.assertIn('id="نکات-مهم"', html)

    def test_code_is_highlighted(self):
        html, _ = render_markdown("```python\nimport os\n```")
        self.assertIn('class="highlight"', html)

    def test_script_is_stripped(self):
        html, _ = render_markdown("<script>alert(1)</script> hello")
        self.assertNotIn("<script>", html)

    def test_reading_time(self):
        self.assertEqual(estimate_reading_time(""), 1)
        self.assertEqual(estimate_reading_time("کلمه " * 1000), 5)


class ArticleModelTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="هوش مصنوعی", slug="ai", icon="🤖")

    def test_unicode_slug_is_unique(self):
        a = make_article(self.cat)
        b = make_article(self.cat)
        self.assertEqual(a.slug, "مقاله-آزمایشی")
        self.assertEqual(b.slug, "مقاله-آزمایشی-2")

    def test_ai_daily_numbering(self):
        first = make_article(self.cat, title="یک", content_type=Article.ContentType.AI_DAILY)
        second = make_article(self.cat, title="دو", content_type=Article.ContentType.AI_DAILY)
        self.assertEqual((first.ai_daily_number, second.ai_daily_number), (1, 2))
        self.assertEqual(second.display_title, "AI Daily #2 — دو")

    def test_published_excludes_drafts_and_future(self):
        make_article(self.cat, title="draft", status=Article.Status.DRAFT)
        make_article(self.cat, title="future", published_at=timezone.now() + timezone.timedelta(days=1))
        live = make_article(self.cat, title="live")
        self.assertEqual(list(Article.objects.published()), [live])

    def test_related_prefers_shared_tags(self):
        other_cat = Category.objects.create(name="وب", slug="web")
        tag = Tag.objects.create(name="Django")
        a = make_article(self.cat, title="a")
        b = make_article(other_cat, title="b")
        a.tags.add(tag)
        b.tags.add(tag)
        self.assertIn(b, a.related())

    def test_youtube_embed(self):
        a = make_article(self.cat, video_url="https://www.youtube.com/watch?v=abc123&t=5")
        self.assertEqual(a.video_embed_url, "https://www.youtube.com/embed/abc123")


class ViewTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="هوش مصنوعی", slug="ai", icon="🤖", show_on_home=True)
        self.article = make_article(self.cat, is_featured=True)
        self.user = User.objects.create_user("ali", "ali@example.com", "pass-12345-x")

    def test_public_pages(self):
        urls = [
            reverse("magazine:home"),
            self.article.get_absolute_url(),
            reverse("magazine:category", args=["ai"]),
            reverse("magazine:content_type", args=["article"]),
            reverse("magazine:ai_daily"),
            reverse("magazine:search") + "?q=آزمایشی",
            reverse("rss"),
            reverse("robots"),
            "/sitemap.xml",
            "/api/articles/",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_draft_hidden_from_public(self):
        draft = make_article(self.cat, title="پیش‌نویس", status=Article.Status.DRAFT)
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)

    def test_search_finds_article(self):
        response = self.client.get(reverse("magazine:search"), {"q": "آزمایشی"})
        self.assertContains(response, self.article.title)
        response = self.client.get(reverse("magazine:search"), {"q": "ناموجود"})
        self.assertEqual(response.context["page_obj"].paginator.count, 0)

    def test_detail_counts_view_and_records_history(self):
        self.client.force_login(self.user)
        self.client.get(self.article.get_absolute_url())
        self.article.refresh_from_db()
        self.assertEqual(self.article.views_count, 1)
        self.assertTrue(ReadingHistory.objects.filter(user=self.user, article=self.article).exists())

    def test_ai_daily_redirect(self):
        daily = make_article(self.cat, title="روزانه", content_type=Article.ContentType.AI_DAILY)
        response = self.client.get(reverse("magazine:ai_daily_detail", args=[daily.ai_daily_number]))
        self.assertRedirects(response, daily.get_absolute_url(), status_code=301)


class InteractionTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="امنیت", slug="security")
        self.article = make_article(self.cat)
        self.user = User.objects.create_user("ali", "ali@example.com", "pass-12345-x")

    def test_anonymous_htmx_gets_redirect_header(self):
        response = self.client.post(reverse("interactions:like", args=[self.article.pk]), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 204)
        self.assertIn(reverse("accounts:login"), response["HX-Redirect"])
        self.assertFalse(Like.objects.exists())

    def test_like_and_bookmark_toggle(self):
        self.client.force_login(self.user)
        url = reverse("interactions:like", args=[self.article.pk])
        self.client.post(url)
        self.assertEqual(Like.objects.count(), 1)
        self.client.post(url)
        self.assertEqual(Like.objects.count(), 0)
        self.client.post(reverse("interactions:bookmark", args=[self.article.pk]))
        self.assertTrue(Bookmark.objects.filter(user=self.user).exists())

    def test_follow_topic_feeds_profile(self):
        self.client.force_login(self.user)
        self.client.post(reverse("interactions:follow", args=[self.cat.pk]))
        self.assertTrue(TopicFollow.objects.filter(user=self.user, category=self.cat).exists())
        response = self.client.get(reverse("accounts:profile"))
        self.assertContains(response, self.article.title)

    def test_comment_and_reply(self):
        self.client.force_login(self.user)
        url = reverse("interactions:comment", args=[self.article.pk])
        response = self.client.post(url, {"body": "عالی بود"}, HTTP_HX_REQUEST="true")
        self.assertContains(response, "عالی بود")
        parent = Comment.objects.get()
        self.client.post(url, {"body": "پاسخ", "parent_id": parent.pk}, HTTP_HX_REQUEST="true")
        self.assertEqual(parent.replies.count(), 1)

    def test_empty_comment_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("interactions:comment", args=[self.article.pk]), {"body": ""})
        self.assertEqual(response.status_code, 422)
        self.assertFalse(Comment.objects.exists())


class AccountTests(TestCase):
    def test_signup_logs_in(self):
        response = self.client.post(reverse("accounts:signup"), {
            "username": "reza", "email": "reza@example.com",
            "password1": "Str0ng-pass-123", "password2": "Str0ng-pass-123",
        })
        self.assertRedirects(response, reverse("accounts:profile"))
        self.assertTrue(User.objects.filter(username="reza").exists())

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
