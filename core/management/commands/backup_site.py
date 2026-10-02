"""Back up the database and uploaded media into one zip file.

    python manage.py backup_site            # writes backups/itmag-YYYYmmdd-HHMM.zip
    python manage.py backup_site --keep 7   # ... and keeps only the 7 newest backups

The zip holds `data.json` (dumpdata, restorable on any database with `loaddata`), a consistent copy
of the SQLite file when SQLite is used, and the `media/` folder. Useful on hosts without the Docker
backup service (e.g. PythonAnywhere): download the zip from the Files tab.
"""

import io
import sqlite3
import tempfile
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

EXCLUDE = ["contenttypes", "auth.permission", "sessions", "admin.logentry"]


class Command(BaseCommand):
    help = "Back up the database and media files into a single zip."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", default=str(Path(settings.BASE_DIR) / "backups"))
        parser.add_argument("--keep", type=int, default=0, help="Keep only this many newest backups (0 = keep all).")

    def handle(self, *args, output_dir, keep, **options):
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / f"itmag-{timezone.localtime():%Y%m%d-%H%M%S}.zip"

        data = io.StringIO()
        call_command("dumpdata", natural_foreign=True, natural_primary=True, exclude=EXCLUDE, indent=1, stdout=data)

        media_root = Path(settings.MEDIA_ROOT)
        media_files = 0
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("data.json", data.getvalue())
            # The raw SQLite copy can't be taken inside an open transaction (e.g. under tests);
            # data.json already holds everything needed to restore.
            if connection.vendor == "sqlite" and not connection.in_atomic_block:
                with tempfile.TemporaryDirectory() as tmp:
                    copy = Path(tmp) / "db.sqlite3"
                    connection.ensure_connection()
                    dest = sqlite3.connect(copy)
                    # SQLite's online backup API: consistent even while the site is running.
                    connection.connection.backup(dest)
                    dest.close()
                    archive.write(copy, "db.sqlite3")
            if media_root.is_dir():
                for path in sorted(media_root.rglob("*")):
                    if path.is_file():
                        archive.write(path, Path("media") / path.relative_to(media_root))
                        media_files += 1

        removed = 0
        if keep > 0:
            for old in sorted(out_dir.glob("itmag-*.zip"), reverse=True)[keep:]:
                old.unlink()
                removed += 1

        size_mb = target.stat().st_size / 1024 / 1024
        self.stdout.write(self.style.SUCCESS(
            f"Backup written to {target} ({size_mb:.1f} MB, {media_files} media files; removed {removed} old)."))
