import json
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

# Derived data that is rebuilt locally (the search index schema differs between environments).
SKIPPED_MODELS = {"wagtailsearch.indexentry", "admin.logentry"}


class Command(BaseCommand):
    help = (
        "Replace the local database with a `dumpdata` export from another environment. "
        "All existing local data is deleted (a copy of a SQLite database is kept first)."
    )

    def add_arguments(self, parser):
        parser.add_argument("fixture", type=Path, help="Path to the dumpdata JSON file.")
        parser.add_argument("--no-input", action="store_true", help="Do not ask for confirmation.")

    def handle(self, *args, fixture, no_input, **options):
        if not fixture.is_file():
            raise CommandError(f"{fixture} does not exist.")

        if not no_input and input("This deletes ALL local data. Type 'yes' to continue: ") != "yes":
            raise CommandError("Cancelled.")

        objects = json.loads(fixture.read_text())
        content_types = [o for o in objects if o["model"] == "contenttypes.contenttype"]
        rest = [o for o in objects if o["model"] != "contenttypes.contenttype" and o["model"] not in SKIPPED_MODELS]

        self.backup_sqlite()

        call_command("migrate", verbosity=0)
        call_command("flush", interactive=False, verbosity=0)
        # Migrating and flushing recreate content types with local ids; the dump's ids must be used instead.
        ContentType.objects.all().delete()

        with tempfile.TemporaryDirectory() as tmp:
            # Content types are loaded on their own first. In one file, other saves create content types
            # before the dump's own rows are reached, which fails on the unique constraint.
            for name, data in (("content_types", content_types), ("data", rest)):
                path = Path(tmp) / f"{name}.json"
                path.write_text(json.dumps(data))
                call_command("loaddata", str(path), ignorenonexistent=True, verbosity=0)
                self.stdout.write(f"Loaded {len(data)} {name.replace('_', ' ')}.")

        call_command("update_index", verbosity=0)
        self.stdout.write(self.style.SUCCESS("Done."))

    def backup_sqlite(self):
        db = settings.DATABASES["default"]
        if "sqlite" not in db["ENGINE"]:
            return
        source = Path(db["NAME"])
        if source.is_file():
            backup = source.with_name(f"{source.name}.{datetime.now(UTC):%Y%m%d-%H%M%S}.bak")
            shutil.copy2(source, backup)
            self.stdout.write(f"Backed up {source.name} to {backup.name}.")
