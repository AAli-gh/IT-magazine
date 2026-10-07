from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from core.views import admin_login, favicon, healthz, robots_txt
from magazine.feeds import CategoryFeed, LatestArticlesFeed, PodcastFeed
from magazine.sitemaps import sitemaps

urlpatterns = [
    # Admin sign-in goes through allauth so rate limits and two-factor codes apply.
    path(settings.ADMIN_URL + "login/", admin_login, name="admin_login_redirect"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("accounts.urls")),
    path("i/", include("interactions.urls")),
    path("api/", include("magazine.api.urls")),
    path("rss/", LatestArticlesFeed(), name="rss"),
    path("rss/podcast/", PodcastFeed(), name="podcast_rss"),
    path("rss/<str:slug>/", CategoryFeed(), name="category_rss"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", robots_txt, name="robots"),
    path("favicon.ico", favicon, name="favicon"),
    path("healthz", healthz, name="healthz"),
    path("", include("newsletter.urls")),
    path("", include("core.urls")),
    path("", include("magazine.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
