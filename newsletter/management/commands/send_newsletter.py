from django.core.management.base import BaseCommand

from newsletter import services


class Command(BaseCommand):
    help = "Send the latest AI Daily and/or the weekly digest (each issue is sent only once)."

    def add_arguments(self, parser):
        parser.add_argument("kind", choices=["ai_daily", "weekly"])

    def handle(self, *args, kind, **options):
        sent = services.send_ai_daily() if kind == "ai_daily" else services.send_weekly_digest()
        if sent is None:
            self.stdout.write("Nothing to send (already sent or no content).")
        else:
            self.stdout.write(self.style.SUCCESS(f"Sent to {sent} subscribers."))
