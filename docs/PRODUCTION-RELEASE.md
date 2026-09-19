# Production release runbook

This runbook releases the managed Agronomy Club stack to `https://agronomy-club.web.app`. It uses Firebase Hosting for the Next.js frontend, Cloud Run for Django, and Cloud SQL for PostgreSQL. It is intentionally separate from the staging App Hosting backend.

## Release boundary

- **Firebase project:** `agronomy-club`
- **Firebase Hosting site:** `agronomy-club`
- **Live website:** `https://agronomy-club.web.app`
- **Production region:** `asia-southeast1`
- **Production API:** `agronomy-club-api-prod`
- **Production database:** `agronomy-club-postgres-prod`
- **Production migration job:** `agronomy-club-migrate-prod`
- **Production Firestore importer job:** `agronomy-club-import-firestore-members-prod`
- **Previous live Hosting version:** `3c44a8ab43b9413c`

This release does not import legacy Firestore members. The legacy `users` documents remain untouched so they can be exported and uploaded later through a separately scheduled, reviewed migration. Firebase Authentication remains the identity provider and Firebase passwords are unchanged.

## Before provisioning

Run all commands from the repository root on `feat/plant-landing-security` after the test suite is green. The deployer needs Firebase Hosting, Cloud Run, Cloud SQL, Artifact Registry, Cloud Build, Secret Manager, IAM, Firebase Authentication, and Firestore permissions in project `agronomy-club`.

```bash
git status --short
git log -1 --oneline
firebase login
firebase projects:list
gcloud config set project agronomy-club
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com firestore.googleapis.com identitytoolkit.googleapis.com
```

Confirm that Firebase Authentication has email/password enabled and that `agronomy-club.web.app` is an authorised domain. Do not use mobile email-link authentication or Cordova OAuth; the web client uses Firebase's supported email/password, email-verification, and password-reset paths.

## API release

Build and deploy the Django API with `deploy/cloudbuild-api-prod.yaml`. The release configuration must use the Cloud SQL Unix socket, exact production frontend URL, generated Cloud Run hostname, Secret Manager secret references, and an immutable Artifact Registry image digest. It must set the following non-secret environment values:

```text
APP_ENV=PRODUCTION
FIREBASE_PROJECT_ID=agronomy-club
FRONTEND_URL=https://agronomy-club.web.app
FRONTEND_EXTRA_ORIGINS=https://www.agronomyclub.au
API_ALLOWED_HOSTS=<generated-production-cloud-run-host>
POSTGRES_NAME=agronomy_club
POSTGRES_USER=agronomy_club
POSTGRES_HOST=/cloudsql/agronomy-club:asia-southeast1:agronomy-club-postgres-prod
```

Create one secret for Django's `API_SECRET_KEY` and one for `POSTGRES_PASSWORD`. Generate them locally, add their values through stdin, and never place their values in a shell history, source file, Cloud Build substitution, terminal capture, or Git commit. The `agronomy-club-api-prod` service account needs Cloud SQL Client and Secret Manager Secret Accessor on only those two production secret resources. The one-off `agronomy-member-import-prod` service account needs its own Cloud SQL and secret access plus temporary Firestore and Firebase Authentication permissions to validate legacy UIDs; it must not be assigned to the public API service.

Run the migration job after each release that includes Django migrations:

```bash
gcloud run jobs execute agronomy-club-migrate-prod --region=asia-southeast1 --project=agronomy-club --wait
curl --fail --silent --show-error https://<production-api-host>/api/healthcheck/ping/
curl --fail --silent --show-error -o /dev/null -w '%{http_code}\n' https://<production-api-host>/admin/
```

The expected responses are `Pong!` and HTTP `200` for the Django Admin sign-in page. Record the Cloud Run revision, image digest, migration execution, API host, and deployment timestamp below before changing Hosting traffic.

| Release field               | Recorded value                                                            |
| --------------------------- | ------------------------------------------------------------------------- |
| Git commit                  | `b0976fe` (Hosting release); `30c9326` (API CORS release)                 |
| API image digest            | `sha256:ef49ac77f0bf0967596f1981806fa5179715b24ad28c1f83fa4db4d0a4b31b49` |
| Cloud Run revision          | `agronomy-club-api-prod-00002-wp6`                                        |
| Migration execution         | `agronomy-club-migrate-prod-tk64s`                                        |
| Production API host         | `agronomy-club-api-prod-869412139245.asia-southeast1.run.app`             |
| Deployment timestamp (AWST) | 19 September 2026 19:25                                                   |

## Deferred Firestore member import

The importer is safe by default. It reads only Firestore `users/{uid}` documents and writes no member record unless the job runs with `--apply`. It queries Firebase Authentication for the authoritative email and skips a Firestore document if the UID, name, role, or optional source email is invalid. Existing Django profiles are never overwritten. Do not run this section as part of the initial website promotion; it is retained as the documented procedure for a later member migration.

First update the job to run the machine-checkable dry-run gate, then execute it:

```bash
gcloud run jobs update agronomy-club-import-firestore-members-prod --region=asia-southeast1 --project=agronomy-club --command=python --args=manage.py,import_firestore_members,--expect-clean-dry-run=6
gcloud run jobs execute agronomy-club-import-firestore-members-prod --region=asia-southeast1 --project=agronomy-club --wait
```

The command fails unless `scanned: 6`, `candidates: 6`, `created: 0`, `existing: 0`, `skipped_invalid: 0`, `skipped_conflict: 0`, and `skipped_unknown_role: 0`. Any failure stops the release until the data issue is understood; do not use `--apply` to force a partial import.

Run the write step only through its matching gate, then run the post-import
reconciliation gate. Each execution fails if any count differs from its expected
state, including a skipped or partially created profile:

```bash
gcloud run jobs update agronomy-club-import-firestore-members-prod --region=asia-southeast1 --project=agronomy-club --command=python --args=manage.py,import_firestore_members,--apply,--expect-created=6
gcloud run jobs execute agronomy-club-import-firestore-members-prod --region=asia-southeast1 --project=agronomy-club --wait
gcloud run jobs update agronomy-club-import-firestore-members-prod --region=asia-southeast1 --project=agronomy-club --command=python --args=manage.py,import_firestore_members,--expect-existing=6
gcloud run jobs execute agronomy-club-import-firestore-members-prod --region=asia-southeast1 --project=agronomy-club --wait
```

After the reconciliation succeeds, restore the job to its default dry-run command and remove its temporary Firestore, Firebase Authentication, Cloud SQL, and Secret Manager access. Record aggregate counts only:

| Import execution     | Scanned | Candidates | Created | Existing | Invalid | Conflict | Unknown role |
| -------------------- | ------: | ---------: | ------: | -------: | ------: | -------: | -----------: |
| Dry run before apply |         |            |         |          |         |          |              |
| Apply run            |         |            |         |          |         |          |              |
| Dry run after apply  |         |            |         |          |         |          |              |

## Firebase Hosting preview and promotion

Create a local ignored frontend build file from the public template. It contains public browser identifiers and the generated production API URL; it contains no server credential. The production client uses Next.js static export and Firebase Hosting serves `client/out` directly. Image requests are direct browser requests and all live data continues to be fetched from Django's API. Keep `FRONTEND_URL` as the canonical `web.app` origin and set `FRONTEND_EXTRA_ORIGINS` to any additional whitespace-separated browser origins, including `https://www.agronomyclub.au`.

```bash
cp client/.env.production.example client/.env.production
chmod 600 client/.env.production
git status --short client/.env.production
npm --prefix client run build
firebase hosting:channel:deploy production-preview --project agronomy-club --site agronomy-club --non-interactive
```

Check the returned preview URL for the landing page, public navigation, chapter/resources pages, sign-in, sign-up, password reset, and mobile layout. The production API permits the live `agronomy-club.web.app` browser origin only, so Firebase member sign-in is tested after live promotion. Verify the intended CORS response without adding the preview hostname as a permanent allowed origin:

```bash
curl --silent --show-error -D - -o /dev/null -H 'Origin: https://agronomy-club.web.app' https://<production-api-host>/api/healthcheck/ping/ | rg -i 'access-control-allow-origin: https://agronomy-club.web.app'
```

Capture the live version, then deploy the same commit:

```bash
firebase hosting:channel:list --project agronomy-club --site agronomy-club --json
firebase deploy --only hosting --project agronomy-club --non-interactive
curl --fail --silent --show-error https://agronomy-club.web.app/
curl --fail --silent --show-error https://agronomy-club.web.app/sign-in
```

On the live site, sign in using one existing verified Firebase account, complete graduation year and discipline, sign out, and sign in again. Confirm the completed member profile is shown. Confirm Django staff can reach `/admin/` on the production API host. Remove the ignored local `client/.env.production` after the release.

## Rollback

If the live frontend smoke test fails, restore Firebase Hosting version `3c44a8ab43b9413c` before changing any database state. Run `firebase hosting:clone --help` to confirm the installed CLI's source and target syntax, then clone the recorded prior live release to the live site. The Firestore import and production Cloud SQL data are not rolled back by a Hosting rollback; do not reverse Django migrations without a specific reviewed forward repair.

Record the new Hosting version and final smoke-test result:

| Release field                         | Recorded value                                                                                                                  |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Previous Hosting version              | `3c44a8ab43b9413c`                                                                                                              |
| New Hosting version                   | `8861dd6a8385d084`                                                                                                              |
| Preview URL                           | Not promoted; the final static build was validated locally before direct release.                                               |
| Live public-pages smoke test          | Passed: homepage and sign-in returned HTTP 200; footer copy, chapter redirect, and CORS headers for both live origins verified. |
| Production chapter content            | Passed: the University of Western Australia chapter was copied from staging and the production API returned one chapter.        |
| Existing-member completion smoke test | Deferred with the member migration.                                                                                             |
| Django Admin smoke test               | Passed: the `agronomy-club@uwa.edu.au` staff account was provisioned and the Admin login page returned HTTP 200.                |
| Rollback command verified             | Prior live version recorded; restore procedure documented above.                                                                |

## 19 September 2026: Chapter detail hotfix

The public Chapters index loaded successfully, but selecting **View** for a
chapter opened the generic Next.js “This page couldn’t load” screen. The API
request was successful; the frontend caused the failure by conditionally
calling its chapter-list data hook after reading the `chapter` URL parameter.
Changing from the index state to a detail state therefore changed the React
hook order.

The fix separates the list into its own component. The route component now
selects either the chapter detail or the list before either component calls its
data hooks, which keeps each component's hook sequence stable.

Validation completed before release:

- `npm test`, `npm run lint`, and `npm run typecheck` passed.
- `npm run build` completed with the production static-export configuration.
- A fresh production browser session loaded `/chapters?page=1`, selected
  **View**, reached `/chapters?chapter=1`, and rendered the University of
  Western Australia detail page.

### Chapter pagination feedback-loop hardening

Commit `8946960` removed local page state that wrote to
`/chapters?page=<page>` from a router effect. Under the static export this
could repeatedly remount the route in some browsers. Pagination now derives
the requested positive whole-number page directly from the URL, with invalid
values falling back to page 1. The new pure parser has unit coverage.

The live release was checked in a fresh browser session on
`https://www.agronomyclub.au`: the list performed one navigation and one API
request, displayed UWA, and its **View** control rendered
`/chapters?chapter=1` successfully.
