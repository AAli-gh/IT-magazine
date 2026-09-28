from rest_framework import viewsets

from magazine.models import Article, Category, Tag

from .serializers import ArticleDetailSerializer, ArticleListSerializer, CategorySerializer, TagSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "slug"


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """Published articles. Filters: ``?q=``, ``?category=``, ``?type=``, ``?tag=``."""

    lookup_field = "slug"
    lookup_value_regex = "[^/]+"

    def get_queryset(self):
        params = self.request.query_params
        qs = Article.objects.published().with_relations().search(params.get("q", "").strip())
        if params.get("category"):
            qs = qs.filter(category__slug=params["category"])
        if params.get("type"):
            qs = qs.filter(content_type=params["type"])
        if params.get("tag"):
            qs = qs.filter(tags__slug=params["tag"])
        return qs

    def get_serializer_class(self):
        return ArticleDetailSerializer if self.action == "retrieve" else ArticleListSerializer
