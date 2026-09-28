from django.contrib import admin

from .models import Bookmark, Comment, Like, ReadingHistory, TopicFollow


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "article", "short_body", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("body", "user__username", "article__title")
    raw_id_fields = ("article", "user", "parent")
    actions = ["approve", "unapprove"]

    @admin.display(description="متن")
    def short_body(self, obj):
        return obj.body[:80]

    @admin.action(description="تأیید دیدگاه‌ها")
    def approve(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="لغو تأیید دیدگاه‌ها")
    def unapprove(self, request, queryset):
        queryset.update(is_approved=False)


@admin.register(Like, Bookmark, ReadingHistory)
class UserArticleAdmin(admin.ModelAdmin):
    list_display = ("user", "article", "created_at")
    search_fields = ("user__username", "article__title")
    raw_id_fields = ("user", "article")


@admin.register(TopicFollow)
class TopicFollowAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "created_at")
    list_filter = ("category",)
