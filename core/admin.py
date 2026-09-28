from django.contrib import admin

from .models import Banner, Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "show_in_footer", "order")
    list_editable = ("is_published", "show_in_footer", "order")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "body")
    fieldsets = (
        (None, {"fields": ("title", "slug", "body", "is_published", "show_in_footer", "order")}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "position", "is_active", "starts_at", "ends_at", "order")
    list_filter = ("kind", "position", "is_active")
    list_editable = ("is_active", "order")
    search_fields = ("title", "text")
