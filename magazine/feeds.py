from django.conf import settings
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404

from .models import Article, Category


class LatestArticlesFeed(Feed):
    title = settings.SITE_NAME
    link = "/"
    description = settings.SITE_DESCRIPTION

    def items(self):
        return Article.objects.published().with_relations()[:30]

    def item_title(self, item):
        return item.display_title

    def item_description(self, item):
        return item.excerpt

    def item_pubdate(self, item):
        return item.published_at

    def item_author_name(self, item):
        return item.author.display_name if item.author else None

    def item_categories(self, item):
        return [item.category.name, *[t.name for t in item.tags.all()]]


class CategoryFeed(LatestArticlesFeed):
    def get_object(self, request, slug):
        return get_object_or_404(Category, slug=slug)

    def title(self, obj):
        return f"{settings.SITE_NAME} — {obj.name}"

    def link(self, obj):
        return obj.get_absolute_url()

    def items(self, obj):
        return Article.objects.published().with_relations().filter(category=obj)[:30]
