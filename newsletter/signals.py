from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from interactions.models import Comment
from magazine.models import Article

from . import services


@receiver(post_save, sender=Article)
def article_published(sender, instance, **kwargs):
    if instance.is_published and not instance.notified_at:
        transaction.on_commit(lambda: services.notify_followers(instance))


@receiver(post_save, sender=Comment)
def comment_reply(sender, instance, created, **kwargs):
    if created and instance.parent_id:
        services.notify_reply(instance)
