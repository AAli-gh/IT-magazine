"""A tiny scheduler so the site needs no cron or Celery.

Runs forever (use it as its own process/container):
- every minute: notify followers of newly-published scheduled articles
- daily at AI_DAILY_GENERATE_AT (default 08:00 Tehran): draft AI Daily with Claude (if API key is set)
- daily at AI_DAILY_SEND_AT (default 09:00): email the latest published AI Daily
- Fridays at WEEKLY_DIGEST_AT (default 10:00): email the weekly digest
Each job is idempotent, so restarts or overlaps don't send duplicates.
"""

import logging
import os
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from newsletter import services

logger = logging.getLogger(__name__)


def _hhmm(name, default):
    return os.environ.get(name, default)


class Command(BaseCommand):
    help = "Run periodic jobs (notifications, AI Daily, newsletters) in a loop."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run the due jobs once and exit")

    def handle(self, *args, once=False, **options):
        done = set()
        while True:
            now = timezone.localtime()
            today = now.date().isoformat()
            hhmm = now.strftime("%H:%M")
            self._run("notifications", services.dispatch_pending_notifications)
            if os.environ.get("ANTHROPIC_API_KEY") and hhmm >= _hhmm("AI_DAILY_GENERATE_AT", "08:00") \
                    and ("generate", today) not in done:
                done.add(("generate", today))
                self._run("generate_ai_daily", lambda: call_command("generate_ai_daily"))
            if hhmm >= _hhmm("AI_DAILY_SEND_AT", "09:00") and ("ai_daily", today) not in done:
                done.add(("ai_daily", today))
                self._run("send_ai_daily", services.send_ai_daily)
            if now.weekday() == 4 and hhmm >= _hhmm("WEEKLY_DIGEST_AT", "10:00") and ("weekly", today) not in done:
                done.add(("weekly", today))
                self._run("send_weekly", services.send_weekly_digest)
            if once:
                return
            time.sleep(60)

    def _run(self, name, job):
        try:
            result = job()
            if result:
                logger.info("%s: %s", name, result)
        except Exception:
            logger.exception("Scheduled job %s failed", name)
