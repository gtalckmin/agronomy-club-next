from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from firebase_admin import auth

from agronomy_club.models import User
from agronomy_club.services.firestore_member_import import (
    FirestoreMemberImporter,
    ImportSummary,
)


class FakeDocument:
    def __init__(self, uid, data):
        self.id = uid
        self._data = data

    def to_dict(self):
        return self._data


class FakeCollection:
    def __init__(self, documents):
        self.documents = documents

    def stream(self):
        return iter(self.documents)


class FakeFirestore:
    def __init__(self, documents):
        self.documents = documents
        self.requested_collections = []

    def collection(self, name):
        self.requested_collections.append(name)
        return FakeCollection(self.documents)


class FakeAuthUser:
    def __init__(self, email):
        self.email = email


class FakeFirebaseAuth:
    def __init__(self, users):
        self.users = users

    def get_user(self, uid, app=None):
        if uid not in self.users:
            raise auth.UserNotFoundError("Firebase user not found")
        return self.users[uid]


class FirestoreMemberImporterTests(TestCase):
    def setUp(self):
        self.firestore = FakeFirestore([
            FakeDocument(
                "uid-1",
                {
                    "fullName": "Imported Member",
                    "email": "member@example.com",
                    "role": "member",
                    "verified": False,
                },
            ),
        ])
        self.firebase_auth = FakeFirebaseAuth({
            "uid-1": FakeAuthUser("member@example.com"),
        })
        self.importer = FirestoreMemberImporter(
            firestore_client=self.firestore,
            firebase_auth=self.firebase_auth,
        )

    def test_dry_run_reports_a_candidate_without_writing(self):
        summary = self.importer.import_members(apply=False)

        self.assertEqual(
            (summary.scanned, summary.candidates, summary.created),
            (1, 1, 0),
        )
        self.assertEqual(self.firestore.requested_collections, ["users"])
        self.assertFalse(User.objects.exists())

    def test_apply_creates_a_safe_incomplete_profile_once(self):
        summary = self.importer.import_members(apply=True)

        member = User.objects.get(firebase_uid="uid-1")
        self.assertEqual(
            (summary.created, member.grad_yr, member.discipline, member.global_role),
            (1, None, "", "user"),
        )

        second_summary = self.importer.import_members(apply=True)

        self.assertEqual((second_summary.created, second_summary.existing), (0, 1))

    def test_import_skips_a_mismatched_source_email(self):
        self.firestore.documents[0] = FakeDocument(
            "uid-1",
            {
                "fullName": "Imported Member",
                "email": "different@example.com",
                "role": "member",
            },
        )

        summary = self.importer.import_members(apply=True)

        self.assertEqual((summary.candidates, summary.skipped_invalid), (0, 1))
        self.assertFalse(User.objects.exists())

    def test_import_skips_a_member_without_a_firebase_account(self):
        self.firebase_auth.users = {}

        summary = self.importer.import_members(apply=True)

        self.assertEqual((summary.candidates, summary.skipped_invalid), (0, 1))
        self.assertFalse(User.objects.exists())

    def test_import_stops_when_firebase_auth_is_unavailable(self):
        def unavailable(uid, app=None):
            raise RuntimeError("Firebase Authentication is unavailable")

        self.firebase_auth.get_user = unavailable

        with self.assertRaisesRegex(RuntimeError, "unavailable"):
            self.importer.import_members(apply=True)
        self.assertFalse(User.objects.exists())

    def test_import_skips_an_unknown_legacy_role(self):
        self.firestore.documents[0] = FakeDocument(
            "uid-1",
            {
                "fullName": "Imported Member",
                "email": "member@example.com",
                "role": "mystery",
            },
        )

        summary = self.importer.import_members(apply=True)

        self.assertEqual((summary.candidates, summary.skipped_unknown_role), (0, 1))
        self.assertFalse(User.objects.exists())

    def test_import_maps_legacy_admin_and_alumni_roles(self):
        self.firestore.documents = [
            FakeDocument("admin-uid", {"fullName": "Admin", "role": "admin"}),
            FakeDocument("alumni-uid", {"fullName": "Alumni", "role": "alumni"}),
        ]
        self.firebase_auth.users = {
            "admin-uid": FakeAuthUser("admin@example.com"),
            "alumni-uid": FakeAuthUser("alumni@example.com"),
        }

        summary = self.importer.import_members(apply=True)

        self.assertEqual(summary.created, 2)
        self.assertEqual(User.objects.get(firebase_uid="admin-uid").global_role, "admin")
        self.assertEqual(User.objects.get(firebase_uid="alumni-uid").global_role, "alumni")

    def test_import_skips_existing_uid_or_email_without_overwriting(self):
        User.objects.create(
            full_name="Existing Member",
            grad_yr=2028,
            discipline="Soil Science",
            email="member@example.com",
            firebase_uid="existing-uid",
        )

        summary = self.importer.import_members(apply=True)

        self.assertEqual((summary.created, summary.skipped_conflict), (0, 1))
        self.assertEqual(User.objects.get(firebase_uid="existing-uid").full_name, "Existing Member")

    @patch("agronomy_club.management.commands.import_firestore_members.FirestoreMemberImporter")
    def test_command_is_dry_run_without_apply(self, importer_class):
        importer = importer_class.from_settings.return_value
        importer.import_members.return_value = ImportSummary(scanned=1, candidates=1)

        call_command("import_firestore_members")

        importer.import_members.assert_called_once_with(apply=False)
