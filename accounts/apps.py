from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "حساب‌های کاربری"

    def ready(self):
        from .roles import ensure_roles

        post_migrate.connect(ensure_roles, dispatch_uid="accounts_ensure_roles")
