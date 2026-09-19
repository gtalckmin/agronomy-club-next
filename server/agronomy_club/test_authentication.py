from copy import deepcopy
from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase
from rest_framework.exceptions import AuthenticationFailed

from agronomy_club.authentication import FirebaseIdentity, verify_firebase_token


class FirebaseTokenVerificationTests(SimpleTestCase):
    def setUp(self):
        project_id = settings.FIREBASE_PROJECT_ID
        self.valid_claims = {
            "uid": "firebase-member",
            "email": "member@example.com",
            "email_verified": True,
            "aud": project_id,
            "iss": f"https://securetoken.google.com/{project_id}",
        }

    def test_rejects_a_missing_or_malformed_bearer_header(self):
        for authorization_header in (None, "", "Basic credentials", "Bearer"):
            with self.subTest(authorization_header=authorization_header):
                with patch("agronomy_club.authentication.auth.verify_id_token") as verify_id_token:
                    with self.assertRaises(AuthenticationFailed):
                        verify_firebase_token(authorization_header)

                verify_id_token.assert_not_called()

    @patch("agronomy_club.authentication._firebase_app", return_value=object())
    @patch("agronomy_club.authentication.auth.verify_id_token")
    def test_returns_identity_from_a_verified_project_token(self, verify_id_token, firebase_app):
        verify_id_token.return_value = self.valid_claims

        identity = verify_firebase_token("Bearer verified-token")

        self.assertEqual(identity, FirebaseIdentity(uid="firebase-member", email="member@example.com"))
        verify_id_token.assert_called_once_with("verified-token", app=firebase_app.return_value)

    @patch("agronomy_club.authentication._firebase_app", return_value=object())
    @patch("agronomy_club.authentication.auth.verify_id_token")
    def test_rejects_unverified_or_wrong_project_claims(self, verify_id_token, _firebase_app):
        invalid_claims = (
            {"email_verified": False},
            {"aud": "another-project"},
            {"iss": "https://securetoken.google.com/another-project"},
            {"email": ""},
            {"uid": ""},
        )

        for override in invalid_claims:
            with self.subTest(override=override):
                claims = deepcopy(self.valid_claims)
                claims.update(override)
                verify_id_token.return_value = claims

                with self.assertRaises(AuthenticationFailed):
                    verify_firebase_token("Bearer invalid-token")

    @patch("agronomy_club.authentication._firebase_app", return_value=object())
    @patch("agronomy_club.authentication.auth.verify_id_token", side_effect=ValueError("bad token"))
    def test_rejects_a_token_that_firebase_cannot_verify(self, _verify_id_token, _firebase_app):
        with self.assertRaises(AuthenticationFailed):
            verify_firebase_token("Bearer invalid-token")
