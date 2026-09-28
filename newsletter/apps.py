from django.apps import AppConfig


class NewsletterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "newsletter"
    verbose_name = "خبرنامه و اعلان‌ها"

    def ready(self):
        from . import signals  # noqa: F401
