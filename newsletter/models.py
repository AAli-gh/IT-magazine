import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse


class Subscriber(models.Model):
    email = models.EmailField("ایمیل", unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_confirmed = models.BooleanField("تأیید شده", default=False)
    wants_ai_daily = models.BooleanField("AI Daily روزانه", default=True)
    wants_weekly = models.BooleanField("خلاصه هفتگی", default=True)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("تاریخ عضویت", auto_now_add=True)
    confirmed_at = models.DateTimeField("تاریخ تأیید", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "مشترک خبرنامه"
        verbose_name_plural = "مشترکین خبرنامه"

    def __str__(self):
        return self.email

    @property
    def confirm_url(self):
        return reverse("newsletter:confirm", args=[self.token])

    @property
    def unsubscribe_url(self):
        return reverse("newsletter:unsubscribe", args=[self.token])


class NewsletterIssue(models.Model):
    """Log of sent newsletters; the unique key prevents sending the same issue twice."""

    class Kind(models.TextChoices):
        AI_DAILY = "ai_daily", "AI Daily"
        WEEKLY = "weekly", "خلاصه هفتگی"

    kind = models.CharField("نوع", max_length=20, choices=Kind.choices)
    key = models.CharField("شناسه", max_length=50, help_text="شماره AI Daily یا هفته (مثلاً 2026-W39)")
    subject = models.CharField("موضوع", max_length=200)
    recipients = models.PositiveIntegerField("تعداد گیرندگان", default=0)
    sent_at = models.DateTimeField("زمان ارسال", auto_now_add=True)

    class Meta:
        ordering = ["-sent_at"]
        verbose_name = "خبرنامه ارسال‌شده"
        verbose_name_plural = "خبرنامه‌های ارسال‌شده"
        constraints = [models.UniqueConstraint(fields=["kind", "key"], name="unique_issue")]

    def __str__(self):
        return self.subject


class Notification(models.Model):
    class Kind(models.TextChoices):
        NEW_ARTICLE = "new_article", "مطلب جدید"
        REPLY = "reply", "پاسخ به دیدگاه"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    message = models.CharField(max_length=300)
    url = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"

    def __str__(self):
        return self.message
