from django.core.management.base import BaseCommand

from newsletter.services import dispatch_pending_notifications


class Command(BaseCommand):
    help = "Notify topic followers about articles whose (scheduled) publish time has arrived."

    def handle(self, *args, **options):
        self.stdout.write(f"{dispatch_pending_notifications()} notifications sent.")
