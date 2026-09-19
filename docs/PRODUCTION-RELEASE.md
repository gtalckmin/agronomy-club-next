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

The release imports the six real `users` documents from legacy Firestore. It does not load generated chapters, demo fixtures, media, quizzes, events, resources, or unverified Firestore fields. Firebase Authentication remains the identity provider and Firebase passwords are unchanged.

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
API_ALLOWED_HOSTS=<generated-production-cloud-run-host>
POSTGRES_NAME=agronomy_club
POSTGRES_USER=agronomy_club
POSTGRES_HOST=/cloudsql/agronomy-club:asia-southeast1:agronomy-club-postgres-prod
```

Create one secret for Django's `API_SECRET_KEY` and one for `POSTGRES_PASSWORD`. Generate them locally, add their values through stdin, and never place their values in a shell history, source file, Cloud Build substitution, terminal capture, or Git commit. The `agronomy-club-api-prod` service account needs Cloud SQL Client and Secret Manager Secret Accessor on only those two production secret resources. The Firestore importer additionally needs read-only Firestore access and Firebase Authentication user-read access.

Run the migration job after each release that includes Django migrations:

```bash
gcloud run jobs execute agronomy-club-migrate-prod --region=asia-southeast1 --project=agronomy-club --wait
curl --fail --silent --show-error https://<production-api-host>/api/healthcheck/ping/
curl --fail --silent --show-error -o /dev/null -w '%{http_code}\n' https://<production-api-host>/admin/
```

The expected responses are `Pong!` and HTTP `200` for the Django Admin sign-in page. Record the Cloud Run revision, image digest, migration execution, API host, and deployment timestamp below before changing Hosting traffic.

| Release field | Recorded value |
| --- | --- |
| Git commit | |
| API image digest | |
| Cloud Run revision | |
| Migration execution | |
| Production API host | |
| Deployment timestamp (AWST) | |

## Firestore member import

The importer is safe by default. It reads only Firestore `users/{uid}` documents and writes no member record unless the job runs with `--apply`. It queries Firebase Authentication for the authoritative email and skips a Firestore document if the UID, name, role, or optional source email is invalid. Existing Django profiles are never overwritten.

First run the job in dry-run mode:

```bash
gcloud run jobs execute agronomy-club-import-firestore-members-prod --region=asia-southeast1 --project=agronomy-club --wait
```

Inspect the job's aggregate JSON log. Before applying, require `scanned: 6`, `candidates: 6`, `created: 0`, `existing: 0`, `skipped_invalid: 0`, `skipped_conflict: 0`, and `skipped_unknown_role: 0`. Any different result stops the release until the data issue is understood; do not use `--apply` to force a partial import.

Set the job command to `python manage.py import_firestore_members --apply`, run it once, then return the job to its default dry-run command. The apply run must report six created profiles and zero skip counts. A final dry-run must report six existing profiles and no candidates. Record aggregate counts only:

| Import execution | Scanned | Candidates | Created | Existing | Invalid | Conflict | Unknown role |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Dry run before apply | | | | | | | |
| Apply run | | | | | | | |
| Dry run after apply | | | | | | | |

## Firebase Hosting preview and promotion

Create a local ignored frontend build file from the public template. It contains public browser identifiers and the generated production API URL; it contains no server credential.

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

| Release field | Recorded value |
| --- | --- |
| Previous Hosting version | `3c44a8ab43b9413c` |
| New Hosting version | |
| Preview URL | |
| Live public-pages smoke test | |
| Existing-member completion smoke test | |
| Django Admin smoke test | |
| Rollback command verified | |
