from django.urls import path

from . import admin_views, views

app_name = "magazine"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("search/suggest/", views.search_suggest, name="search_suggest"),
    path("for-you/", views.for_you, name="for_you"),
    path("admin-tools/preview/", admin_views.preview, name="admin_preview"),
    path("admin-tools/upload/", admin_views.upload_image, name="admin_upload"),
    path("ai-daily/", views.ai_daily_list, name="ai_daily"),
    path("ai-daily/<int:number>/", views.ai_daily_detail, name="ai_daily_detail"),
    path("article/<str:slug>/", views.article_detail, name="article"),
    path("category/<str:slug>/", views.category_detail, name="category"),
    path("tag/<str:slug>/", views.tag_detail, name="tag"),
    path("type/<str:content_type>/", views.content_type_list, name="content_type"),
]
