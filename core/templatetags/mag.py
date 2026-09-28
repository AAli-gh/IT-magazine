import jdatetime
from django import template
from django.utils import timezone

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
