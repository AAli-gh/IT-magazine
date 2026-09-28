from django.conf import settings
from django.db import models
from django.db.models import Max, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify

from .rendering import estimate_reading_time, render_markdown


def unique_slug(instance, value, field="slug"):
    base = slugify(value, allow_unicode=True)[:200] or "item"
    slug, n = base, 2
    model = type(instance)
    while model.objects.filter(**{field: slug}).exclude(pk=instance.pk).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


class SEOFields(models.Model):
    meta_title = models.CharField("عنوان SEO", max_length=70, blank=True)
    meta_description = models.CharField("توضیحات SEO", max_length=160, blank=True)

    class Meta:
        abstract = True


class Category(SEOFields):
    name = models.CharField("نام", max_length=100)
    slug = models.SlugField("اسلاگ", unique=True, allow_unicode=True)
    icon = models.CharField("آیکون (ایموجی)", max_length=8, blank=True)
    description = models.TextField("توضیحات", blank=True)
    order = models.PositiveIntegerField("ترتیب", default=0)
    show_on_home = models.BooleanField("نمایش در صفحه اصلی", default=False)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        return f"{self.icon} {self.name}".strip()

    def get_absolute_url(self):
        return reverse("magazine:category", args=[self.slug])


class Tag(models.Model):
    name = models.CharField("نام", max_length=60, unique=True)
    slug = models.SlugField("اسلاگ", unique=True, allow_unicode=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "تگ"
        verbose_name_plural = "تگ‌ها"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("magazine:tag", args=[self.slug])


class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Article.Status.PUBLISHED, published_at__lte=timezone.now())

    def with_relations(self):
        return self.select_related("category", "author").prefetch_related("tags")

    def search(self, query):
        if not query:
            return self
        return self.filter(
            Q(title__icontains=query)
            | Q(excerpt__icontains=query)
            | Q(body__icontains=query)
            | Q(tags__name__icontains=query)
        ).distinct()


class Article(SEOFields):
    class ContentType(models.TextChoices):
        ARTICLE = "article", "مقاله"
        NEWS = "news", "خبر"
        TUTORIAL = "tutorial", "آموزش"
        REVIEW = "review", "بررسی تکنولوژی"
        AI_TOOL = "ai_tool", "معرفی ابزار AI"
        OPEN_SOURCE = "open_source", "پروژه Open Source"
        RESEARCH = "research", "مقاله علمی"
        INTERVIEW = "interview", "مصاحبه"
        VIDEO = "video", "ویدئو"
        PODCAST = "podcast", "پادکست"
        AI_DAILY = "ai_daily", "AI Daily"

    class Status(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        PUBLISHED = "published", "منتشر شده"

    title = models.CharField("عنوان", max_length=220)
    slug = models.SlugField("اسلاگ", max_length=240, unique=True, allow_unicode=True, blank=True)
    content_type = models.CharField(
        "نوع محتوا", max_length=20, choices=ContentType.choices, default=ContentType.ARTICLE
    )
    category = models.ForeignKey(
        Category, verbose_name="دسته‌بندی", on_delete=models.PROTECT, related_name="articles"
    )
    tags = models.ManyToManyField(Tag, verbose_name="تگ‌ها", blank=True, related_name="articles")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="نویسنده",
        on_delete=models.SET_NULL,
        null=True,
        related_name="articles",
    )
    cover = models.ImageField("تصویر اصلی", upload_to="covers/%Y/%m/", blank=True)
    excerpt = models.TextField("خلاصه", max_length=500, blank=True)
    body = models.TextField("متن (Markdown)", help_text="از Markdown و بلوک‌های ```code``` پشتیبانی می‌شود.")
    video_url = models.URLField("لینک ویدئو", blank=True)
    audio_url = models.URLField("لینک فایل صوتی (پادکست)", blank=True)
    source_url = models.URLField("منبع", blank=True)

    status = models.CharField("وضعیت", max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField("تاریخ انتشار", default=timezone.now, db_index=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)
    is_featured = models.BooleanField("مهم‌ترین مطلب روز", default=False)
    is_editor_pick = models.BooleanField("منتخب سردبیر", default=False)
    reading_time = models.PositiveSmallIntegerField("زمان مطالعه (دقیقه)", default=1, editable=False)
    views_count = models.PositiveIntegerField("بازدید", default=0, editable=False)

    # AI Daily: "AI Daily #127" with the three standard questions.
    ai_daily_number = models.PositiveIntegerField("شماره AI Daily", null=True, blank=True, unique=True)
    why_important = models.TextField("چرا مهم است؟", blank=True)
    use_cases = models.TextField("چه کاربردی دارد؟", blank=True)
    developer_impact = models.TextField("چه تأثیری روی توسعه‌دهندگان دارد؟", blank=True)

    objects = ArticleQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "مطلب"
        verbose_name_plural = "مطالب"
        indexes = [models.Index(fields=["status", "-published_at"])]

    def __str__(self):
        return self.display_title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        if self.content_type == self.ContentType.AI_DAILY and self.ai_daily_number is None:
            last = Article.objects.aggregate(n=Max("ai_daily_number"))["n"] or 0
            self.ai_daily_number = last + 1
        self.reading_time = estimate_reading_time(
            " ".join([self.body, self.why_important, self.use_cases, self.developer_impact])
        )
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("magazine:article", args=[self.slug])

    @property
    def display_title(self):
        if self.ai_daily_number:
            return f"AI Daily #{self.ai_daily_number} — {self.title}"
        return self.title

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED and self.published_at <= timezone.now()

    @cached_property
    def _rendered(self):
        return render_markdown(self.body)

    @property
    def body_html(self):
        return self._rendered[0]

    @property
    def toc(self):
        return self._rendered[1]

    @property
    def seo_title(self):
        return self.meta_title or self.display_title

    @property
    def seo_description(self):
        return self.meta_description or self.excerpt[:160]

    @property
    def video_embed_url(self):
        """Embeddable URL for YouTube / Aparat links, else ``None``."""
        url = self.video_url
        if not url:
            return None
        if "youtube.com/watch" in url and "v=" in url:
            return "https://www.youtube.com/embed/" + url.split("v=")[1].split("&")[0]
        if "youtu.be/" in url:
            return "https://www.youtube.com/embed/" + url.rsplit("/", 1)[1].split("?")[0]
        if "aparat.com/v/" in url:
            return "https://www.aparat.com/video/video/embed/videohash/" + url.rstrip("/").rsplit("/", 1)[1] + "/vt/frame"
        return None

    def related(self, limit=3):
        qs = Article.objects.published().with_relations().exclude(pk=self.pk)
        tag_ids = list(self.tags.values_list("id", flat=True))
        related = list(
            qs.filter(Q(tags__in=tag_ids) | Q(category_id=self.category_id))
            .annotate(shared=models.Count("tags", filter=Q(tags__in=tag_ids)))
            .order_by("-shared", "-published_at")
            .distinct()[:limit]
        )
        return related
