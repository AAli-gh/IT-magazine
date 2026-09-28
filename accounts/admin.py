from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "get_full_name", "is_author", "is_staff", "date_joined")
    list_filter = ("is_author", "is_staff", "is_superuser", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("پروفایل", {"fields": ("bio", "avatar", "website", "github", "is_author")}),
    )
    actions = ["make_author"]

    @admin.action(description="تبدیل به نویسنده")
    def make_author(self, request, queryset):
        queryset.update(is_author=True)
