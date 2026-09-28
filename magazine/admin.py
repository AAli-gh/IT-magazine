from django.contrib import admin
from django.utils.html import format_html

from .models import Article, Category, Tag

admin.site.site_header = "پنل مدیریت مجله فناوری"
admin.site.site_title = "مجله فناوری"
admin.site.index_title = "مدیریت محتوا"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("__str__", "slug", "order", "show_on_home", "article_count")
    list_editable = ("order", "show_on_home")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    fieldsets = (
        (None, {"fields": ("name", "slug", "icon", "description", "order", "show_on_home")}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )

    @admin.display(description="تعداد مطالب")
    def article_count(self, obj):
        return obj.articles.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title", "content_type", "category", "author", "status",
        "is_featured", "is_editor_pick", "published_at", "views_count", "view_link",
    )
    list_filter = ("status", "content_type", "category", "is_featured", "is_editor_pick", "published_at")
    list_editable = ("status", "is_featured", "is_editor_pick")
    search_fields = ("title", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("tags",)
    raw_id_fields = ("author",)
    date_hierarchy = "published_at"
    readonly_fields = ("reading_time", "views_count", "updated_at")
    list_per_page = 30
    fieldsets = (
        (None, {"fields": ("title", "slug", "content_type", "category", "tags", "author")}),
        ("محتوا", {"fields": ("cover", "excerpt", "body", "video_url", "audio_url", "source_url")}),
        ("انتشار", {"fields": ("status", "published_at", "is_featured", "is_editor_pick",
                              "reading_time", "views_count", "updated_at")}),
        ("AI Daily", {
            "fields": ("ai_daily_number", "why_important", "use_cases", "developer_impact"),
            "classes": ("collapse",),
            "description": "برای نوع محتوای AI Daily؛ اگر شماره خالی بماند خودکار تعیین می‌شود.",
        }),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )
    actions = ["publish", "unpublish", "feature"]

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description="مشاهده")
    def view_link(self, obj):
        return format_html('<a href="{}" target="_blank">↗</a>', obj.get_absolute_url())

    @admin.action(description="انتشار مطالب انتخاب‌شده")
    def publish(self, request, queryset):
        queryset.update(status=Article.Status.PUBLISHED)

    @admin.action(description="برگرداندن به پیش‌نویس")
    def unpublish(self, request, queryset):
        queryset.update(status=Article.Status.DRAFT)

    @admin.action(description="تنظیم به عنوان مهم‌ترین مطلب روز")
    def feature(self, request, queryset):
        queryset.update(is_featured=True)
