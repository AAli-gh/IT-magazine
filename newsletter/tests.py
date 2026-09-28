from datetime import timedelta

from django.core import mail
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from interactions.models import Comment, TopicFollow
from magazine.models import Article, Category
from magazine.tests import make_article

from . import services
from .models import NewsletterIssue, Notification, Subscriber


class SubscriptionTests(TestCase):
    def test_double_opt_in_and_unsubscribe(self):
        response = self.client.post(reverse("newsletter:subscribe"), {"email": "Reader@Example.com"},
                                    HTTP_HX_REQUEST="true")
        self.assertContains(response, "لینک تأیید")
        subscriber = Subscriber.objects.get()
        self.assertEqual(subscriber.email, "reader@example.com")
        self.assertFalse(subscriber.is_confirmed)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(subscriber.token), mail.outbox[0].body)

        self.client.get(reverse("newsletter:confirm", args=[subscriber.token]))
        subscriber.refresh_from_db()
        self.assertTrue(subscriber.is_confirmed)

        self.client.post(reverse("newsletter:unsubscribe", args=[subscriber.token]))
        subscriber.refresh_from_db()
        self.assertFalse(subscriber.is_active)

    def test_honeypot(self):
        self.client.post(reverse("newsletter:subscribe"), {"email": "bot@example.com", "website": "x"},
                         HTTP_HX_REQUEST="true")
        self.assertFalse(Subscriber.objects.exists())


class SendingTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="هوش مصنوعی", slug="ai")
        Subscriber.objects.create(email="yes@example.com", is_confirmed=True)
        Subscriber.objects.create(email="pending@example.com", is_confirmed=False)
        Subscriber.objects.create(email="weekly-only@example.com", is_confirmed=True, wants_ai_daily=False)

    def test_ai_daily_sent_once_to_confirmed_subscribers(self):
        make_article(self.cat, title="روز", content_type=Article.ContentType.AI_DAILY, why_important="چون")
        mail.outbox.clear()
        self.assertEqual(services.send_ai_daily(), 1)
        self.assertEqual(mail.outbox[0].to, ["yes@example.com"])
        self.assertIn("List-Unsubscribe", mail.outbox[0].extra_headers)
        self.assertIsNone(services.send_ai_daily())  # already sent
        self.assertEqual(NewsletterIssue.objects.count(), 1)

    def test_weekly_digest(self):
        make_article(self.cat, title="هفته")
        make_article(self.cat, title="قدیمی", published_at=timezone.now() - timedelta(days=30))
        mail.outbox.clear()
        self.assertEqual(services.send_weekly_digest(), 2)
        self.assertIn("هفته", mail.outbox[0].body)
        self.assertNotIn("قدیمی", mail.outbox[0].body)


class EditorAlertTests(TransactionTestCase):
    """Editors hear about articles waiting for review and comments held for moderation."""

    def setUp(self):
        from accounts.roles import ensure_roles, make_author, make_editor

        ensure_roles()
        self.cat = Category.objects.create(name="وب", slug="web")
        self.editor = User.objects.create_user("chief", "chief@example.com", "pass-12345-x")
        make_editor(self.editor)
        self.author = User.objects.create_user("writer", "writer@example.com", "pass-12345-x")
        make_author(self.author)
        self.reader = User.objects.create_user("reader", "reader@example.com", "pass-12345-x")

    def test_review_request_notifies_editors_once(self):
        article = make_article(self.cat, title="پیش‌نویس", status=Article.Status.DRAFT, author=self.author)
        self.assertFalse(Notification.objects.exists())
        article.status = Article.Status.REVIEW
        article.save()
        note = Notification.objects.get()
        self.assertEqual((note.user, note.kind), (self.editor, Notification.Kind.REVIEW))
        self.assertIn(f"/admin/magazine/article/{article.pk}/change/", note.url)
        self.assertEqual([m.to for m in mail.outbox], [["chief@example.com"]])
        article.title = "ویرایش در صف بررسی"
        article.save()  # still in review: no second alert
        self.assertEqual(Notification.objects.count(), 1)

    def test_ai_generated_draft_in_review_notifies(self):
        make_article(self.cat, title="AI", status=Article.Status.REVIEW)
        self.assertEqual(Notification.objects.filter(kind=Notification.Kind.REVIEW).count(), 1)

    def test_held_comment_notifies_moderators(self):
        article = make_article(self.cat)
        Notification.objects.all().delete()
        mail.outbox.clear()
        Comment.objects.create(article=article, user=self.reader, body="http://a http://b http://c",
                               is_approved=False, held_reason="لینک زیاد")
        note = Notification.objects.get(kind=Notification.Kind.MODERATION)
        self.assertEqual(note.user, self.editor)  # authors can't moderate
        self.assertIn("لینک زیاد", note.message)
        Comment.objects.create(article=article, user=self.reader, body="عادی")
        self.assertEqual(Notification.objects.filter(kind=Notification.Kind.MODERATION).count(), 1)


class NotificationTests(TransactionTestCase):
    """TransactionTestCase so on_commit notification hooks actually run."""

    def setUp(self):
        self.cat = Category.objects.create(name="وب", slug="web")
        self.follower = User.objects.create_user("f", "f@example.com", "pass-12345-x")
        self.quiet = User.objects.create_user("q", "q@example.com", "pass-12345-x", email_notifications=False)
        TopicFollow.objects.create(user=self.follower, category=self.cat)
        TopicFollow.objects.create(user=self.quiet, category=self.cat)

    def test_publishing_notifies_followers_once(self):
        article = make_article(self.cat, title="مطلب تازه")
        self.assertEqual(Notification.objects.filter(kind="new_article").count(), 2)
        self.assertEqual([m.to for m in mail.outbox], [["f@example.com"]])
        article.title = "ویرایش"
        article.save()
        self.assertEqual(Notification.objects.count(), 2)

    def test_scheduled_article_notifies_when_due(self):
        article = make_article(self.cat, published_at=timezone.now() + timedelta(hours=1))
        self.assertFalse(Notification.objects.exists())
        Article.objects.filter(pk=article.pk).update(published_at=timezone.now() - timedelta(minutes=1))
        services.dispatch_pending_notifications()
        self.assertEqual(Notification.objects.count(), 2)

    def test_reply_notification_and_bell(self):
        article = make_article(self.cat)
        Notification.objects.all().delete()
        parent = Comment.objects.create(article=article, user=self.follower, body="سؤال")
        Comment.objects.create(article=article, user=self.quiet, body="جواب", parent=parent)
        note = Notification.objects.get(user=self.follower)
        self.assertEqual(note.kind, "reply")
        self.client.force_login(self.follower)
        self.assertContains(self.client.get(reverse("magazine:home")), "اعلان‌ها")
        response = self.client.get(reverse("newsletter:open_notification", args=[note.pk]))
        self.assertRedirects(response, note.url, fetch_redirect_response=False)
        note.refresh_from_db()
        self.assertTrue(note.is_read)
