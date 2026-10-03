from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("page/<str:slug>/", views.page_detail, name="page"),
    path("errors/403/", views.forbidden_preview, name="forbidden_preview"),
]
