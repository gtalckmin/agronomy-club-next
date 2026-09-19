"""Import legacy Firestore members without exposing member data in logs."""

from dataclasses import dataclass

from django.conf import settings
from django.db import IntegrityError, transaction
from firebase_admin import auth
from google.cloud import firestore

from agronomy_club.authentication import _firebase_app
from agronomy_club.models import User


@dataclass
class ImportSummary:
    scanned: int = 0
    candidates: int = 0
    created: int = 0
    existing: int = 0
    skipped_invalid: int = 0
    skipped_conflict: int = 0
    skipped_unknown_role: int = 0


class FirestoreMemberImporter:
    """Conservatively create missing Django profiles from legacy members."""

    ROLE_MAP = {
        "member": "user",
        "curator": "user",
        "chapter_lead": "user",
        "admin": "admin",
        "alumni": "alumni",
    }

    def __init__(self, firestore_client, firebase_auth, firebase_app=None):
        self.firestore_client = firestore_client
        self.firebase_auth = firebase_auth
        self.firebase_app = firebase_app

    @classmethod
    def from_settings(cls):
        return cls(
            firestore_client=firestore.Client(project=settings.FIREBASE_PROJECT_ID),
            firebase_auth=auth,
            firebase_app=_firebase_app(),
        )

    def import_members(self, apply: bool) -> ImportSummary:
        summary = ImportSummary()

        for document in self.firestore_client.collection("users").stream():
            summary.scanned += 1
            record = document.to_dict()
            uid = self._text(document.id)
            if not isinstance(record, dict) or not uid:
                summary.skipped_invalid += 1
                continue

            full_name = self._text(record.get("fullName"))
            global_role = self._legacy_role(record.get("role"))
            firebase_user = self._firebase_user(uid)
            email = self._email(getattr(firebase_user, "email", None))
            source_email = record.get("email")

            if not full_name or not firebase_user or not email:
                summary.skipped_invalid += 1
                continue
            if source_email is not None and self._email(source_email) != email:
                summary.skipped_invalid += 1
                continue
            if global_role is None:
                summary.skipped_unknown_role += 1
                continue

            existing_uid = User.objects.filter(firebase_uid=uid).first()
            if existing_uid:
                if self._email(existing_uid.email) == email:
                    summary.existing += 1
                else:
                    summary.skipped_conflict += 1
                continue
            if User.objects.filter(email__iexact=email).exists():
                summary.skipped_conflict += 1
                continue

            summary.candidates += 1
            if not apply:
                continue

            try:
                with transaction.atomic():
                    if (
                        User.objects.filter(firebase_uid=uid).exists()
                        or User.objects.filter(email__iexact=email).exists()
                    ):
                        summary.candidates -= 1
                        summary.skipped_conflict += 1
                        continue
                    User.objects.create(
                        full_name=full_name,
                        grad_yr=None,
                        discipline="",
                        email=email,
                        firebase_uid=uid,
                        global_role=global_role,
                    )
            except IntegrityError:
                summary.candidates -= 1
                summary.skipped_conflict += 1
            else:
                summary.created += 1

        return summary

    def _firebase_user(self, uid):
        try:
            return self.firebase_auth.get_user(uid, app=self.firebase_app)
        except auth.UserNotFoundError:
            return None

    @classmethod
    def _legacy_role(cls, value):
        if not isinstance(value, str):
            return None
        return cls.ROLE_MAP.get(value.strip().lower())

    @staticmethod
    def _text(value):
        if not isinstance(value, str):
            return None
        value = value.strip()
        return value or None

    @classmethod
    def _email(cls, value):
        email = cls._text(value)
        return email.casefold() if email else None
