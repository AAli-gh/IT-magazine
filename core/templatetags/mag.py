import datetime

import jdatetime
from django import template
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe

from core.models import Banner

register = template.Library()

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@register.filter
def fa_digits(value):
    """Convert Latin digits to Persian digits."""
    return str(value).translate(PERSIAN_DIGITS)


@register.filter
def jdate(value, fmt="%d %B %Y"):
    """Render a datetime as a Jalali (Shamsi) date with Persian digits."""
    if not value:
        return ""
    if not isinstance(value, datetime.datetime):  # plain date
        jd = jdatetime.date.fromgregorian(date=value, locale="fa_IR")
        return jd.strftime(fmt).translate(PERSIAN_DIGITS)
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    jd = jdatetime.datetime.fromgregorian(datetime=value, locale="fa_IR")
    return jd.strftime(fmt).translate(PERSIAN_DIGITS)


@register.inclusion_tag("partials/banner_slot.html")
def banner_slot(position):
    return {"banners": Banner.objects.active(position)[:3]}


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """Rebuild the current query string with some params replaced (for pagination)."""
    params = context["request"].GET.copy()
    for key, value in kwargs.items():
        params[key] = value
    return params.urlencode()


@register.filter
def can_edit_comment(comment, user):
    return comment.can_edit(user)


@register.filter
def can_delete_comment(comment, user):
    return comment.can_delete(user)


# Line icons (24×24, drawn with currentColor) used in the menu and hero.
ICONS = {
    "home": '<path d="m3 10 9-7 9 7v10a2 2 0 0 1-2 2h-4v-7h-6v7H5a2 2 0 0 1-2-2z"/>',
    "news": '<path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9'
            'c0-1.1.9-2 2-2h2"/><path d="M18 14h-8M15 18h-5M10 6h8v4h-8z"/>',
    "article": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8"/>',
    "tutorial": '<path d="m2 10 10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5M22 10v6"/>',
    "ai_tool": '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/>'
               '<path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>',
    "sparkle": '<path d="M12 3l1.9 5.6 5.6 1.9-5.6 1.9L12 18l-1.9-5.6-5.6-1.9 5.6-1.9z"/><path d="M19 15v4M17 17h4"/>',
    "research": '<path d="M10 2v7.5L4.7 20.5A1 1 0 0 0 5.6 22h12.8a1 1 0 0 0 .9-1.5L14 9.5V2M8.5 2h7M7 16h10"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/>'
            '<rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "chevron-left": '<path d="m15 18-6-6 6-6"/>',
    "chevron-right": '<path d="m9 18 6-6-6-6"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
}


@register.simple_tag
def icon(name, size="h-5 w-5"):
    """An inline SVG line icon; decorative, so hidden from screen readers."""
    return mark_safe(
        f'<svg class="{escape(size)} shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'
    )
