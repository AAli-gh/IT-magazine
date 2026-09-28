from django.contrib import admin, messages

from . import services
from .models import NewsletterIssue, Notification, Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "is_confirmed", "is_active", "wants_ai_daily", "wants_weekly", "created_at")
    list_filter = ("is_confirmed", "is_active", "wants_ai_daily", "wants_weekly")
    search_fields = ("email",)
    actions = ["send_ai_daily_now", "send_weekly_now"]

    @admin.action(description="ارسال آخرین AI Daily به مشترکین (اگر قبلاً ارسال نشده)")
    def send_ai_daily_now(self, request, queryset):
        sent = services.send_ai_daily()
        self._report(request, sent)

    @admin.action(description="ارسال خلاصه هفتگی (اگر این هفته ارسال نشده)")
    def send_weekly_now(self, request, queryset):
        self._report(request, services.send_weekly_digest())

    def _report(self, request, sent):
        if sent is None:
            self.message_user(request, "این شماره قبلاً ارسال شده یا مطلبی برای ارسال نیست.", messages.WARNING)
        else:
            self.message_user(request, f"برای {sent} مشترک ارسال شد.")


@admin.register(NewsletterIssue)
class NewsletterIssueAdmin(admin.ModelAdmin):
    list_display = ("subject", "kind", "key", "recipients", "sent_at")
    list_filter = ("kind",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "message", "is_read", "created_at")
    list_filter = ("kind", "is_read")
    raw_id_fields = ("user",)
