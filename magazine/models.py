from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, SearchVectorField
from django.core.validators import FileExtensionValidator
from django.db import connection, models
from django.db.models import F, Max, Q, Value
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify

from .fulltext import build_tsquery
from .rendering import estimate_reading_time, render_markdown
from .textutils import expand_query, normalize, strip_code


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
        """Normalized, synonym-aware search: every query term (or one of its synonyms) must match.

        On PostgreSQL this uses the GIN-indexed full-text vector (and annotates ``rank``),
        which scales to large archives; elsewhere it falls back to substring matching.
        """
        groups = expand_query(query)
        if not groups:
            return self
        if connection.vendor == "postgresql":
            tsquery = build_tsquery(groups)
            if tsquery:
                q = SearchQuery(tsquery, search_type="raw", config="simple")
                return self.filter(search_vector=q).annotate(rank=SearchRank(F("search_vector"), q))
        qs = self
        for group in groups:
            condition = Q()
            for term in group:
                condition |= Q(search_text__icontains=term)
            qs = qs.filter(condition)
        return qs


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
        REVIEW = "review", "در انتظار بررسی"
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
        blank=True,
        related_name="articles",
    )
    cover = models.ImageField("تصویر اصلی", upload_to="covers/%Y/%m/", blank=True)
    excerpt = models.TextField("خلاصه", max_length=500, blank=True)
    body = models.TextField("متن (Markdown)", help_text="از Markdown و بلوک‌های ```code``` پشتیبانی می‌شود.")
    cover_variants = models.JSONField("نسخه‌های کوچک کاور", default=dict, blank=True, editable=False)
    video_url = models.URLField("لینک ویدئو", blank=True, help_text="یوتیوب، آپارات یا لینک مستقیم")
    video_file = models.FileField(
        "فایل ویدئو", upload_to="videos/%Y/%m/", blank=True,
        validators=[FileExtensionValidator(["mp4", "webm", "mov"])],
    )
    audio_url = models.URLField("لینک فایل صوتی (پادکست)", blank=True)
    audio_file = models.FileField(
        "فایل صوتی (پادکست)", upload_to="podcasts/%Y/%m/", blank=True,
        validators=[FileExtensionValidator(["mp3", "m4a", "ogg", "wav"])],
    )
    media_duration = models.CharField("مدت ویدئو/پادکست", max_length=20, blank=True, help_text="مثلاً 42:10")
    source_url = models.URLField("منبع", blank=True)

    # Interview
    interviewee_name = models.CharField("نام مصاحبه‌شونده", max_length=120, blank=True)
    interviewee_title = models.CharField("سمت مصاحبه‌شونده", max_length=200, blank=True)
    interviewee_photo = models.ImageField("عکس مصاحبه‌شونده", upload_to="interviews/", blank=True)

    status = models.CharField("وضعیت", max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField("تاریخ انتشار", default=timezone.now, db_index=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)
    is_featured = models.BooleanField("مهم‌ترین مطلب روز", default=False)
    is_editor_pick = models.BooleanField("منتخب سردبیر", default=False)
    reading_time = models.PositiveSmallIntegerField("زمان مطالعه (دقیقه)", default=1, editable=False)
    views_count = models.PositiveIntegerField("بازدید", default=0, editable=False)
    notified_at = models.DateTimeField("اطلاع‌رسانی به دنبال‌کنندگان", null=True, blank=True, editable=False)
    ai_generated = models.BooleanField("تولیدشده با AI", default=False, editable=False)
    search_text = models.TextField(blank=True, editable=False)
    # PostgreSQL full-text vector (title weighted A, everything else D); unused on other databases.
    search_vector = SearchVectorField(null=True, editable=False)

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
        permissions = [
            ("publish_article", "می‌تواند مطلب منتشر یا ویژه کند (سردبیر)"),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Read the raw value so deferred-field querysets don't trigger extra queries.
        cover = self.__dict__.get("cover")
        self._original_cover = getattr(cover, "name", cover) or ""
        self._original_status = self.__dict__.get("status")

    def __str__(self):
        return self.display_title

    def save(self, *args, **kwargs):
        cover_changed = (self.cover.name if self.cover else "") != self._original_cover
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        if self.content_type == self.ContentType.AI_DAILY and self.ai_daily_number is None:
            last = Article.objects.aggregate(n=Max("ai_daily_number"))["n"] or 0
            self.ai_daily_number = last + 1
        self.reading_time = estimate_reading_time(
            " ".join([self.body, self.why_important, self.use_cases, self.developer_impact])
        )
        if cover_changed and not self.cover:
            self.cover_variants = {}
        self.search_text = self.build_search_text()
        if self.pk and self.notified_at is None:
            # Never clear the flag set by the notification service from a stale in-memory copy.
            self.notified_at = Article.objects.filter(pk=self.pk).values_list("notified_at", flat=True).first()
        super().save(*args, **kwargs)
        if self.cover and (cover_changed or not self.cover_variants):
            from .images import build_cover_variants

            self.cover_variants = build_cover_variants(self.cover)
            Article.objects.filter(pk=self.pk).update(cover_variants=self.cover_variants)
        self.update_search_vector()
        self._original_cover = self.cover.name if self.cover else ""
        self._original_status = self.status

    def get_absolute_url(self):
        return reverse("magazine:article", args=[self.slug])

    def build_search_text(self, include_tags=True):
        tags = " ".join(self.tags.values_list("name", flat=True)) if include_tags and self.pk else ""
        category = self.category.name if self.category_id else ""
        parts = [self.title, self.excerpt, category, tags, strip_code(self.body), self.interviewee_name]
        return normalize(" ".join(parts))

    def refresh_search_text(self):
        self.search_text = self.build_search_text()
        Article.objects.filter(pk=self.pk).update(search_text=self.search_text)
        self.update_search_vector()

    def update_search_vector(self):
        if connection.vendor != "postgresql" or not self.pk:
            return
        Article.objects.filter(pk=self.pk).update(search_vector=(
            SearchVector(Value(normalize(self.title)), weight="A", config="simple")
            + SearchVector("search_text", weight="D", config="simple")
        ))

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
        from django.core.cache import cache

        if not self.pk:
            return render_markdown(self.body)
        key = f"article-html:{self.pk}:{self.updated_at.timestamp() if self.updated_at else 0}"
        rendered = cache.get(key)
        if rendered is None:
            rendered = render_markdown(self.body)
            cache.set(key, rendered, 60 * 60 * 24)
        return rendered

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
    def cover_srcset(self):
        return ", ".join(f"{url} {width}w" for width, url in sorted(
            ((int(w), u) for w, u in self.cover_variants.items())))

    @property
    def cover_small(self):
        """Smallest generated variant (for cards), falling back to the original."""
        if self.cover_variants:
            return self.cover_variants[min(self.cover_variants, key=int)]
        return self.cover.url if self.cover else ""

    @property
    def video_src(self):
        return self.video_file.url if self.video_file else ""

    @property
    def audio_src(self):
        if self.audio_file:
            return self.audio_file.url
        return self.audio_url

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
        """Most similar published articles (TF-IDF over text, tags and category)."""
        from .recommender import similar_ids

        ids = similar_ids(self, limit)
        if len(ids) < limit:  # top up with recent articles from the same category
            ids += list(
                Article.objects.published().filter(category_id=self.category_id)
                .exclude(pk__in=[self.pk, *ids]).values_list("pk", flat=True)[: limit - len(ids)]
            )
        articles = Article.objects.published().with_relations().in_bulk(ids)
        return [articles[pk] for pk in ids if pk in articles]


class InterviewQA(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="interview_qas")
    question = models.TextField("پرسش")
    answer = models.TextField("پاسخ")
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "پرسش و پاسخ"
        verbose_name_plural = "پرسش و پاسخ‌های مصاحبه"

    def __str__(self):
        return self.question[:60]


class MediaFile(models.Model):
    """Images uploaded for use inside article bodies."""

    image = models.ImageField("تصویر", upload_to="uploads/%Y/%m/")
    alt = models.CharField("متن جایگزین (alt)", max_length=200, blank=True)
    caption = models.CharField("زیرنویس", max_length=250, blank=True)
    article = models.ForeignKey(
        Article, on_delete=models.SET_NULL, null=True, blank=True, related_name="media_files", verbose_name="مطلب"
    )
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "تصویر"
        verbose_name_plural = "کتابخانه تصاویر"

    def __str__(self):
        return self.alt or self.image.name

    def save(self, *args, **kwargs):
        from .images import optimize_upload

        if self.image and not self.pk:
            optimize_upload(self.image)
        super().save(*args, **kwargs)

    @property
    def markdown(self):
        md = f"![{self.alt}]({self.image.url})"
        if self.caption:
            md += f"\n*{self.caption}*"
        return md


class ArticleDailyView(models.Model):
    """Per-day view counter for the admin dashboard."""

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="daily_views")
    date = models.DateField(default=timezone.localdate, db_index=True)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "بازدید روزانه"
        verbose_name_plural = "بازدیدهای روزانه"
        constraints = [models.UniqueConstraint(fields=["article", "date"], name="unique_daily_view")]


class NewsSource(models.Model):
    """RSS/Atom feeds used as input for automatic AI Daily drafts."""

    name = models.CharField("نام", max_length=100)
    feed_url = models.URLField("آدرس RSS", unique=True)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "منبع خبری AI"
        verbose_name_plural = "منابع خبری AI Daily"

    def __str__(self):
        return self.name
