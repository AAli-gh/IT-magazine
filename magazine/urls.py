from django.urls import path

from . import views

app_name = "magazine"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("ai-daily/", views.ai_daily_list, name="ai_daily"),
    path("ai-daily/<int:number>/", views.ai_daily_detail, name="ai_daily_detail"),
    path("article/<str:slug>/", views.article_detail, name="article"),
    path("category/<str:slug>/", views.category_detail, name="category"),
    path("tag/<str:slug>/", views.tag_detail, name="tag"),
    path("type/<str:content_type>/", views.content_type_list, name="content_type"),
]
