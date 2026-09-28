from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """Site user. Authors are users with ``is_author=True``."""

    bio = models.TextField("درباره من", blank=True)
    avatar = models.ImageField("آواتار", upload_to="avatars/", blank=True)
    website = models.URLField("وب‌سایت", blank=True)
    github = models.CharField("گیت‌هاب", max_length=100, blank=True)
    is_author = models.BooleanField("نویسنده", default=False)

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    def get_absolute_url(self):
        return reverse("accounts:author", args=[self.username])
