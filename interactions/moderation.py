"""Anti-spam checks for comments."""

import re

from django.conf import settings
from django.core.cache import cache

from core.models import SiteSettings

LINK_RE = re.compile(r"https?://|www\.", re.IGNORECASE)


def rate_limited(user):
    """True when the user has posted too many comments in the current window."""
    limit, window = settings.COMMENT_RATE_LIMIT
    key = f"comment-rate:{user.pk}"
    if cache.add(key, 1, window):
        return False
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        return False
    return count > limit


def email_verified(user):
    if user.is_staff:
        return True
    from allauth.account.models import EmailAddress

    return EmailAddress.objects.filter(user=user, verified=True).exists()


def hold_reason(user, body):
    """Return why a comment should wait for moderation, or '' to publish immediately."""
    if user.is_staff:
        return ""
    site = SiteSettings.load()
    if site.comments_require_approval:
        return "تأیید دستی فعال است"
    if len(LINK_RE.findall(body)) > settings.COMMENT_MAX_LINKS:
        return "لینک زیاد"
    lowered = body.lower()
    if any(word in lowered for word in site.banned_word_list):
        return "کلمه ممنوع"
    return ""
