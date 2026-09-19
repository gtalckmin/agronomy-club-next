"""Safely import legacy Firebase member profiles from Firestore."""

import json
from dataclasses import asdict

from django.core.management.base import BaseCommand, CommandError

from agronomy_club.services.firestore_member_import import FirestoreMemberImporter


class Command(BaseCommand):
    help = "Dry-run or import legacy Firestore users into Django member profiles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Create validated member profiles instead of only reporting counts.",
        )
        parser.add_argument(
            "--expect-clean-dry-run",
            type=int,
            metavar="COUNT",
            help=(
                "Fail unless dry-run summary contains COUNT clean candidates "
                "and no existing, created, or skipped records."
            ),
        )

    def handle(self, *args, **options):
        if options["apply"] and options["expect_clean_dry_run"] is not None:
            raise CommandError("--expect-clean-dry-run cannot be used with --apply.")

        summary = FirestoreMemberImporter.from_settings().import_members(
            apply=options["apply"],
        )
        expected = options["expect_clean_dry_run"]
        if expected is not None and not self._is_clean_dry_run(summary, expected):
            raise CommandError(
                "Dry-run aggregate counts did not match expected clean import."
            )
        self.stdout.write(json.dumps(asdict(summary), sort_keys=True))

    @staticmethod
    def _is_clean_dry_run(summary, expected):
        return (
            summary.scanned == expected
            and summary.candidates == expected
            and summary.created == 0
            and summary.existing == 0
            and summary.skipped_invalid == 0
            and summary.skipped_conflict == 0
            and summary.skipped_unknown_role == 0
        )
