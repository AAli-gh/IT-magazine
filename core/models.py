from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from magazine.models import SEOFields
from magazine.rendering import render_markdown


class Page(SEOFields):
    """Static site pages: about us, contact, terms, ..."""

    title = models.CharField("عنوان", max_length=200)
    slug = models.SlugField("اسلاگ", unique=True, allow_unicode=True)
    body = models.TextField("متن (Markdown)")
    is_published = models.BooleanField("منتشر شده", default=True)
    show_in_footer = models.BooleanField("نمایش در فوتر", default=True)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "صفحه"
        verbose_name_plural = "صفحات سایت"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:page", args=[self.slug])

    @property
    def body_html(self):
        return render_markdown(self.body)[0]


class BannerQuerySet(models.QuerySet):
    def active(self, position=None):
        now = timezone.now()
        qs = self.filter(is_active=True).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now),
            Q(ends_at__isnull=True) | Q(ends_at__gte=now),
        )
        if position:
            qs = qs.filter(position=position)
        return qs


class Banner(models.Model):
    """Banners and advertisements shown in fixed slots of the site."""

    class Position(models.TextChoices):
        HOME_TOP = "home_top", "بالای صفحه اصلی"
        HOME_MIDDLE = "home_middle", "میانه صفحه اصلی"
        SIDEBAR = "sidebar", "سایدبار"
        ARTICLE_BOTTOM = "article_bottom", "انتهای مقاله"

    class Kind(models.TextChoices):
        BANNER = "banner", "بنر"
        AD = "ad", "تبلیغ"

    title = models.CharField("عنوان", max_length=150)
    kind = models.CharField("نوع", max_length=10, choices=Kind.choices, default=Kind.BANNER)
    position = models.CharField("جایگاه", max_length=20, choices=Position.choices)
    image = models.ImageField("تصویر", upload_to="banners/", blank=True)
    text = models.CharField("متن", max_length=250, blank=True)
    link = models.URLField("لینک", blank=True)
    is_active = models.BooleanField("فعال", default=True)
    starts_at = models.DateTimeField("شروع نمایش", null=True, blank=True)
    ends_at = models.DateTimeField("پایان نمایش", null=True, blank=True)
    order = models.PositiveIntegerField("ترتیب", default=0)

    objects = BannerQuerySet.as_manager()

    class Meta:
        ordering = ["order", "-id"]
        verbose_name = "بنر / تبلیغ"
        verbose_name_plural = "بنرها و تبلیغات"

    def __str__(self):
        return self.title


class SiteSettings(models.Model):
    """Singleton with site-wide settings editable from the admin panel."""

    site_name = models.CharField("نام سایت", max_length=100, blank=True,
                                 help_text="خالی = مقدار پیش‌فرض از تنظیمات سرور")
    site_description = models.CharField("توضیحات سایت (SEO)", max_length=300, blank=True)
    default_og_image = models.ImageField("تصویر پیش‌فرض اشتراک‌گذاری (OG)", upload_to="site/", blank=True)
    contact_email = models.EmailField("ایمیل تماس", blank=True)
    telegram_url = models.URLField("تلگرام", blank=True)
    instagram_url = models.URLField("اینستاگرام", blank=True)
    twitter_url = models.URLField("ایکس (توییتر)", blank=True)
    linkedin_url = models.URLField("لینکدین", blank=True)
    github_url = models.URLField("گیت‌هاب", blank=True)
    head_scripts = models.TextField(
        "کدهای head (آنالیتیکس)", blank=True,
        help_text="فقط کد مورد اعتماد وارد کنید؛ بدون تغییر در head همه صفحات قرار می‌گیرد.",
    )
    comments_require_approval = models.BooleanField("دیدگاه‌ها قبل از نمایش تأیید شوند", default=False)
    banned_words = models.TextField("کلمات ممنوع در دیدگاه‌ها", blank=True, help_text="هر کلمه در یک خط")
    ai_daily_auto_publish = models.BooleanField(
        "انتشار خودکار AI Daily", default=False,
        help_text="اگر خاموش باشد، AI Daily تولیدشده به‌صورت «در انتظار بررسی» ذخیره می‌شود.",
    )

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return "تنظیمات سایت"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        from django.core.cache import cache

        obj = cache.get("site_settings")
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set("site_settings", obj, 3600)
        return obj

    @property
    def banned_word_list(self):
        return [w.strip().lower() for w in self.banned_words.splitlines() if w.strip()]
