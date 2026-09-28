from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from core.models import Page

from .models import Article, Category, Tag


class ArticleSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Article.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.6

    def items(self):
        return Category.objects.all()


class TagSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.3

    def items(self):
        return Tag.objects.filter(articles__isnull=False).distinct()


class PageSitemap(Sitemap):
    priority = 0.4

    def items(self):
        return Page.objects.filter(is_published=True)


class StaticSitemap(Sitemap):
    priority = 1.0
    changefreq = "daily"

    def items(self):
        return ["magazine:home", "magazine:ai_daily"]

    def location(self, item):
        return reverse(item)


sitemaps = {
    "static": StaticSitemap,
    "articles": ArticleSitemap,
    "categories": CategorySitemap,
    "tags": TagSitemap,
    "pages": PageSitemap,
}
