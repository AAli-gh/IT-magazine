from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from core.cache import bump_content_version
from core.models import Banner, Page, SiteSettings

from .models import Article, Category, Tag


@receiver(m2m_changed, sender=Article.tags.through)
def tags_changed(sender, instance, action, **kwargs):
    if action in ("post_add", "post_remove", "post_clear") and isinstance(instance, Article):
        instance.refresh_search_text()
        bump_content_version()


for model in (Article, Category, Tag, Page, Banner, SiteSettings):
    post_save.connect(bump_content_version, sender=model, dispatch_uid=f"bump_save_{model.__name__}")
    post_delete.connect(bump_content_version, sender=model, dispatch_uid=f"bump_delete_{model.__name__}")
