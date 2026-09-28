"""Automatic AI Daily drafts: collect AI news from RSS feeds and let Claude write the issue.

Requires ``ANTHROPIC_API_KEY`` (or another credential the Anthropic SDK can find).
Generated issues are saved as "in review" unless SiteSettings.ai_daily_auto_publish is on.
"""

import logging
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.html import strip_tags
from pydantic import BaseModel, Field

from core.models import SiteSettings

from .models import Article, Category, NewsSource, Tag

logger = logging.getLogger(__name__)

FEED_TIMEOUT = 15
MAX_ITEMS_PER_FEED = 10
MAX_ITEMS_TOTAL = 30
ATOM = "{http://www.w3.org/2005/Atom}"

SYSTEM_PROMPT = """You are the editor of "AI Daily", a daily column in a Persian-language IT magazine \
read mostly by software developers. Each issue covers exactly one important AI story.

From the news items provided, choose the single story that matters most to developers today \
(new models, tools, APIs, research with practical impact). Skip stories that were already covered \
(listed under "Already covered").

Write the issue in fluent, natural Persian. Keep established technical terms and product names in \
English (e.g. LLM, API, open source model names). Use only facts from the provided item; if a detail \
is not in the source, leave it out rather than guessing. The body is Markdown with 2-4 "##" sections; \
use a fenced code block only if the source includes code or an API example."""


class AIDailyDraft(BaseModel):
    chosen_item: int = Field(description="Index of the chosen news item")
    title: str = Field(description="Persian headline, under 90 characters")
    excerpt: str = Field(description="One or two Persian sentences summarising the story")
    body_markdown: str = Field(description="The article body in Persian Markdown")
    why_important: str = Field(description="چرا مهم است؟ — 2-3 Persian sentences")
    use_cases: str = Field(description="چه کاربردی دارد؟ — 2-3 Persian sentences")
    developer_impact: str = Field(description="چه تأثیری روی توسعه‌دهندگان دارد؟ — 2-3 Persian sentences")
    tags: list[str] = Field(description="2-5 short tags, English or Persian")


class AIDailyError(Exception):
    pass


def _text(element, *names):
    for name in names:
        found = element.find(name)
        if found is not None and (found.text or found.get("href")):
            return (found.text or found.get("href") or "").strip()
    return ""


def fetch_feed(url):
    request = urllib.request.Request(url, headers={"User-Agent": "ITMagazine-AIDaily/1.0"})
    with urllib.request.urlopen(request, timeout=FEED_TIMEOUT) as response:  # noqa: S310 (admin-configured URLs)
        root = ET.fromstring(response.read())
    items = []
    for node in root.iter("item"):  # RSS 2.0
        items.append({"title": _text(node, "title"), "link": _text(node, "link"),
                      "summary": strip_tags(_text(node, "description"))[:800]})
    for node in root.iter(f"{ATOM}entry"):  # Atom
        link = node.find(f"{ATOM}link")
        items.append({"title": _text(node, f"{ATOM}title"),
                      "link": link.get("href", "") if link is not None else "",
                      "summary": strip_tags(_text(node, f"{ATOM}summary", f"{ATOM}content"))[:800]})
    return [i for i in items if i["title"] and i["link"]][:MAX_ITEMS_PER_FEED]


def collect_items():
    used = set(Article.objects.filter(content_type=Article.ContentType.AI_DAILY)
               .exclude(source_url="").values_list("source_url", flat=True))
    items, seen = [], set()
    for source in NewsSource.objects.filter(is_active=True):
        try:
            feed_items = fetch_feed(source.feed_url)
        except Exception:
            logger.exception("Could not read feed %s", source.feed_url)
            continue
        for item in feed_items:
            if item["link"] in used or item["link"] in seen:
                continue
            seen.add(item["link"])
            items.append({**item, "source": source.name})
    return items[:MAX_ITEMS_TOTAL]


def _build_prompt(items):
    recent = Article.objects.filter(
        content_type=Article.ContentType.AI_DAILY, published_at__gte=timezone.now() - timedelta(days=14)
    ).values_list("title", flat=True)
    lines = ["News items:"]
    for i, item in enumerate(items):
        lines.append(f"[{i}] {item['title']} ({item['source']})\n{item['link']}\n{item['summary']}")
    lines.append("\nAlready covered:\n" + ("\n".join(f"- {t}" for t in recent) or "- (none)"))
    return "\n\n".join(lines)


def draft_with_claude(items, client=None):
    import anthropic

    client = client or anthropic.Anthropic()
    response = client.beta.messages.parse(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_prompt(items)}],
        output_format=AIDailyDraft,
        thinking={"type": "adaptive"},
        # On a policy decline, let the API retry on a suitable fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise AIDailyError("Claude از نوشتن این شماره خودداری کرد.")
    draft = response.parsed_output
    if draft is None or not 0 <= draft.chosen_item < len(items):
        raise AIDailyError("پاسخ Claude معتبر نبود؛ دوباره تلاش کنید.")
    return draft


def generate_ai_daily(client=None, author=None, force=False):
    """Create today's AI Daily issue. Returns the new Article."""
    today = timezone.localdate()
    if not force and Article.objects.filter(
        content_type=Article.ContentType.AI_DAILY, published_at__date=today
    ).exists():
        raise AIDailyError("AI Daily امروز قبلاً ساخته شده است (برای ساخت دوباره از --force استفاده کنید).")
    items = collect_items()
    if not items:
        raise AIDailyError("خبر جدیدی پیدا نشد. در بخش «منابع خبری AI Daily» منبع فعال اضافه کنید.")
    draft = draft_with_claude(items, client=client)
    item = items[draft.chosen_item]

    category = Category.objects.filter(slug="ai").first() or Category.objects.first()
    if category is None:
        raise AIDailyError("ابتدا دسته‌بندی‌ها را بسازید (python manage.py seed_magazine).")
    publish = SiteSettings.load().ai_daily_auto_publish
    article = Article.objects.create(
        title=draft.title[:220],
        content_type=Article.ContentType.AI_DAILY,
        category=category,
        author=author,
        excerpt=draft.excerpt[:500],
        body=draft.body_markdown,
        why_important=draft.why_important,
        use_cases=draft.use_cases,
        developer_impact=draft.developer_impact,
        source_url=item["link"],
        status=Article.Status.PUBLISHED if publish else Article.Status.REVIEW,
        ai_generated=True,
    )
    article.tags.set([Tag.objects.get_or_create(name=name.strip()[:60])[0] for name in draft.tags if name.strip()])
    return article
