from django.conf import settings
from django.db import models

from magazine.models import Article, Category


class UserArticleRelation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کاربر")
    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name="مطلب")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} → {self.article}"


class Like(UserArticleRelation):
    class Meta(UserArticleRelation.Meta):
        verbose_name = "لایک"
        verbose_name_plural = "لایک‌ها"
        constraints = [models.UniqueConstraint(fields=["user", "article"], name="unique_like")]


class Bookmark(UserArticleRelation):
    class Meta(UserArticleRelation.Meta):
        verbose_name = "ذخیره"
        verbose_name_plural = "مطالب ذخیره‌شده"
        constraints = [models.UniqueConstraint(fields=["user", "article"], name="unique_bookmark")]


class ReadingHistory(UserArticleRelation):
    last_read_at = models.DateTimeField("آخرین مطالعه", auto_now=True)

    class Meta:
        ordering = ["-last_read_at"]
        verbose_name = "تاریخچه مطالعه"
        verbose_name_plural = "تاریخچه مطالعه"
        constraints = [models.UniqueConstraint(fields=["user", "article"], name="unique_history")]


class TopicFollow(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followed_topics", verbose_name="کاربر"
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="followers", verbose_name="موضوع")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "دنبال‌کردن موضوع"
        verbose_name_plural = "موضوعات دنبال‌شده"
        constraints = [models.UniqueConstraint(fields=["user", "category"], name="unique_follow")]

    def __str__(self):
        return f"{self.user} → {self.category}"


class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments", verbose_name="مطلب")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کاربر")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies", verbose_name="پاسخ به"
    )
    body = models.TextField("متن دیدگاه", max_length=3000)
    is_approved = models.BooleanField("تأیید شده", default=True)
    is_deleted = models.BooleanField("حذف‌شده توسط کاربر", default=False)
    held_reason = models.CharField("دلیل نگه‌داشتن برای بررسی", max_length=100, blank=True)
    created_at = models.DateTimeField("تاریخ", auto_now_add=True)
    edited_at = models.DateTimeField("آخرین ویرایش", null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "دیدگاه"
        verbose_name_plural = "دیدگاه‌ها"

    def __str__(self):
        return f"{self.user}: {self.body[:40]}"

    def can_edit(self, user):
        return user.is_authenticated and user.pk == self.user_id and not self.is_deleted

    def can_delete(self, user):
        return user.is_authenticated and (user.pk == self.user_id or user.is_staff) and not self.is_deleted
