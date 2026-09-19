# Firebase authentication and Django member profiles

## Purpose

Enable members to create and use Agronomy Club accounts without adding password storage to Django. Firebase Authentication remains the identity provider; the Django API and Cloud SQL remain the source of truth for member profiles, roles, and chapter memberships.

## Scope

The first release supports email-and-password registration, email verification, sign-in, sign-out, password reset, and a profile-completion step for an authenticated person who does not yet have a Django profile. It does not migrate legacy Firestore records, introduce Firebase Dynamic Links, or make Firestore a second member database.

## Architecture

```text
Browser
  │ Firebase email/password SDK
  ▼
Firebase Authentication ── Firebase ID token ──► Django API
                                                │ verifies token
                                                ▼
                                         Cloud SQL member profile
                                                │
                                                ▼
                                           Django Admin
```

The Next.js client receives a Firebase user only after Firebase Authentication accepts the credentials. It sends the resulting ID token in an `Authorization: Bearer <token>` header to the Django API. Django verifies the token for the `agronomy-club` Firebase project and maps the token subject to an immutable `firebase_uid` field on `agronomy_club.User`.

Firebase web configuration values are public application identifiers. They are supplied through App Hosting build and runtime configuration, not committed as credentials. The Cloud Run service uses Application Default Credentials and its Firebase project ID to verify tokens. No Firebase service-account file is committed or copied from the legacy repository.

## Profile contract

`User` gains a nullable, unique `firebase_uid`. A member profile contains the existing fields:

- `full_name`
- `email`
- `grad_yr`
- `discipline`
- `global_role`

The public profile endpoint accepts only the editable profile fields. It derives the Firebase UID and email from the verified token. The caller cannot select `global_role`, another UID, or another email. A newly created profile always has role `user`.

Existing Firebase-authenticated people without a Django profile are directed to profile completion. Existing Django profiles without a linked Firebase UID are not linked automatically by email; staff perform that reconciliation through an explicitly reviewed migration or administration step.

## API contract

The API adds an authenticated member-profile resource:

- `GET /api/member-profile/` returns the caller's profile or `404` when profile completion is required.
- `POST /api/member-profile/` creates the caller's profile exactly once from Firebase-verified identity plus validated profile data.
- `PATCH /api/member-profile/` updates only the caller's permitted profile fields.

Missing, malformed, expired, or wrong-project bearer tokens receive `401`. A UID that conflicts with an existing profile receives `409`. Django REST Framework serializers perform request validation. Role and membership administration remain in Django Admin.

## Client flow

1. Registration validates matching passwords and required profile fields, creates the Firebase email/password identity, and sends a Firebase web email-verification action.
2. The site creates no Django profile until the person has verified their email address.
3. After verification, sign-in authenticates with Firebase, checks the profile endpoint, then either opens the member profile or requests the missing profile details.
4. Profile completion sends the verified Firebase ID token and required profile data to Django.
5. Password reset uses Firebase's web email action flow, not mobile email-link authentication or Firebase Dynamic Links.

## Security and operations

- Email/password is the only enabled client flow in this release; there is no Cordova or mobile Dynamic Links flow.
- Add the Firebase App Hosting staging host to Firebase Authentication authorised domains before testing browser authentication.
- Browser requests use the existing Django API client; the bearer token is held in Firebase's supported client persistence rather than a custom password store.
- Server verification constrains the Firebase project ID and rejects tokens without verified email addresses.
- The Firebase Auth and Cloud Run deployment configurations identify the staging project and domain explicitly.
- Firestore rules and existing Firestore records are not changed by this release.

## Testing and acceptance criteria

Backend tests cover token rejection, profile creation from verified identity, default-role enforcement, duplicate-profile handling, and own-profile updates. Client tests cover form validation and authenticated API request construction where the repository's test tooling supports them. The release also runs format, lint, TypeScript, Django tests, database migration checks, and a staged browser smoke test using a disposable Firebase account.

Acceptance requires a person to create an email/password account at the staging site, verify their email, receive a Django member profile with role `user`, sign out and sign back in, reset their password, and appear in Django Admin without exposing another member's profile or role controls.
