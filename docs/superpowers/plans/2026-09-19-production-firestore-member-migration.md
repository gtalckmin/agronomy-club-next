# Production Firestore Member Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release the new site at `https://agronomy-club.web.app` with the six existing Firebase member identities and Firestore profiles safely available through Django and Cloud SQL.

**Architecture:** Firebase Authentication remains the identity provider. A one-time Cloud Run Django command reads the legacy Firestore `users` collection through ADC and creates conservative Django member profiles in a separate production Cloud SQL database. Firebase Hosting serves the new Next.js client and the client calls the isolated production Cloud Run API by its generated HTTPS URL.

**Tech Stack:** Next.js 16, React 19, Firebase Hosting and Authentication, Firebase Admin SDK, Google Cloud Firestore, Django 5, Django REST Framework, Cloud Run, Cloud SQL for PostgreSQL 16, Secret Manager, Cloud Build.

**Spec:** `docs/superpowers/specs/2026-09-19-production-firestore-member-migration-design.md`

## Global Constraints

- Preserve Firebase Authentication accounts and existing passwords in Firebase project `agronomy-club`.
- Import only Firestore `users/{uid}` documents; do not load fixtures, generated chapters, media, quizzes, events, or resources.
- The importer defaults to dry-run mode and requires `--apply` before it writes PostgreSQL data.
- Do not log, copy, commit, export, or print names, emails, UIDs, Firebase tokens, service-account JSON, database passwords, or Django secrets.
- Source emails come from Firebase Authentication; Firestore's `verified` field never controls Django or Firebase Authentication access.
- Existing Django profiles are never overwritten by the importer.
- Production Cloud Run, Cloud SQL, secrets, and service accounts use the `*-prod` names defined in the spec and stay separate from staging.
- The live frontend targets `https://agronomy-club.web.app`; custom-domain and media-storage work are out of scope.
- Do not promote the staging API or database to production traffic.

---

### Task 1: Support imported profiles that need completion

**Files:**
- Modify: `server/agronomy_club/models.py`
- Create: `server/agronomy_club/migrations/0020_allow_imported_member_profile_fields.py`
- Modify: `server/agronomy_club/serializers.py`
- Modify: `server/agronomy_club/views.py`
- Modify: `server/agronomy_club/test_member_profile_api.py`
- Modify: `client/src/lib/member-profile.ts`
- Create: `client/src/lib/member-profile.test.ts`
- Modify: `client/src/components/auth/member-profile.tsx`

**Interfaces:**
- Produces: `User.grad_yr: int | None` and `User.discipline: str`, where null/empty values are permitted only for imported incomplete profiles.
- Produces: `profileNeedsCompletion(profile: MemberProfile): boolean` and `updateMemberProfile(idToken: string, input: MemberProfileInput): Promise<MemberProfile>`.
- Consumes: `PATCH /api/member-profile/` with `full_name`, `grad_yr`, and `discipline` supplied by the authenticated caller.

- [ ] **Step 1: Write failing API tests for an imported incomplete profile.**

```python
def test_get_returns_an_imported_incomplete_profile(self):
    User.objects.create(
        full_name="Imported Member", grad_yr=None, discipline="",
        email="member@example.com", firebase_uid="firebase-member",
    )
    response = self.request("get")
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertIsNone(response.data["grad_yr"])
    self.assertEqual(response.data["discipline"], "")

def test_patch_completes_an_imported_profile(self):
    member = User.objects.create(
        full_name="Imported Member", grad_yr=None, discipline="",
        email="member@example.com", firebase_uid="firebase-member",
    )
    response = self.request("patch", {
        "full_name": "Imported Member", "grad_yr": 2029, "discipline": "Agronomy",
    })
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    member.refresh_from_db()
    self.assertEqual((member.grad_yr, member.discipline), (2029, "Agronomy"))
```

- [ ] **Step 2: Run the focused Django test and confirm the current model cannot create an incomplete profile.**

```bash
/tmp/agronomy-club-admin-tests/bin/python server/manage.py test agronomy_club.test_member_profile_api --settings=api.test_settings
```

- [ ] **Step 3: Make the minimum model and serializer changes.**

Set `User.grad_yr` to `null=True, blank=True` and `User.discipline` to `blank=True`, then create migration `0020_allow_imported_member_profile_fields.py`. Keep response serialization capable of returning `null` graduation years. Use a write serializer whose validation combines request data with `self.instance`; it must reject a create or update when the resulting `full_name`, `grad_yr`, or `discipline` is absent, null, blank, or whitespace-only. Let imported records remain incomplete only until a member supplies all fields in one PATCH.

- [ ] **Step 4: Add client-level completion tests before changing the component.**

```ts
import { describe, expect, it } from "vitest";
import { profileNeedsCompletion } from "./member-profile";

describe("profileNeedsCompletion", () => {
  it("asks imported members for missing fields", () => {
    expect(profileNeedsCompletion({
      id: 1, full_name: "Imported Member", grad_yr: null, discipline: "",
      email: "member@example.com", global_role: "user",
    })).toBe(true);
  });
});
```

- [ ] **Step 5: Implement the client completion path.**

Make `grad_yr` a `number | null`; add `profileNeedsCompletion` and `updateMemberProfile` that sends an authenticated PATCH to `/member-profile/`. In `MemberProfile`, render the completion form for an existing incomplete profile, pre-fill the imported name, and save with `updateMemberProfile`; retain POST only for a `404` profile. Do not expose email or role as editable form fields.

- [ ] **Step 6: Run focused and full profile checks.**

```bash
/tmp/agronomy-club-admin-tests/bin/python server/manage.py test agronomy_club.test_member_profile_api --settings=api.test_settings
npm --prefix client test -- member-profile
npm --prefix client run lint
npm --prefix client run typecheck
```

- [ ] **Step 7: Commit the independently reviewable profile-completion change.**

```bash
git add server/agronomy_club client/src/lib/member-profile.ts client/src/lib/member-profile.test.ts client/src/components/auth/member-profile.tsx
git commit -m "feat: complete imported member profiles"
```

### Task 2: Implement a conservative Firestore member importer

**Files:**
- Modify: `server/pyproject.toml`
- Modify: `server/poetry.lock`
- Create: `server/agronomy_club/services/__init__.py`
- Create: `server/agronomy_club/services/firestore_member_import.py`
- Create: `server/agronomy_club/management/__init__.py`
- Create: `server/agronomy_club/management/commands/__init__.py`
- Create: `server/agronomy_club/management/commands/import_firestore_members.py`
- Create: `server/agronomy_club/test_firestore_member_import.py`

**Interfaces:**
- Produces: `FirestoreMemberImporter.import_members(apply: bool) -> ImportSummary`.
- Produces: management command `python manage.py import_firestore_members [--apply]`.
- Consumes: Firestore `users` documents, Firebase Admin `auth.get_user(uid)`, and Django `User` records.
- Produces: aggregate-only JSON-safe summary fields `scanned`, `candidates`, `created`, `existing`, `skipped_invalid`, `skipped_conflict`, and `skipped_unknown_role`.

- [ ] **Step 1: Write failing importer tests with fakes, never a live Firestore project.**

```python
def test_dry_run_reports_a_candidate_without_writing(self):
    importer = FirestoreMemberImporter(
        firestore_client=FakeFirestore([FakeDocument("uid-1", {"fullName": "Member", "email": "member@example.com", "role": "member"})]),
        firebase_auth=FakeFirebaseAuth({"uid-1": FakeAuthUser("member@example.com")}),
    )
    summary = importer.import_members(apply=False)
    self.assertEqual((summary.scanned, summary.candidates, summary.created), (1, 1, 0))
    self.assertFalse(User.objects.exists())

def test_apply_creates_a_safe_incomplete_profile_once(self):
    summary = self.importer.import_members(apply=True)
    member = User.objects.get(firebase_uid="uid-1")
    self.assertEqual((summary.created, member.grad_yr, member.discipline, member.global_role), (1, None, "", "user"))
    second = self.importer.import_members(apply=True)
    self.assertEqual((second.created, second.existing), (0, 1))
```

- [ ] **Step 2: Run the focused test and confirm the import module does not yet exist.**

```bash
/tmp/agronomy-club-admin-tests/bin/python server/manage.py test agronomy_club.test_firestore_member_import --settings=api.test_settings
```

- [ ] **Step 3: Add the direct Firestore dependency and lock it.**

Add `google-cloud-firestore` to the Poetry production dependencies, regenerate `poetry.lock` with Python 3.12, and verify `poetry install --only main` includes the Firestore client. Do not add any credential file or environment variable for a key.

- [ ] **Step 4: Implement exact importer behavior.**

Use `google.cloud.firestore.Client(project=settings.FIREBASE_PROJECT_ID)` and `firebase_admin.auth.get_user`. Iterate only `client.collection("users").stream()`. Validate UID, authenticated email, optional source-email agreement, trimmed `fullName`, and role mapping before counting a candidate. Check both `User.objects.filter(firebase_uid=uid)` and `User.objects.filter(email=email)` before a write. With `apply=True`, use `transaction.atomic()` and `User.objects.create(full_name=..., grad_yr=None, discipline="", email=email, firebase_uid=uid, global_role=role)`; catch `IntegrityError` as a conflict. Emit `json.dumps(asdict(summary), sort_keys=True)` from the command and no member-level values.

- [ ] **Step 5: Test validation, roles, conflicts, and command safety.**

```bash
/tmp/agronomy-club-admin-tests/bin/python server/manage.py test agronomy_club.test_firestore_member_import --settings=api.test_settings
/tmp/agronomy-club-admin-tests/bin/python server/manage.py import_firestore_members --help
```

Add tests for source-email mismatch, missing Firebase account, missing name, unknown role, existing UID, existing email, `admin`/`alumni` mapping, and that the command writes only with `--apply`.

- [ ] **Step 6: Commit the importer.**

```bash
git add server/pyproject.toml server/poetry.lock server/agronomy_club
git commit -m "feat: add Firestore member import command"
```

### Task 3: Make the Firebase Hosting release reproducible

**Files:**
- Modify: `firebase.json`
- Create: `client/.env.production.example`
- Modify: `docs/DEPLOYMENT-STRATEGY.md`
- Create: `docs/PRODUCTION-RELEASE.md`

**Interfaces:**
- Produces: Firebase Hosting configuration for site `agronomy-club` with source root `./client` while preserving the existing staging App Hosting backend declaration.
- Produces: an ignored local production-environment template containing only public `NEXT_PUBLIC_*` values.
- Consumes: `NEXT_PUBLIC_BACKEND_URL=https://agronomy-club-api-prod-<generated-id>-as.a.run.app/api` at build time.

- [ ] **Step 1: Write the release-document assertions as a shell check.**

```bash
rg -n '"site": "agronomy-club"|"source": "./client"' firebase.json
rg -n 'NEXT_PUBLIC_BACKEND_URL|firebase deploy --only hosting' docs/PRODUCTION-RELEASE.md
git check-ignore client/.env.production
```

- [ ] **Step 2: Confirm the checks fail before adding the Hosting declaration and release document.**

Run the commands above and record that `firebase.json` only has App Hosting configuration.

- [ ] **Step 3: Add the Hosting configuration and public template.**

Add a `hosting` object to `firebase.json` with `site: "agronomy-club"`, `source: "./client"`, the standard Node build ignores, and `frameworksBackend.region: "asia-southeast1"`. Do not remove the `apphosting` array. Create `client/.env.production.example` with variable names and explanatory placeholder values only; keep `client/.env.production` ignored. Document preview-channel deploy, live deploy, version capture, and rollback commands in `docs/PRODUCTION-RELEASE.md`.

- [ ] **Step 4: Run configuration and frontend build verification.**

```bash
firebase --config firebase.json hosting:sites:list --project agronomy-club
npm --prefix client run format:check
npm --prefix client run build
```

- [ ] **Step 5: Commit production release configuration and documentation.**

```bash
git add firebase.json client/.env.production.example docs/DEPLOYMENT-STRATEGY.md docs/PRODUCTION-RELEASE.md
git commit -m "docs: add reproducible Firebase Hosting release"
```

### Task 4: Provision the isolated production API stack

**Files:**
- Create: `deploy/cloudbuild-api-prod.yaml`
- Modify: `docs/PRODUCTION-RELEASE.md`

**Interfaces:**
- Produces: Cloud SQL instance `agronomy-club-postgres-prod`, Cloud Run service `agronomy-club-api-prod`, migration job `agronomy-club-migrate-prod`, and importer job `agronomy-club-import-firestore-members-prod` in `asia-southeast1`.
- Produces: Secret Manager secrets `agronomy-club-api-prod-secret` and `agronomy-club-postgres-prod-password`, readable by the production API service account and the separate importer service account only.
- Consumes: a pinned API image digest from Artifact Registry and Cloud SQL Unix socket `/cloudsql/agronomy-club:asia-southeast1:agronomy-club-postgres-prod`.

- [ ] **Step 1: Write a deploy configuration validation check.**

```bash
rg -n 'agronomy-club-api-prod|agronomy-club-postgres-prod|asia-southeast1' deploy/cloudbuild-api-prod.yaml
gcloud beta code dev --help >/dev/null 2>&1 || true
```

- [ ] **Step 2: Add the production Cloud Build definition.**

Use `docker/server/Dockerfile` to build `asia-southeast1-docker.pkg.dev/$PROJECT_ID/agronomy-club/agronomy-club-api-prod:$COMMIT_SHA`, then deploy by immutable digest. The Cloud Run configuration must set `APP_ENV=PRODUCTION`, `FIREBASE_PROJECT_ID=agronomy-club`, `FRONTEND_URL=https://agronomy-club.web.app`, exact generated API allowed host, production database name/user/socket, and Secret Manager references. Do not include secret values in YAML substitutions.

- [ ] **Step 3: Create the production principals, database, and secrets using the documented commands.**

```bash
gcloud iam service-accounts create agronomy-club-api-prod --project agronomy-club
gcloud sql instances create agronomy-club-postgres-prod --database-version=POSTGRES_16 --tier=db-f1-micro --region=asia-southeast1 --storage-size=10 --availability-type=ZONAL --backup-start-time=07:00 --enable-point-in-time-recovery --project=agronomy-club
gcloud sql databases create agronomy_club --instance=agronomy-club-postgres-prod --project=agronomy-club
gcloud secrets create agronomy-club-api-prod-secret --replication-policy=automatic --project=agronomy-club
gcloud secrets create agronomy-club-postgres-prod-password --replication-policy=automatic --project=agronomy-club
```

Generate each secret locally in command memory, add it through stdin without echoing it, grant the runtime service account `roles/secretmanager.secretAccessor` only on the two secret resources, and grant `roles/cloudsql.client`. Use a separate importer service account for the Cloud Run import job; grant it access to the same two secrets and Cloud SQL, then obtain an explicitly approved, temporary read-only Firestore permission for the import. Create a database user and password before deploying the service. Record IAM policy bindings without values in `docs/PRODUCTION-RELEASE.md`.

- [ ] **Step 4: Build, deploy, migrate, and test the API.**

```bash
gcloud builds submit --config deploy/cloudbuild-api-prod.yaml --project agronomy-club .
gcloud run jobs execute agronomy-club-migrate-prod --region=asia-southeast1 --project=agronomy-club --wait
curl --fail --silent --show-error https://<production-api-host>/api/healthcheck/ping/
curl --fail --silent --show-error -o /dev/null -w '%{http_code}\n' https://<production-api-host>/admin/
```

Create the Cloud Run Jobs with the same immutable image, service account, Cloud SQL socket, environment, and secret references as the API service. The migration job executes `python manage.py migrate --noinput`; the importer job executes `python manage.py import_firestore_members`. Record the returned image digest, revision, migration job execution, and API host in the release document.

- [ ] **Step 5: Commit the declarative release assets and operations record.**

```bash
git add deploy/cloudbuild-api-prod.yaml docs/PRODUCTION-RELEASE.md
git commit -m "ops: add production Cloud Run release configuration"
```

### Task 5: Perform and reconcile the live member import

**Files:**
- Modify: `docs/PRODUCTION-RELEASE.md`

**Interfaces:**
- Consumes: healthy production API/database and Cloud Run job `agronomy-club-import-firestore-members-prod`.
- Produces: a recorded aggregate dry-run, apply-run, and post-apply dry-run summary.

- [ ] **Step 1: Execute the production dry run and retain aggregate output only.**

```bash
gcloud run jobs execute agronomy-club-import-firestore-members-prod --region=asia-southeast1 --project=agronomy-club --wait
```

Read the job logs using the execution identifier. Confirm `scanned=6`, `candidates=6`, `created=0`, `existing=0`, and each skip count is zero. Stop the release if any count differs and do not run an apply job.

- [ ] **Step 2: Run the apply job only after the dry-run result matches six candidates.**

Update the job command to `python manage.py import_firestore_members --apply`, execute it once, then restore the job command to dry-run mode. The apply result must be `created=6`, `existing=0`, with all skip counts zero.

- [ ] **Step 3: Prove importer idempotency.**

Run the restored dry-run job. Require `scanned=6`, `candidates=0`, `created=0`, and `existing=6`. Do not use the Hosting preview for member sign-in because the production API deliberately permits only the live `agronomy-club.web.app` browser origin. Record only aggregate counts.

- [ ] **Step 4: Update the release record and commit it without member data.**

```bash
git add docs/PRODUCTION-RELEASE.md
git commit -m "docs: record production member import"
```

### Task 6: Preview, promote, and smoke-test Firebase Hosting

**Files:**
- Modify: `docs/PRODUCTION-RELEASE.md`

**Interfaces:**
- Consumes: tested production API URL and a temporary ignored `client/.env.production` with public build identifiers.
- Produces: preview release followed by the live `https://agronomy-club.web.app` release.

- [ ] **Step 1: Create the temporary local build environment without committing it.**

```bash
cp client/.env.production.example client/.env.production
chmod 600 client/.env.production
```

Replace only the example values with public Firebase Web configuration and the production API URL. Verify `git status --short client/.env.production` is empty because the file is ignored.

- [ ] **Step 2: Build a Firebase Hosting preview and run browser/API smoke checks.**

```bash
firebase hosting:channel:deploy production-preview --project agronomy-club --site agronomy-club --non-interactive
```

Check the returned preview URL for the landing page, chapters, resources, sign-in, sign-up, password-reset page, and responsive navigation. Confirm the production API's exact CORS behavior without changing it for the preview hostname:

```bash
curl --silent --show-error -D - -o /dev/null -H 'Origin: https://agronomy-club.web.app' https://<production-api-host>/api/healthcheck/ping/ | rg -i 'access-control-allow-origin: https://agronomy-club.web.app'
curl --silent --show-error -D - -o /dev/null -H 'Origin: <preview-url>' https://<production-api-host>/api/healthcheck/ping/ | rg -iv 'access-control-allow-origin: <preview-url>'
```

Use Django Admin with the staff account to create a test chapter only if it is an authentic operational chapter; otherwise do not create test content in production.

- [ ] **Step 3: Record the existing live version and deploy the tested commit.**

```bash
firebase hosting:channel:list --project agronomy-club --site agronomy-club --json
firebase deploy --only hosting --project agronomy-club --non-interactive
```

Record pre-release version `3c44a8ab43b9413c`, the returned live version, the Git commit, production API revision and digest, migration execution, importer counts, and timestamp. Remove the ignored local `client/.env.production` after the deployment.

- [ ] **Step 4: Smoke-test the live website and rollback path.**

```bash
curl --fail --silent --show-error https://agronomy-club.web.app/
curl --fail --silent --show-error https://agronomy-club.web.app/sign-in
firebase hosting:clone --help
```

In a browser, verify the landing page, public navigation, an existing verified member completion/sign-in path, staff access to `/admin/`, and no browser console CORS errors. The member test must sign in with an existing verified Firebase account, complete graduation year and discipline, sign out, then show the completed profile after the next sign-in. If a frontend smoke check fails, use the documented `firebase hosting:clone` rollback command to restore `3c44a8ab43b9413c` immediately; leave the production database and import intact because data rollback is not part of Hosting rollback.

- [ ] **Step 5: Commit the final, non-sensitive release record.**

```bash
git add docs/PRODUCTION-RELEASE.md
git commit -m "docs: record production Firebase Hosting rollout"
```

## Plan self-review

- [x] **Spec coverage:** Tasks 1 and 2 preserve and complete six Firebase member profiles; Tasks 3 through 6 create isolated production infrastructure, preview Hosting, promote `web.app`, record release data, and document rollback. The plan excludes generated data, custom-domain work, media uploads, and credential files as required.
- [x] **Placeholder scan:** The plan contains no unfinished-work markers or deferred implementation language. Generated Cloud Run host values are intentionally resolved by Cloud Run at deployment and recorded as release metadata.
- [x] **Type consistency:** `profileNeedsCompletion`, `updateMemberProfile`, `FirestoreMemberImporter.import_members`, and `ImportSummary` use the same names and contracts in their producing and consuming tasks.
