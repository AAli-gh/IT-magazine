from django.core.paginator import Paginator
from django.db.models import Count, F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from interactions.forms import CommentForm
from interactions.models import Bookmark, Like, ReadingHistory, TopicFollow

from .models import Article, Category, Tag

PAGE_SIZE = 12
SORT_OPTIONS = {
    "new": ("-published_at", "جدیدترین"),
    "old": ("published_at", "قدیمی‌ترین"),
    "popular": ("-views_count", "پربازدیدترین"),
}


def _published():
    return Article.objects.published().with_relations()


def _paginate(request, queryset):
    return Paginator(queryset, PAGE_SIZE).get_page(request.GET.get("page"))


def home(request):
    articles = _published()
    featured = articles.filter(is_featured=True).first() or articles.first()
    exclude_ids = [featured.pk] if featured else []

    category_sections = []
    for category in Category.objects.filter(show_on_home=True):
        items = list(articles.filter(category=category).exclude(pk__in=exclude_ids)[:4])
        if items:
            category_sections.append((category, items))

    context = {
        "featured": featured,
        "latest": articles.exclude(pk__in=exclude_ids)[:6],
        "category_sections": category_sections,
        "ai_daily": articles.filter(content_type=Article.ContentType.AI_DAILY).first(),
        "tutorials": articles.filter(content_type=Article.ContentType.TUTORIAL).order_by(
            "-is_editor_pick", "-published_at"
        )[:4],
        "news": articles.filter(content_type=Article.ContentType.NEWS)[:6],
        "popular": articles.order_by("-views_count")[:5],
    }
    return render(request, "magazine/home.html", context)


def article_detail(request, slug):
    article = get_object_or_404(Article.objects.with_relations(), slug=slug)
    if not article.is_published and not request.user.is_staff:
        raise Http404

    Article.objects.filter(pk=article.pk).update(views_count=F("views_count") + 1)

    user = request.user
    liked = bookmarked = False
    if user.is_authenticated:
        ReadingHistory.objects.update_or_create(user=user, article=article)
        liked = Like.objects.filter(user=user, article=article).exists()
        bookmarked = Bookmark.objects.filter(user=user, article=article).exists()

    comments = (
        article.comments.filter(is_approved=True, parent__isnull=True)
        .select_related("user")
        .prefetch_related("replies__user")
    )
    context = {
        "article": article,
        "related": article.related(),
        "comments": comments,
        "comment_form": CommentForm(),
        "liked": liked,
        "bookmarked": bookmarked,
        "like_count": article.like_set.count(),
    }
    return render(request, "magazine/article_detail.html", context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    following = (
        request.user.is_authenticated
        and TopicFollow.objects.filter(user=request.user, category=category).exists()
    )
    context = {
        "category": category,
        "page_obj": _paginate(request, _published().filter(category=category)),
        "following": following,
        "follower_count": category.followers.count(),
    }
    return render(request, "magazine/category_detail.html", context)


def tag_detail(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    context = {"tag": tag, "page_obj": _paginate(request, _published().filter(tags=tag))}
    return render(request, "magazine/tag_detail.html", context)


def content_type_list(request, content_type):
    labels = dict(Article.ContentType.choices)
    if content_type not in labels:
        raise Http404
    context = {
        "content_type": content_type,
        "content_type_label": labels[content_type],
        "page_obj": _paginate(request, _published().filter(content_type=content_type)),
    }
    return render(request, "magazine/content_type_list.html", context)


def ai_daily_list(request):
    qs = _published().filter(content_type=Article.ContentType.AI_DAILY).order_by("-ai_daily_number")
    return render(request, "magazine/ai_daily_list.html", {"page_obj": _paginate(request, qs)})


def ai_daily_detail(request, number):
    article = get_object_or_404(Article, ai_daily_number=number)
    return redirect(article, permanent=True)


def search(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    content_type = request.GET.get("type", "")
    tag = request.GET.get("tag", "")
    sort = request.GET.get("sort", "new")

    results = _published().search(q)
    if category:
        results = results.filter(category__slug=category)
    if content_type:
        results = results.filter(content_type=content_type)
    if tag:
        results = results.filter(tags__slug=tag)
    results = results.order_by(SORT_OPTIONS.get(sort, SORT_OPTIONS["new"])[0])

    has_query = any([q, category, content_type, tag])
    context = {
        "q": q,
        "selected_category": category,
        "selected_type": content_type,
        "selected_tag": tag,
        "sort": sort,
        "sort_options": [(k, v[1]) for k, v in SORT_OPTIONS.items()],
        "page_obj": _paginate(request, results) if has_query else None,
        "popular_tags": Tag.objects.annotate(n=Count("articles")).filter(n__gt=0).order_by("-n")[:20],
    }
    template = "magazine/partials/search_results.html" if request.headers.get("HX-Request") else "magazine/search.html"
    return render(request, template, context)
