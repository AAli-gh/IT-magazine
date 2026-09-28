from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from interactions.models import Bookmark, Like, ReadingHistory
from magazine.models import Article, Category

from .forms import ProfileForm
from .models import User

PROFILE_TABS = {
    "feed": "فید من",
    "for_you": "پیشنهاد برای شما",
    "bookmarks": "ذخیره‌شده‌ها",
    "likes": "پسندیده‌ها",
    "history": "تاریخچه مطالعه",
    "topics": "موضوعات من",
}


def _articles_via(model, user):
    ids = model.objects.filter(user=user).values_list("article_id", flat=True)
    return Article.objects.published().with_relations().filter(pk__in=ids)


@login_required
def profile(request):
    user = request.user
    tab = request.GET.get("tab", "feed")
    if tab not in PROFILE_TABS:
        tab = "feed"

    articles = None
    if tab == "feed":
        articles = Article.objects.published().with_relations().filter(
            category__followers__user=user
        )
    elif tab == "for_you":
        from magazine.recommender import for_user_ids

        ids = for_user_ids(user, 24)
        found = Article.objects.published().with_relations().in_bulk(ids)
        articles = [found[pk] for pk in ids if pk in found]
    elif tab == "bookmarks":
        articles = _articles_via(Bookmark, user)
    elif tab == "likes":
        articles = _articles_via(Like, user)
    elif tab == "history":
        history = ReadingHistory.objects.filter(user=user).select_related("article__category")
        articles = [h.article for h in history if h.article.is_published]

    context = {
        "tab": tab,
        "tabs": PROFILE_TABS.items(),
        "page_obj": Paginator(articles, 12).get_page(request.GET.get("page")) if articles is not None else None,
        "followed_ids": set(user.followed_topics.values_list("category_id", flat=True)),
        "topic_categories": Category.objects.annotate(follower_count=Count("followers")) if tab == "topics" else None,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def edit_profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "پروفایل به‌روزرسانی شد.")
        return redirect("accounts:profile")
    return render(request, "accounts/edit_profile.html", {"form": form})


def author(request, username):
    person = get_object_or_404(User, username=username)
    articles = Article.objects.published().with_relations().filter(author=person)
    context = {
        "person": person,
        "page_obj": Paginator(articles, 12).get_page(request.GET.get("page")),
    }
    return render(request, "accounts/author.html", context)
