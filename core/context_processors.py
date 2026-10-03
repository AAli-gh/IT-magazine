from django.conf import settings
from django.core.cache import cache

from magazine.models import Article, Category

from .cache import content_version
from .models import Page, SiteSettings


def _cached(name, builder):
    key = f"ctx:{name}:{content_version()}"
    value = cache.get(key)
    if value is None:
        value = builder()
        cache.set(key, value, 3600)
    return value


def site(request):
    site_settings = SiteSettings.load()
    unread = 0
    if getattr(request, "user", None) and request.user.is_authenticated:
        unread = request.user.notifications.filter(is_read=False).count()
    return {
        "SITE_NAME": site_settings.site_name or settings.SITE_NAME,
        "SITE_NAME_EN": settings.SITE_NAME_EN,
        "SITE_URL": settings.SITE_URL.rstrip("/"),
        "SITE_DESCRIPTION": site_settings.site_description or settings.SITE_DESCRIPTION,
        "site_settings": site_settings,
        "nav_categories": _cached("categories", lambda: list(Category.objects.all())),
        "content_types": Article.ContentType.choices,
        "footer_pages": _cached("pages", lambda: list(
            Page.objects.filter(is_published=True, show_in_footer=True))),
        "unread_notifications": unread,
        "error_layout": "base.html",  # error pages rendered with a request use the full site layout
    }
