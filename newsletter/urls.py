from django.urls import path

from . import views

app_name = "newsletter"

urlpatterns = [
    path("newsletter/subscribe/", views.subscribe, name="subscribe"),
    path("newsletter/confirm/<uuid:token>/", views.confirm, name="confirm"),
    path("newsletter/unsubscribe/<uuid:token>/", views.unsubscribe, name="unsubscribe"),
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/<int:pk>/", views.open_notification, name="open_notification"),
]
