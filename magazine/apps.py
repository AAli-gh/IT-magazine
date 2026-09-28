from django.apps import AppConfig


class MagazineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "magazine"
    verbose_name = "مجله"

    def ready(self):
        from . import signals  # noqa: F401
