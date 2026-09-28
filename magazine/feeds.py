from django.conf import settings
from django.contrib.syndication.views import Feed
from django.db.models import Q
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


class PodcastFeed(LatestArticlesFeed):
    """Podcast episodes with audio enclosures, for podcast apps."""

    title = f"پادکست {settings.SITE_NAME}"
    link = "/type/podcast/"

    def items(self):
        return (Article.objects.published().with_relations()
                .filter(content_type=Article.ContentType.PODCAST)
                .filter(~Q(audio_file="") | ~Q(audio_url=""))[:50])

    def item_enclosure_url(self, item):
        src = item.audio_src
        return src if src.startswith("http") else settings.SITE_URL.rstrip("/") + src

    def item_enclosure_length(self, item):
        try:
            return item.audio_file.size if item.audio_file else 0
        except OSError:
            return 0

    def item_enclosure_mime_type(self, item):
        name = (item.audio_file.name if item.audio_file else item.audio_url).lower()
        return {"m4a": "audio/mp4", "ogg": "audio/ogg", "wav": "audio/wav"}.get(name.rsplit(".", 1)[-1], "audio/mpeg")
