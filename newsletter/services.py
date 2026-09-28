"""Sending newsletters and creating notifications."""

import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.utils import timezone

from interactions.models import TopicFollow
from magazine.models import Article

from .models import NewsletterIssue, Notification, Subscriber

logger = logging.getLogger(__name__)


def absolute(url):
    return settings.SITE_URL.rstrip("/") + url


def _message(template, context, to, subject, connection=None, headers=None):
    context = {**context, "SITE_NAME": settings.SITE_NAME, "SITE_URL": settings.SITE_URL.rstrip("/")}
    text = render_to_string(f"newsletter/email/{template}.txt", context)
    html = render_to_string(f"newsletter/email/{template}.html", context)
    msg = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [to],
                                 connection=connection, headers=headers or {})
    msg.attach_alternative(html, "text/html")
    return msg


def send_confirmation(subscriber):
    _message("confirm", {"confirm_url": absolute(subscriber.confirm_url)}, subscriber.email,
             f"تأیید عضویت در خبرنامه {settings.SITE_NAME}").send(fail_silently=True)


def _send_issue(kind, key, subject, template, context, subscribers):
    """Send one issue to subscribers; returns recipient count, or None if already sent."""
    try:
        with transaction.atomic():
            issue = NewsletterIssue.objects.create(kind=kind, key=key, subject=subject)
    except IntegrityError:
        return None
    sent = 0
    connection = get_connection()
    for subscriber in subscribers.iterator():
        unsubscribe = absolute(subscriber.unsubscribe_url)
        msg = _message(template, {**context, "unsubscribe_url": unsubscribe}, subscriber.email, subject,
                       connection=connection, headers={"List-Unsubscribe": f"<{unsubscribe}>"})
        try:
            msg.send()
            sent += 1
        except Exception:
            logger.exception("Newsletter to %s failed", subscriber.email)
    issue.recipients = sent
    issue.save(update_fields=["recipients"])
    return sent


def active_subscribers():
    return Subscriber.objects.filter(is_confirmed=True, is_active=True)


def send_ai_daily(article=None):
    article = article or Article.objects.published().filter(
        content_type=Article.ContentType.AI_DAILY).order_by("-ai_daily_number").first()
    if not article or not article.is_published:
        return None
    return _send_issue(
        NewsletterIssue.Kind.AI_DAILY, str(article.ai_daily_number), article.display_title, "ai_daily",
        {"article": article, "article_url": absolute(article.get_absolute_url())},
        active_subscribers().filter(wants_ai_daily=True),
    )


def send_weekly_digest(now=None):
    now = now or timezone.now()
    year, week, _ = now.isocalendar()
    articles = list(Article.objects.published().filter(published_at__gte=now - timedelta(days=7))
                    .select_related("category").order_by("-views_count")[:7])
    if not articles:
        return None
    items = [{"article": a, "url": absolute(a.get_absolute_url())} for a in articles]
    return _send_issue(
        NewsletterIssue.Kind.WEEKLY, f"{year}-W{week:02d}", f"خلاصه هفتگی {settings.SITE_NAME}", "weekly",
        {"items": items}, active_subscribers().filter(wants_weekly=True),
    )


def notify_followers(article):
    """Notify users following the article's topic, once per article (in-site + optional email)."""
    if article.notified_at or not article.is_published:
        return 0
    now = timezone.now()
    updated = Article.objects.filter(pk=article.pk, notified_at__isnull=True).update(notified_at=now)
    if not updated:  # another process got there first
        return 0
    article.notified_at = now
    follows = TopicFollow.objects.filter(category_id=article.category_id).select_related("user")
    url = article.get_absolute_url()
    message = f"مطلب جدید در {article.category.name}: {article.display_title}"[:300]
    Notification.objects.bulk_create([
        Notification(user=f.user, kind=Notification.Kind.NEW_ARTICLE, message=message, url=url)
        for f in follows if f.user_id != article.author_id
    ])
    connection = get_connection()
    for follow in follows:
        user = follow.user
        if user.email and user.email_notifications and user.pk != article.author_id:
            try:
                _message("new_article", {"article": article, "article_url": absolute(url), "user": user},
                         user.email, message[:150], connection=connection).send()
            except Exception:
                logger.exception("Notification email to %s failed", user.email)
    return len(follows)


def dispatch_pending_notifications():
    """Catch scheduled articles whose publish time has arrived."""
    count = 0
    for article in Article.objects.published().filter(notified_at__isnull=True).select_related("category"):
        count += notify_followers(article)
    return count


def notify_reply(comment):
    parent = comment.parent
    if not parent or parent.user_id == comment.user_id or not comment.is_approved:
        return
    Notification.objects.create(
        user=parent.user, kind=Notification.Kind.REPLY,
        message=f"{comment.user.display_name} به دیدگاه شما پاسخ داد"[:300],
        url=f"{comment.article.get_absolute_url()}#comment-{comment.pk}",
    )
