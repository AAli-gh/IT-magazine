from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from .models import Page


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "core/page.html", {"page": page})


@require_GET
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


def healthz(request):
    """Liveness/readiness probe for Docker and load balancers."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse("ok", content_type="text/plain")
