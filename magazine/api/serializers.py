from rest_framework import serializers

from magazine.models import Article, Category, Tag


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "description"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class ArticleListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = serializers.CharField(source="author.display_name", default=None, read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id", "title", "display_title", "slug", "url", "content_type", "category", "tags",
            "author", "cover", "excerpt", "reading_time", "published_at", "views_count",
            "ai_daily_number",
        ]

    def get_url(self, obj):
        request = self.context.get("request")
        url = obj.get_absolute_url()
        return request.build_absolute_uri(url) if request else url


class ArticleDetailSerializer(ArticleListSerializer):
    toc = serializers.ListField(read_only=True)

    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + [
            "body", "body_html", "toc", "video_url", "audio_url", "source_url",
            "why_important", "use_cases", "developer_impact", "updated_at",
        ]
