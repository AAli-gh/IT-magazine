from django.conf import settings

from magazine.models import Article, Category

from .models import Page


def site(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_NAME_EN": settings.SITE_NAME_EN,
        "SITE_URL": settings.SITE_URL.rstrip("/"),
        "SITE_DESCRIPTION": settings.SITE_DESCRIPTION,
        "nav_categories": Category.objects.all(),
        "content_types": Article.ContentType.choices,
        "footer_pages": Page.objects.filter(is_published=True, show_in_footer=True),
    }
