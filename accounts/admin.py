from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User
from .roles import ensure_roles, make_author, make_editor


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "get_full_name", "is_author", "is_staff", "date_joined")
    list_filter = ("is_author", "is_staff", "is_superuser", "is_active", "groups")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("پروفایل", {"fields": ("bio", "avatar", "website", "github", "is_author", "email_notifications")}),
    )
    actions = ["action_make_author", "action_make_editor"]

    @admin.action(description="تبدیل به نویسنده (دسترسی به پنل برای نوشتن مطلب)")
    def action_make_author(self, request, queryset):
        ensure_roles()
        for user in queryset:
            make_author(user)
        self.message_user(request, f"{queryset.count()} کاربر نویسنده شدند.")

    @admin.action(description="تبدیل به سردبیر (انتشار و مدیریت محتوا)")
    def action_make_editor(self, request, queryset):
        ensure_roles()
        for user in queryset:
            make_editor(user)
        self.message_user(request, f"{queryset.count()} کاربر سردبیر شدند.")

