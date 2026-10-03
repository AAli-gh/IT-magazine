from django.conf import settings
from django.core.exceptions import BadRequest, PermissionDenied
from django.db import connection
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_GET

from .models import Page


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "core/page.html", {"page": page})


@require_GET
@require_GET
def favicon(request):
    """Browsers request /favicon.ico directly; point them at the static icon."""
    return redirect(static("brand/favicon.ico"), permanent=True)


def robots_txt(request):
    sitemap = settings.SITE_URL.rstrip("/") + reverse("django.contrib.sitemaps.views.sitemap")
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /i/",
        "Disallow: /admin-tools/",
        "Disallow: /notifications/",
        "Disallow: /newsletter/",
        f"Sitemap: {sitemap}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def admin_login(request):
    """Send the admin login form to allauth (which handles 2FA), then back to the admin."""
    from urllib.parse import urlencode

    next_url = request.GET.get("next") or reverse("admin:index")
    return redirect(f"{reverse('account_login')}?{urlencode({'next': next_url})}")


def healthz(request):
    """Liveness/readiness probe for Docker and load balancers."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse("ok", content_type="text/plain")


def error_preview(request, code):
    """Lets site admins preview the custom 400/403 pages; everyone else gets a 404."""
    if not request.user.is_superuser:
        raise Http404
    if code == 400:
        raise BadRequest
    if code == 403:
        raise PermissionDenied
    raise Http404
