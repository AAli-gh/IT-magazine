from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from interactions.models import Comment
from magazine.models import Article

from . import services


@receiver(post_save, sender=Article)
def article_saved(sender, instance, created, **kwargs):
    if instance.is_published and not instance.notified_at:
        transaction.on_commit(lambda: services.notify_followers(instance))
    # Notify editors when an article enters the review queue (not on every later save).
    entered_review = instance.status == Article.Status.REVIEW and (
        created or instance._original_status != Article.Status.REVIEW
    )
    if entered_review:
        transaction.on_commit(lambda: services.notify_review_requested(instance))


@receiver(post_save, sender=Comment)
def comment_saved(sender, instance, created, **kwargs):
    if created and instance.parent_id:
        services.notify_reply(instance)
    # A comment just became held for moderation (new, or edited into a held state).
    newly_held = not instance.is_approved and not instance.is_deleted and (
        created or instance._original_approved
    )
    if newly_held:
        transaction.on_commit(lambda: services.notify_comment_held(instance))
