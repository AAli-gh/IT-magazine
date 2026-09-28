"""HTMX endpoints: like, bookmark, follow topic, comment.

Each endpoint returns a small HTML fragment that replaces the triggering
widget. Unauthenticated HTMX requests are redirected to login via the
``HX-Redirect`` header so the whole page navigates.
"""

from functools import wraps
from urllib.parse import quote

from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from magazine.models import Article, Category

from .forms import CommentForm
from .models import Bookmark, Comment, Like, TopicFollow


def login_required_htmx(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view(request, *args, **kwargs)
        next_url = request.headers.get("HX-Current-URL") or request.get_full_path()
        if request.headers.get("HX-Request"):
            response = HttpResponse(status=204)
            response["HX-Redirect"] = f"{reverse('accounts:login')}?next={quote(next_url)}"
            return response
        return redirect_to_login(next_url)

    return wrapper


def _toggle(model, **lookup):
    obj, created = model.objects.get_or_create(**lookup)
    if not created:
        obj.delete()
    return created


@require_POST
@login_required_htmx
def toggle_like(request, pk):
    article = get_object_or_404(Article.objects.published(), pk=pk)
    liked = _toggle(Like, user=request.user, article=article)
    return render(request, "interactions/partials/like_button.html", {
        "article": article, "liked": liked, "like_count": article.like_set.count(),
    })


@require_POST
@login_required_htmx
def toggle_bookmark(request, pk):
    article = get_object_or_404(Article.objects.published(), pk=pk)
    bookmarked = _toggle(Bookmark, user=request.user, article=article)
    return render(request, "interactions/partials/bookmark_button.html", {
        "article": article, "bookmarked": bookmarked,
    })


@require_POST
@login_required_htmx
def toggle_follow(request, pk):
    category = get_object_or_404(Category, pk=pk)
    following = _toggle(TopicFollow, user=request.user, category=category)
    return render(request, "interactions/partials/follow_button.html", {
        "category": category, "following": following, "follower_count": category.followers.count(),
    })


@require_POST
@login_required_htmx
def add_comment(request, pk):
    article = get_object_or_404(Article.objects.published(), pk=pk)
    form = CommentForm(request.POST)
    if not form.is_valid():
        return render(request, "interactions/partials/comment_form.html",
                      {"article": article, "comment_form": form}, status=422)

    comment = form.save(commit=False)
    comment.article = article
    comment.user = request.user
    parent_id = form.cleaned_data.get("parent_id")
    if parent_id:
        comment.parent = get_object_or_404(Comment, pk=parent_id, article=article, parent__isnull=True)
    comment.save()

    if not request.headers.get("HX-Request"):
        return redirect(f"{article.get_absolute_url()}#comments")
    return render(request, "interactions/partials/comment_created.html", {
        "article": article, "comment": comment, "comment_form": CommentForm(),
    })
