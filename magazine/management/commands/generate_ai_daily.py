from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from magazine.ai_daily import AIDailyError, generate_ai_daily


class Command(BaseCommand):
    help = "Draft today's AI Daily from the configured news sources using Claude."

    def add_arguments(self, parser):
        parser.add_argument("--author", help="Username to set as the issue's author")
        parser.add_argument("--force", action="store_true", help="Create even if today's issue exists")

    def handle(self, *args, author=None, force=False, **options):
        user = None
        if author:
            user = get_user_model().objects.filter(username=author).first()
            if user is None:
                raise CommandError(f"User {author!r} not found")
        try:
            article = generate_ai_daily(author=user, force=force)
        except AIDailyError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(
            f"Created {article.display_title} ({article.get_status_display()})"))
