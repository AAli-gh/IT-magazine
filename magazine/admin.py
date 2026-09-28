from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html

from .models import Article, Category, InterviewQA, MediaFile, NewsSource, Tag
from .widgets import MarkdownEditorWidget

admin.site.site_header = "پنل مدیریت مجله فناوری"
admin.site.site_title = "مجله فناوری"
admin.site.index_title = "داشبورد"
admin.site.index_template = "admin/dashboard.html"


def can_publish(request):
    return request.user.has_perm("magazine.publish_article")


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


class InterviewQAInline(admin.StackedInline):
    model = InterviewQA
    extra = 0
    fields = ("order", "question", "answer")
    classes = ("collapse",)
    verbose_name_plural = "پرسش و پاسخ‌های مصاحبه (فقط برای نوع «مصاحبه»)"


class MediaFileInline(admin.TabularInline):
    model = MediaFile
    extra = 1
    fields = ("image", "alt", "caption", "preview", "markdown_snippet")
    readonly_fields = ("preview", "markdown_snippet")
    verbose_name_plural = "تصاویر این مطلب (کد Markdown را در متن کپی کنید)"

    @admin.display(description="پیش‌نمایش")
    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="max-height:60px;border-radius:6px">', obj.image.url)
        return "-"

    @admin.display(description="کد Markdown")
    def markdown_snippet(self, obj):
        if obj.pk and obj.image:
            return format_html('<input readonly value="{}" style="width:22em;direction:ltr" onclick="this.select()">',
                               obj.markdown)
        return "-"


class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = "__all__"
        widgets = {"body": MarkdownEditorWidget()}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = (
        "title", "content_type", "category", "author", "status_badge",
        "is_featured", "published_at", "views_count", "view_link",
    )
    list_filter = ("status", "content_type", "category", "is_featured", "is_editor_pick", "ai_generated", "published_at")
    search_fields = ("title", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("tags",)
    raw_id_fields = ("author",)
    date_hierarchy = "published_at"
    list_per_page = 30
    inlines = [MediaFileInline, InterviewQAInline]
    actions = ["submit_for_review", "publish", "unpublish", "feature", "unfeature"]
    fieldsets = (
        (None, {"fields": ("title", "slug", "content_type", "category", "tags", "author")}),
        ("محتوا", {"fields": ("cover", "excerpt", "body", "source_url")}),
        ("ویدئو و پادکست", {
            "fields": ("video_url", "video_file", "audio_url", "audio_file", "media_duration"),
            "classes": ("collapse",),
        }),
        ("مصاحبه", {"fields": ("interviewee_name", "interviewee_title", "interviewee_photo"), "classes": ("collapse",)}),
        ("انتشار", {
            "fields": ("status", "published_at", "is_featured", "is_editor_pick",
                       "reading_time", "views_count", "updated_at", "ai_generated"),
            "description": "برای انتشار زمان‌بندی‌شده، تاریخ انتشار را در آینده تنظیم کنید.",
        }),
        ("AI Daily", {
            "fields": ("ai_daily_number", "why_important", "use_cases", "developer_impact"),
            "classes": ("collapse",),
            "description": "برای نوع محتوای AI Daily؛ اگر شماره خالی بماند خودکار تعیین می‌شود.",
        }),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )

    # --- Role-based access: authors see and edit only their own unpublished articles ---

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("category", "author")
        return qs if can_publish(request) else qs.filter(author=request.user)

    def get_readonly_fields(self, request, obj=None):
        fields = ["reading_time", "views_count", "updated_at", "ai_generated"]
        if not can_publish(request):
            fields += ["author", "is_featured", "is_editor_pick", "ai_daily_number"]
        return fields

    def has_change_permission(self, request, obj=None):
        allowed = super().has_change_permission(request, obj)
        if allowed and obj is not None and not can_publish(request):
            return obj.author_id == request.user.pk and obj.status != Article.Status.PUBLISHED
        return allowed

    def has_delete_permission(self, request, obj=None):
        return can_publish(request) and super().has_delete_permission(request, obj)

    def has_publish_permission(self, request):
        return can_publish(request)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "status" and not can_publish(request):
            kwargs["choices"] = [(Article.Status.DRAFT, Article.Status.DRAFT.label),
                                 (Article.Status.REVIEW, Article.Status.REVIEW.label)]
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        if not can_publish(request) and obj.status == Article.Status.PUBLISHED:
            obj.status = Article.Status.REVIEW
        super().save_model(request, obj, form, change)

    def get_changeform_initial_data(self, request):
        return {**super().get_changeform_initial_data(request), "author": request.user.pk}

    # --- List display ---

    @admin.display(description="وضعیت", ordering="status")
    def status_badge(self, obj):
        colors = {"draft": "#64748b", "review": "#d97706", "published": "#16a34a"}
        return format_html('<span style="color:{};font-weight:600">● {}</span>',
                           colors.get(obj.status, "#64748b"), obj.get_status_display())

    @admin.display(description="مشاهده")
    def view_link(self, obj):
        return format_html('<a href="{}" target="_blank">↗</a>', obj.get_absolute_url())

    # --- Actions ---

    @admin.action(description="ارسال برای بررسی سردبیر")
    def submit_for_review(self, request, queryset):
        updated = queryset.filter(status=Article.Status.DRAFT).update(status=Article.Status.REVIEW)
        self.message_user(request, f"{updated} مطلب برای بررسی ارسال شد.")

    @admin.action(description="انتشار مطالب انتخاب‌شده", permissions=["publish"])
    def publish(self, request, queryset):
        # save() per object so signals (notifications, caches) run.
        for article in queryset.exclude(status=Article.Status.PUBLISHED):
            article.status = Article.Status.PUBLISHED
            article.save()
        self.message_user(request, "مطالب منتشر شدند.")

    @admin.action(description="برگرداندن به پیش‌نویس", permissions=["publish"])
    def unpublish(self, request, queryset):
        for article in queryset:
            article.status = Article.Status.DRAFT
            article.save()

    @admin.action(description="تنظیم به عنوان مهم‌ترین مطلب روز", permissions=["publish"])
    def feature(self, request, queryset):
        for article in queryset:
            article.is_featured = True
            article.save()

    @admin.action(description="حذف از مطالب ویژه", permissions=["publish"])
    def unfeature(self, request, queryset):
        for article in queryset:
            article.is_featured = False
            article.save()


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ("thumb", "alt", "article", "uploaded_by", "created_at", "markdown_snippet")
    search_fields = ("alt", "caption")
    raw_id_fields = ("article",)
    exclude = ("uploaded_by",)

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description="تصویر")
    def thumb(self, obj):
        return format_html('<img src="{}" style="max-height:48px;border-radius:6px">', obj.image.url)

    @admin.display(description="کد Markdown")
    def markdown_snippet(self, obj):
        return format_html('<input readonly value="{}" style="width:20em;direction:ltr" onclick="this.select()">',
                           obj.markdown)


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "feed_url", "is_active")
    list_editable = ("is_active",)
    actions = ["generate_now"]

    @admin.action(description="ساخت AI Daily امروز با Claude (از منابع فعال)")
    def generate_now(self, request, queryset):
        from .ai_daily import AIDailyError, generate_ai_daily

        try:
            article = generate_ai_daily(author=request.user)
        except AIDailyError as exc:
            self.message_user(request, str(exc), messages.ERROR)
        except Exception as exc:  # network / API errors
            self.message_user(request, f"خطا در تولید AI Daily: {exc}", messages.ERROR)
        else:
            self.message_user(request, format_html(
                'AI Daily ساخته شد: <a href="{}">{}</a> ({})',
                f"../article/{article.pk}/change/", article.display_title, article.get_status_display()))
