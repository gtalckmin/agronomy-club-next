"""Safely import legacy Firebase member profiles from Firestore."""

import json
from dataclasses import asdict

from django.core.management.base import BaseCommand

from agronomy_club.services.firestore_member_import import FirestoreMemberImporter


class Command(BaseCommand):
    help = "Dry-run or import legacy Firestore users into Django member profiles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Create validated member profiles instead of only reporting counts.",
        )

    def handle(self, *args, **options):
        summary = FirestoreMemberImporter.from_settings().import_members(
            apply=options["apply"],
        )
        self.stdout.write(json.dumps(asdict(summary), sort_keys=True))
