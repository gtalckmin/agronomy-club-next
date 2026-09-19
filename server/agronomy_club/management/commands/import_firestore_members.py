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
        parser.add_argument(
            "--expect-created",
            type=int,
            metavar="COUNT",
            help=(
                "Fail unless an apply run creates COUNT records with no existing "
                "or skipped records."
            ),
        )
        parser.add_argument(
            "--expect-existing",
            type=int,
            metavar="COUNT",
            help=(
                "Fail unless a dry run finds exactly COUNT existing records with "
                "no candidates, created, or skipped records."
            ),
        )

    def handle(self, *args, **options):
        expected_clean = options["expect_clean_dry_run"]
        expected_created = options["expect_created"]
        expected_existing = options["expect_existing"]

        if options["apply"] and expected_clean is not None:
            raise CommandError(
                "--expect-clean-dry-run cannot be used with --apply."
            )
        if not options["apply"] and expected_created is not None:
            raise CommandError("--expect-created requires --apply.")
        if options["apply"] and expected_existing is not None:
            raise CommandError("--expect-existing cannot be used with --apply.")
        expectations = (expected_clean, expected_created, expected_existing)
        if sum(expected is not None for expected in expectations) > 1:
            raise CommandError("Use only one expected import outcome at a time.")

        summary = FirestoreMemberImporter.from_settings().import_members(
            apply=options["apply"],
        )
        if expected_clean is not None and not self._is_clean_dry_run(
            summary,
            expected_clean,
        ):
            raise CommandError(
                "Dry-run aggregate counts did not match expected clean import."
            )
        if expected_created is not None and not self._is_clean_apply(
            summary,
            expected_created,
        ):
            raise CommandError(
                "Apply aggregate counts did not match expected created import."
            )
        if expected_existing is not None and not self._is_existing_reconciliation(
            summary,
            expected_existing,
        ):
            raise CommandError(
                "Reconciliation aggregate counts did not match expected "
                "existing import."
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

    @staticmethod
    def _is_clean_apply(summary, expected):
        return (
            summary.scanned == expected
            and summary.candidates == expected
            and summary.created == expected
            and summary.existing == 0
            and summary.skipped_invalid == 0
            and summary.skipped_conflict == 0
            and summary.skipped_unknown_role == 0
        )

    @staticmethod
    def _is_existing_reconciliation(summary, expected):
        return (
            summary.scanned == expected
            and summary.candidates == 0
            and summary.created == 0
            and summary.existing == expected
            and summary.skipped_invalid == 0
            and summary.skipped_conflict == 0
            and summary.skipped_unknown_role == 0
        )
