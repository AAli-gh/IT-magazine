from datetime import timedelta

from django import template
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone

from interactions.models import Comment
from magazine.models import Article, ArticleDailyView
from newsletter.models import Subscriber

register = template.Library()

DAYS = 14


@register.simple_tag(takes_context=True)
def dashboard_stats(context):
    request = context["request"]
    today = timezone.localdate()
    start = today - timedelta(days=DAYS - 1)
    week_ago = timezone.now() - timedelta(days=7)
    can_publish = request.user.has_perm("magazine.publish_article")

    per_day = dict(ArticleDailyView.objects.filter(date__gte=start)
                   .values_list("date").annotate(total=Sum("views")).values_list("date", "total"))
    days = [start + timedelta(days=i) for i in range(DAYS)]
    series = [{"date": d, "views": per_day.get(d, 0)} for d in days]
    peak = max((d["views"] for d in series), default=0) or 1
    for point in series:
        point["pct"] = round(point["views"] * 100 / peak, 1)

    top = (ArticleDailyView.objects.filter(date__gte=today - timedelta(days=6))
           .values("article_id", "article__title", "article__slug")
           .annotate(total=Sum("views")).order_by("-total")[:5])

    articles = Article.objects.all()
    if not can_publish:
        articles = articles.filter(author=request.user)
    User = get_user_model()
    return {
        "can_publish": can_publish,
        "tiles": [
            ("مطالب منتشرشده", articles.filter(status=Article.Status.PUBLISHED).count()),
            ("در انتظار بررسی", articles.filter(status=Article.Status.REVIEW).count()),
            ("بازدید ۷ روز اخیر", sum(d["views"] for d in series[-7:])),
            ("کاربران جدید (۷ روز)", User.objects.filter(date_joined__gte=week_ago).count()),
            ("مشترکین خبرنامه", Subscriber.objects.filter(is_confirmed=True, is_active=True).count()),
            ("دیدگاه‌های در انتظار", Comment.objects.filter(is_approved=False, is_deleted=False).count()),
        ],
        "series": series,
        "peak": peak,
        "top": list(top),
        "review_queue": list(articles.filter(status=Article.Status.REVIEW)
                             .select_related("author").order_by("-updated_at")[:5]),
        "scheduled": list(articles.filter(status=Article.Status.PUBLISHED, published_at__gt=timezone.now())
                          .order_by("published_at")[:5]),
    }
