from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from core.views import robots_txt
from magazine.feeds import CategoryFeed, LatestArticlesFeed
from magazine.sitemaps import sitemaps

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("i/", include("interactions.urls")),
    path("api/", include("magazine.api.urls")),
    path("rss/", LatestArticlesFeed(), name="rss"),
    path("rss/<str:slug>/", CategoryFeed(), name="category_rss"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", robots_txt, name="robots"),
    path("", include("core.urls")),
    path("", include("magazine.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
