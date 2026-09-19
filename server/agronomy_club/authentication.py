from dataclasses import dataclass

import firebase_admin
from django.conf import settings
from firebase_admin import auth
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


@dataclass(frozen=True)
class FirebaseIdentity:
    uid: str
    email: str

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


def _firebase_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        return firebase_admin.initialize_app(options={"projectId": settings.FIREBASE_PROJECT_ID})


def verify_firebase_token(authorization_header):
    if not authorization_header:
        raise AuthenticationFailed("Authentication credentials were not provided.")

    scheme, _, id_token = authorization_header.partition(" ")
    if scheme.lower() != "bearer" or not id_token:
        raise AuthenticationFailed("Invalid authentication credentials.")

    try:
        decoded_token = auth.verify_id_token(id_token, app=_firebase_app())
    except Exception as error:
        raise AuthenticationFailed("Invalid authentication credentials.") from error

    project_id = settings.FIREBASE_PROJECT_ID
    uid = decoded_token.get("uid") or decoded_token.get("sub")
    email = decoded_token.get("email")
    expected_issuer = f"https://securetoken.google.com/{project_id}"
    if (
        not isinstance(uid, str)
        or not uid
        or not isinstance(email, str)
        or not email
        or decoded_token.get("email_verified") is not True
        or decoded_token.get("aud") != project_id
        or decoded_token.get("iss") != expected_issuer
    ):
        raise AuthenticationFailed("Invalid authentication credentials.")

    return FirebaseIdentity(uid=uid, email=email)


class FirebaseTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        authorization_header = request.headers.get("Authorization")
        if not authorization_header:
            return None

        identity = verify_firebase_token(authorization_header)
        return identity, identity

    def authenticate_header(self, request):
        return "Bearer"
