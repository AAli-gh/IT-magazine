"""Replace the placeholder demo posts with real showcase articles and generated covers.

    python manage.py load_showcase           # add missing showcase articles
    python manage.py load_showcase --update  # also rewrite existing ones (body, excerpt, cover)
"""

import io
import zlib
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from magazine.management.commands.seed_magazine import DEMO_BODY
from magazine.models import Article, Category, Tag
from magazine.showcase import ARTICLES

COVER_SIZE = (1440, 810)
# Gradient start/end colours per category.
PALETTE = {
    "ai": ("#4f46e5", "#9333ea"),
    "programming": ("#0f766e", "#0891b2"),
    "web": ("#2563eb", "#06b6d4"),
    "security": ("#991b1b", "#ea580c"),
    "cloud-devops": ("#0369a1", "#6366f1"),
    "database": ("#15803d", "#0d9488"),
    "computer-science": ("#7c3aed", "#db2777"),
    "hardware": ("#374151", "#0f766e"),
    "gaming": ("#be185d", "#7c3aed"),
    "mobile": ("#16a34a", "#65a30d"),
    "research": ("#1e3a8a", "#0e7490"),
    "tutorials": ("#b45309", "#dc2626"),
    "news-trends": ("#0f172a", "#2563eb"),
}
FONT_CANDIDATES = ("DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


def _font(size):
    for name in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _hex(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def make_cover(label, category_slug):
    """A 16:9 gradient cover with a large Latin label (Pillow can't shape Persian text)."""
    start, end = (_hex(c) for c in PALETTE.get(category_slug, ("#1e293b", "#475569")))
    width, height = COVER_SIZE
    image = Image.new("RGB", COVER_SIZE)
    draw = ImageDraw.Draw(image)
    for x in range(width):
        t = x / (width - 1)
        draw.line([(x, 0), (x, height)], fill=tuple(round(a + (b - a) * t) for a, b in zip(start, end)))

    # Soft decorative circles, positioned from the label so each cover differs.
    seed = zlib.crc32(label.encode())
    overlay = Image.new("RGBA", COVER_SIZE, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for i in range(3):
        r = 180 + (seed >> (i * 5)) % 260
        cx = (seed >> (i * 7)) % width
        cy = (seed >> (i * 3)) % height
        odraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 22))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    size = 190 if len(label) <= 7 else 150 if len(label) <= 10 else 110
    font = _font(size)
    box = draw.textbbox((0, 0), label, font=font)
    x = (width - (box[2] - box[0])) / 2 - box[0]
    y = (height - (box[3] - box[1])) / 2 - box[1]
    draw.text((x + 6, y + 8), label, font=font, fill=(0, 0, 0, 60))
    draw.text((x, y), label, font=font, fill="white")
    small = _font(34)
    draw.text((60, height - 90), "IT MAGAZINE", font=small, fill=(255, 255, 255))

    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=88, optimize=True)
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    help = "Replace placeholder demo posts with real showcase articles (with generated covers)."

    def add_arguments(self, parser):
        parser.add_argument("--update", action="store_true", help="Rewrite showcase articles that already exist.")

    @transaction.atomic
    def handle(self, *args, update=False, **options):
        call_command("seed_magazine", stdout=self.stdout)  # categories, pages, roles
        placeholders = Article.objects.filter(body=DEMO_BODY)
        removed = placeholders.count()
        placeholders.delete()

        User = get_user_model()
        author, _ = User.objects.get_or_create(username="editor", defaults={"is_author": True})
        if not author.has_usable_password():
            author.set_unusable_password()
        author.first_name, author.last_name = "تحریریه", "مجله فناوری"
        author.is_author = True
        author.bio = "تیم تحریریهٔ مجله فناوری؛ مقاله، آموزش و تحلیل روز دنیای IT."
        author.save()

        now = timezone.now()
        created = updated = 0
        # Oldest first, so AI Daily numbers grow with the publish date.
        for index, item in reversed(list(enumerate(ARTICLES))):
            article = Article.objects.filter(title=item["title"]).first()
            if article and not update:
                continue
            is_new = article is None
            article = article or Article(title=item["title"])
            article.category = Category.objects.get(slug=item["category"])
            article.content_type = item["type"]
            article.author = author
            article.excerpt = item["excerpt"]
            article.body = item["body"]
            article.source_url = item.get("source_url", "")
            article.why_important = item.get("why_important", "")
            article.use_cases = item.get("use_cases", "")
            article.developer_impact = item.get("developer_impact", "")
            article.is_featured = item.get("featured", False)
            article.is_editor_pick = item.get("pick", False)
            article.status = Article.Status.PUBLISHED
            if is_new:
                article.published_at = now - timedelta(hours=index * 13 + 1)
            article.cover.save(f"{item['category']}-{index}.jpg", make_cover(item["label"], item["category"]),
                               save=False)
            article.save()
            article.tags.set([Tag.objects.get_or_create(name=name)[0] for name in item["tags"]])
            # Spread view counts so the «popular» box has a stable, varied order.
            Article.objects.filter(pk=article.pk).update(
                views_count=120 + zlib.crc32(item["title"].encode()) % 2400)
            created += is_new
            updated += not is_new

        self.stdout.write(self.style.SUCCESS(
            f"Removed {removed} placeholder posts; {created} showcase articles created, {updated} updated."))
