# Firebase Authentication and Django Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let members register, sign in, reset passwords, and maintain Firebase-authenticated profiles stored and administered through Django and Cloud SQL.

**Architecture:** Firebase Authentication manages email/password credentials. The Next.js client obtains Firebase ID tokens and sends them through the existing Axios API client. Django verifies each token for `agronomy-club`, maps its UID to `User.firebase_uid`, and owns profile fields, roles, and chapter memberships in PostgreSQL.

**Tech Stack:** Next.js 16, React 19, Firebase Web SDK, Django 5, Django REST Framework, Firebase Admin Python SDK, PostgreSQL, Firebase App Hosting, Cloud Run.

**Spec:** `docs/superpowers/specs/2026-09-19-firebase-auth-django-profile-design.md`

## Global Constraints

- Use Firebase email/password only; do not use Firebase Dynamic Links, mobile email-link authentication, or Cordova OAuth.
- Do not create, modify, or depend on Firestore member records.
- Never commit Firebase credentials, service-account keys, access tokens, or local environment files.
- Verify Firebase ID tokens for `agronomy-club` before a Django member profile is read or changed.
- Client input must never choose a member role, Firebase UID, or email address.
- The staging App Hosting domain must be authorised in Firebase Auth before browser testing.
- Existing Firebase users without a Django profile complete their profile after successful sign-in.
- Create no Django profile until Firebase reports the member email as verified.

---

### Task 1: Link the Django profile to a Firebase identity

**Files:**
- Modify: `server/agronomy_club/models.py`
- Create: `server/agronomy_club/migrations/0018_user_firebase_uid.py`
- Modify: `server/agronomy_club/admin.py`
- Modify: `server/agronomy_club/tests.py`

**Interfaces:**
- Produces: `User.firebase_uid: str | None`, nullable and unique.
- Produces: a staff-visible, non-editable Firebase UID in Django Admin.

- [ ] **Step 1: Write the failing model test.**

```python
def test_user_can_store_unique_firebase_uid(self):
    User.objects.create(
        full_name="Ada Lovelace", grad_yr=2030, discipline="Agronomy",
        email="ada@example.com", firebase_uid="firebase-ada",
    )
    with self.assertRaises(IntegrityError):
        with transaction.atomic():
            User.objects.create(
                full_name="Grace Hopper", grad_yr=2031, discipline="Soil Science",
                email="grace@example.com", firebase_uid="firebase-ada",
            )
```

- [ ] **Step 2: Run the test and confirm it fails because `firebase_uid` is absent.**

```bash
PYTHONPATH=server python3 -m unittest server.agronomy_club.tests.UserModelSmokeTests.test_user_can_store_unique_firebase_uid
```

- [ ] **Step 3: Add `firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True, editable=False)`, make a new migration, and expose it as read-only in Django Admin.**

- [ ] **Step 4: Re-run the focused and complete member-model tests.**

```bash
PYTHONPATH=server python3 -m unittest server.agronomy_club.tests.UserModelSmokeTests
```

- [ ] **Step 5: Commit the model change.**

```bash
git add server/agronomy_club
git commit -m "feat: link member profiles to Firebase identities"
```

### Task 2: Verify Firebase tokens and offer a member-profile API

**Files:**
- Create: `server/agronomy_club/authentication.py`
- Modify: `server/api/settings.py`
- Modify: `server/pyproject.toml`
- Modify: `server/agronomy_club/serializers.py`
- Modify: `server/agronomy_club/views.py`
- Modify: `server/agronomy_club/urls.py`
- Create: `server/agronomy_club/test_member_profile_api.py`
- Modify: `server/.env.example`

**Interfaces:**
- Produces: `verify_firebase_token(authorization_header: str) -> FirebaseIdentity`.
- Produces: `GET`, `POST`, and `PATCH /api/member-profile/`.
- Consumes: `Authorization: Bearer <Firebase ID token>` and `FIREBASE_PROJECT_ID=agronomy-club`.

- [ ] **Step 1: Write the failing API test for creation from verified identity.**

```python
def test_create_profile_uses_verified_identity_and_default_role(self):
    self.mock_identity.return_value = FirebaseIdentity(uid="uid-123", email="member@example.com")
    response = self.client.post(
        "/api/member-profile/",
        {"full_name": "Member", "grad_yr": 2029, "discipline": "Agronomy"},
        format="json",
        HTTP_AUTHORIZATION="Bearer verified-token",
    )
    self.assertEqual(response.status_code, 201)
    self.assertEqual(User.objects.get().email, "member@example.com")
    self.assertEqual(User.objects.get().global_role, "user")
```

- [ ] **Step 2: Run the API test and confirm it fails because no endpoint exists.**

```bash
PYTHONPATH=server python3 -m unittest server.agronomy_club.test_member_profile_api
```

- [ ] **Step 3: Add a Firebase Admin verifier that parses Bearer tokens, validates the Firebase project and verified email, then raises DRF `AuthenticationFailed` for malformed, expired, or invalid tokens. Add a serializer that derives UID/email from the verifier and never accepts role, UID, or email fields.**

- [ ] **Step 4: Implement the member-profile view: return `404` for an authenticated member without a profile, create once with role `user`, and permit only the caller’s editable fields on `PATCH`. Return `409` for an unresolvable UID conflict.**

- [ ] **Step 5: Run the API tests and Django checks.**

```bash
PYTHONPATH=server python3 -m unittest server.agronomy_club.test_member_profile_api
PYTHONPATH=server python3 server/manage.py check
```

- [ ] **Step 6: Commit the authenticated API.**

```bash
git add server
git commit -m "feat: add Firebase-authenticated member profile API"
```

### Task 3: Implement the Next.js account flow

**Files:**
- Create: `client/src/lib/firebase.ts`
- Create: `client/src/lib/member-profile.ts`
- Create: `client/src/lib/registration-validation.ts`
- Create: `client/src/lib/registration-validation.test.ts`
- Create: `client/src/components/auth/auth-form.tsx`
- Create: `client/src/app/member/page.tsx`
- Create: `client/src/app/reset-password/page.tsx`
- Modify: `client/src/app/sign-up/page.tsx`
- Modify: `client/src/app/sign-in/page.tsx`
- Modify: `client/src/lib/api.ts`
- Modify: `client/package.json`
- Modify: `client/.env.example`
- Modify: `client/apphosting.yaml`

**Interfaces:**
- Produces: Firebase singleton configuration, `registerMember`, `signInMember`, `sendPasswordReset`, and authenticated profile calls.
- Consumes: public `NEXT_PUBLIC_FIREBASE_*` App Hosting configuration and Firebase ID tokens.
- Produces: `/member`, which renders profile data or a completion form after an authenticated `404`.

- [ ] **Step 1: Write the failing password-confirmation test.**

```ts
test("registration rejects different passwords", () => {
  expect(validateRegistration({ password: "password-123", confirmPassword: "other-password" }))
    .toEqual({ confirmPassword: "Passwords do not match." });
});
```

- [ ] **Step 2: Run the client test and confirm it fails because the validation module does not exist.**

```bash
npm --prefix client test -- registration-validation
```

- [ ] **Step 3: Add the Firebase Web SDK and a single client-only Firebase app/auth instance. Register with `createUserWithEmailAndPassword`, obtain `getIdToken()`, and call the member-profile API with the bearer token. Use a generic failure response for Firebase credential errors.**

- [ ] **Step 4: Replace presentation-only forms with client forms that show pending, field-validation, and server-error states. Route successful sign-up/sign-in to `/member`; route password resets through Firebase’s supported web action. Correct the existing sign-in link to `/sign-up`.**

- [ ] **Step 5: Run client tests, formatting, lint, TypeScript, and production build.**

```bash
npm --prefix client test
npm --prefix client run format:check
npm --prefix client run lint
npm --prefix client run typecheck
npm --prefix client run build
```

- [ ] **Step 6: Commit the client authentication flow.**

```bash
git add client
git commit -m "feat: add Firebase member registration and sign-in"
```

### Task 4: Configure staging and smoke-test the release

**Files:**
- Modify: `docs/DEPLOYMENT-STRATEGY.md`
- Modify: `docs/PROJECT.md`

**Interfaces:**
- Consumes: Firebase project `agronomy-club`, App Hosting backend `agronomy-club-next-staging`, and Cloud Run API `agronomy-club-api-staging`.
- Produces: a deployed staging account flow with the staging host authorised for Firebase Auth and Cloud Run token verification configured.

- [ ] **Step 1: Read existing Firebase web-app metadata without reading user records.**

```bash
firebase apps:list WEB --project agronomy-club
```

- [ ] **Step 2: Authorise the App Hosting staging domain in Firebase Authentication and place only public Firebase Web SDK identifiers in App Hosting configuration. Set `FIREBASE_PROJECT_ID=agronomy-club` on Cloud Run.**

- [ ] **Step 3: Build and deploy the API image, execute the explicit migration job, then deploy App Hosting.**

```bash
firebase deploy --only apphosting:agronomy-club-next-staging --project agronomy-club --non-interactive
```

- [ ] **Step 4: Smoke-test account registration, sign-out/sign-in, profile retrieval, password reset initiation, unauthenticated API rejection, and Django Admin visibility with a disposable account. Delete the disposable Firebase identity after the test.**

- [ ] **Step 5: Record the active Firebase Auth and Cloud Run settings without secrets, run the complete project verification suite, and commit documentation.**

```bash
git add docs
git commit -m "docs: record Firebase member authentication deployment"
```
