from django.urls import path

from . import views

app_name = "interactions"

urlpatterns = [
    path("like/<int:pk>/", views.toggle_like, name="like"),
    path("bookmark/<int:pk>/", views.toggle_bookmark, name="bookmark"),
    path("follow/<int:pk>/", views.toggle_follow, name="follow"),
    path("comment/<int:pk>/", views.add_comment, name="comment"),
]
