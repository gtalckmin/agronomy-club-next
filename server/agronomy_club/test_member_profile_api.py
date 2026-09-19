from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIClient

from agronomy_club.authentication import FirebaseIdentity
from agronomy_club.models import User


class MemberProfileAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.authentication = patch(
            "agronomy_club.authentication.verify_firebase_token",
            return_value=FirebaseIdentity(uid="firebase-member", email="member@example.com"),
        )
        self.mock_authentication = self.authentication.start()
        self.addCleanup(self.authentication.stop)

    def request(self, method, data=None):
        return getattr(self.client, method)(
            "/api/member-profile/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION="Bearer verified-token",
        )

    def test_get_requires_bearer_token(self):
        response = self.client.get("/api/member-profile/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_returns_not_found_when_profile_is_missing(self):
        response = self.request("get")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_uses_verified_email_and_default_role(self):
        response = self.request(
            "post",
            {
                "full_name": "Member Example",
                "grad_yr": 2029,
                "discipline": "Agronomy",
                "email": "attacker@example.com",
                "global_role": "admin",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        member = User.objects.get(firebase_uid="firebase-member")
        self.assertEqual(member.email, "member@example.com")
        self.assertEqual(member.global_role, "user")

    def test_create_rejects_existing_firebase_profile(self):
        User.objects.create(
            full_name="Existing Member",
            grad_yr=2028,
            discipline="Soil Science",
            email="member@example.com",
            firebase_uid="firebase-member",
        )

        response = self.request(
            "post",
            {"full_name": "Member Example", "grad_yr": 2029, "discipline": "Agronomy"},
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_patch_only_updates_the_callers_editable_profile_fields(self):
        member = User.objects.create(
            full_name="Existing Member",
            grad_yr=2028,
            discipline="Soil Science",
            email="member@example.com",
            firebase_uid="firebase-member",
            global_role="user",
        )

        response = self.request(
            "patch",
            {
                "discipline": "Plant Science",
                "email": "attacker@example.com",
                "global_role": "admin",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        member.refresh_from_db()
        self.assertEqual(member.discipline, "Plant Science")
        self.assertEqual(member.email, "member@example.com")
        self.assertEqual(member.global_role, "user")

    def test_invalid_token_returns_401(self):
        self.mock_authentication.side_effect = AuthenticationFailed("Invalid credentials.")

        response = self.request("get")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
