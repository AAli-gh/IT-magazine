from allauth.account.models import EmailAddress
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from core.models import SiteSettings
from magazine.models import Category
from magazine.tests import make_article

from .models import Bookmark, Comment, Like, TopicFollow


def verified_user(username="ali"):
    user = User.objects.create_user(username, f"{username}@example.com", "pass-12345-x")
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    return user


class InteractionTests(TestCase):
    def setUp(self):
        cache.clear()
        self.cat = Category.objects.create(name="امنیت", slug="security")
        self.article = make_article(self.cat)
        self.user = verified_user()
        self.comment_url = reverse("interactions:comment", args=[self.article.pk])

    def test_anonymous_htmx_gets_redirect_header(self):
        response = self.client.post(reverse("interactions:like", args=[self.article.pk]), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 204)
        self.assertIn(reverse("account_login"), response["HX-Redirect"])
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
        response = self.client.post(self.comment_url, {"body": "عالی بود"}, HTTP_HX_REQUEST="true")
        self.assertContains(response, "عالی بود")
        parent = Comment.objects.get()
        self.assertTrue(parent.is_approved)
        self.client.post(self.comment_url, {"body": "پاسخ", "parent_id": parent.pk}, HTTP_HX_REQUEST="true")
        self.assertEqual(parent.replies.count(), 1)

    def test_empty_comment_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(self.comment_url, {"body": ""})
        self.assertEqual(response.status_code, 422)
        self.assertFalse(Comment.objects.exists())


class CommentSpamTests(TestCase):
    def setUp(self):
        cache.clear()
        self.cat = Category.objects.create(name="امنیت", slug="security")
        self.article = make_article(self.cat)
        self.url = reverse("interactions:comment", args=[self.article.pk])

    def test_unverified_email_cannot_comment(self):
        user = User.objects.create_user("new", "new@example.com", "pass-12345-x")
        self.client.force_login(user)
        response = self.client.post(self.url, {"body": "سلام"}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "ایمیل", status_code=403)
        self.assertFalse(Comment.objects.exists())

    def test_honeypot_rejects_bots(self):
        self.client.force_login(verified_user())
        response = self.client.post(self.url, {"body": "spam", "website": "http://spam"})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Comment.objects.exists())

    @override_settings(COMMENT_RATE_LIMIT=(2, 600))
    def test_rate_limit(self):
        self.client.force_login(verified_user())
        codes = [self.client.post(self.url, {"body": f"دیدگاه {i}"}, HTTP_HX_REQUEST="true").status_code
                 for i in range(3)]
        self.assertEqual(codes, [200, 200, 429])
        self.assertEqual(Comment.objects.count(), 2)

    def test_many_links_are_held_for_moderation(self):
        self.client.force_login(verified_user())
        body = "http://a.com http://b.com http://c.com"
        self.client.post(self.url, {"body": body}, HTTP_HX_REQUEST="true")
        comment = Comment.objects.get()
        self.assertFalse(comment.is_approved)
        self.assertEqual(comment.held_reason, "لینک زیاد")
        response = self.client.get(self.article.get_absolute_url())
        self.assertNotContains(response, "http://a.com")

    def test_banned_words_and_manual_approval(self):
        site = SiteSettings.load()
        site.banned_words = "قمار"
        site.save()
        self.client.force_login(verified_user())
        self.client.post(self.url, {"body": "سایت قمار"}, HTTP_HX_REQUEST="true")
        self.assertFalse(Comment.objects.get().is_approved)

        site.banned_words = ""
        site.comments_require_approval = True
        site.save()
        self.client.post(self.url, {"body": "دیدگاه عادی"}, HTTP_HX_REQUEST="true")
        self.assertFalse(Comment.objects.get(body="دیدگاه عادی").is_approved)


class CommentEditDeleteTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="امنیت", slug="security")
        self.article = make_article(cat)
        self.owner = verified_user("owner")
        self.other = verified_user("other")
        self.comment = Comment.objects.create(article=self.article, user=self.owner, body="نسخه اول")

    def test_owner_can_edit(self):
        self.client.force_login(self.owner)
        url = reverse("interactions:edit_comment", args=[self.comment.pk])
        self.assertContains(self.client.get(url), "نسخه اول")
        response = self.client.post(url, {"body": "نسخه دوم"})
        self.assertContains(response, "ویرایش‌شده")
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, "نسخه دوم")
        self.assertIsNotNone(self.comment.edited_at)

    def test_others_cannot_edit_or_delete(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse("interactions:edit_comment", args=[self.comment.pk]),
                                          {"body": "hack"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("interactions:delete_comment", args=[self.comment.pk])).status_code, 403)

    def test_delete_without_replies_removes(self):
        self.client.force_login(self.owner)
        self.client.post(reverse("interactions:delete_comment", args=[self.comment.pk]))
        self.assertFalse(Comment.objects.exists())

    def test_delete_with_replies_keeps_thread(self):
        Comment.objects.create(article=self.article, user=self.other, body="پاسخ", parent=self.comment)
        self.client.force_login(self.owner)
        response = self.client.post(reverse("interactions:delete_comment", args=[self.comment.pk]))
        self.assertContains(response, "حذف شده")
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)
        self.assertEqual(self.comment.replies.count(), 1)
