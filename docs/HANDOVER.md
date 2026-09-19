# Agronomy Club project handover

**Last verified:** 19 September 2026 (AWST)

This is the current operational source of truth. Read it with [PRODUCTION-RELEASE.md](PRODUCTION-RELEASE.md) and [ADMIN-ACCESS.md](ADMIN-ACCESS.md). [DEPLOYMENT-STRATEGY.md](DEPLOYMENT-STRATEGY.md) records earlier planning and may describe proposed `.org` domains that are not live.

## Purpose and architecture

`gtalckmin/agronomy-club-next` is the active Agronomy Club application and a fork of `codersforcauses/agronomy-club`. The older `gtalckmin/Agronomy-Club` repository is historical reference material only.

```text
Visitors
  └─ www.agronomyclub.au and agronomy-club.web.app
       └─ Firebase Hosting: static Next.js export (client/out)
            └─ HTTPS requests to Django API on Cloud Run
                 └─ Cloud SQL for PostgreSQL

Firebase Authentication ── member identity
Firestore ── retained legacy user records
Secret Manager ── server secrets and admin bootstrap secret
```

The application provides chapters, events, resources, quizzes, alumni, Firebase member accounts, and Django staff administration.

## Production inventory

| Area                            | Current state                                                             |
| ------------------------------- | ------------------------------------------------------------------------- |
| Google Cloud / Firebase project | `agronomy-club`                                                           |
| Public website                  | `https://www.agronomyclub.au`                                             |
| Firebase Hosting fallback       | `https://agronomy-club.web.app`                                           |
| Firebase Hosting site           | `agronomy-club`                                                           |
| Frontend source                 | `client/`, built as a static export                                       |
| Production API                  | Cloud Run `agronomy-club-api-prod`, `asia-southeast1`                     |
| API revision                    | `agronomy-club-api-prod-00002-wp6`, 100% traffic at verification          |
| API origin compiled into client | `https://agronomy-club-api-prod-869412139245.asia-southeast1.run.app/api` |
| Cloud Run reported URL          | `https://agronomy-club-api-prod-q7uvfi4yhq-as.a.run.app`                  |
| Database                        | Cloud SQL `agronomy-club-postgres-prod`, PostgreSQL 16                    |
| Cloud SQL connection            | `agronomy-club:asia-southeast1:agronomy-club-postgres-prod`               |
| Database status                 | Runnable, backups enabled, `db-f1-micro` tier                             |
| Firebase Auth                   | Email/password member identity provider                                   |
| Firestore                       | Existing native default database in `nam5`                                |
| Staging API                     | Cloud Run `agronomy-club-api-staging`, revision `00006-hfl`               |

Cloud Run reports a newer generated service URL than the older URL compiled into the live client. Both currently serve the API. Do not consolidate those hosts casually: update the frontend build configuration, API allowed hosts, CORS settings, deploy both services, and smoke-test in one planned release.

## Public frontend behaviour

[firebase.json](../firebase.json) serves `client/out` with clean URLs and this legacy path redirect:

```text
/chapters/<id>  →  /chapters?chapter=<id>
```

The API production CORS settings allow the canonical Hosting origin and the custom `.au` origin:

```text
FRONTEND_URL=https://agronomy-club.web.app
FRONTEND_EXTRA_ORIGINS=https://www.agronomyclub.au
```

Commit `f906d16` fixed the Chapters detail route. The former implementation conditionally called a React Query hook, so selecting a chapter changed the React hook order and produced “This page couldn’t load.” The list now runs in its own component. After every Hosting release, test:

1. `https://www.agronomyclub.au/chapters?page=1` loads a UWA card.
2. Selecting **View** opens `/chapters?chapter=1`.
3. The UWA detail page remains visible and the API returns HTTP 200.

This flow passed on both `web.app` and `www.agronomyclub.au` on 19 September 2026. For an earlier browser error, hard-refresh or test in a private window before treating it as a deployment regression.

## Data, members, and roles

- Production has one verified content item copied from staging: **University of Western Australia** (`UWA`, Perth, `agronomy-club@uwa.edu.au`).
- Legacy Firestore member data has not been written to Cloud SQL. Import is intentionally deferred at the owner's request.
- The importer defaults to dry run and has count gates. Follow [PRODUCTION-RELEASE.md](PRODUCTION-RELEASE.md) exactly before any `--apply` operation. Never use an apply run merely for testing.
- Firebase Authentication owns member passwords. Password hashes cannot be moved into Django or PostgreSQL.
- Firebase member accounts and Django staff accounts are separate. Django Admin manages chapters, roles, memberships, committee positions, events, resources, quizzes, and member profiles.

## Admin access

The working Django Admin fallback is:

```text
https://agronomy-club-api-prod-869412139245.asia-southeast1.run.app/admin/
```

The initial Django superuser is `agronomy-club@uwa.edu.au`. Its initial password is stored only in Secret Manager. An authorised project owner can retrieve it in Cloud Shell and must change it after first sign-in:

```bash
gcloud secrets versions access latest \
  --secret=agronomy-club-admin-bootstrap-prod \
  --project=agronomy-club
```

Never print, paste, commit, or send that password. Reset a lost password using a recorded one-off Cloud Run administrative job.

`https://admin.agronomyclub.org/admin/` is the intended permanent address but is **not provisioned**: it has no DNS record or Cloud Run mapping. Its setup is in [ADMIN-ACCESS.md](ADMIN-ACCESS.md). The live public custom domain is `.au`; do not assume `.org` is a live public or admin endpoint.

## Release procedures

### Frontend: Firebase Hosting

1. Create an ignored `client/.env.production` from `client/.env.production.example`. It contains public browser identifiers and an API origin, never server credentials.
2. From `client/`, run:

   ```bash
   npm ci
   npm test
   npm run lint
   npm run typecheck
   npm run build
   ```

3. From the repository root, deploy the generated `client/out`:

   ```bash
   firebase deploy --only hosting --project agronomy-club --non-interactive
   ```

4. Use a fresh browser session to smoke-test homepage, sign-in, chapter list, chapter detail, and both frontend origins. Record the release in [PRODUCTION-RELEASE.md](PRODUCTION-RELEASE.md).

Firebase deployment creates a local `.firebase/` cache; it is ignored.

### Backend: Cloud Run and Cloud SQL

Build the Django image using [deploy/cloudbuild-api-prod.yaml](../deploy/cloudbuild-api-prod.yaml), deploy an immutable digest to `agronomy-club-api-prod`, and run the dedicated migration job only when migrations changed. The runtime uses Cloud SQL through its Unix socket and service account `agronomy-club-api-prod@agronomy-club.iam.gserviceaccount.com`.

Required production configuration includes:

```text
APP_ENV=PRODUCTION
FIREBASE_PROJECT_ID=agronomy-club
POSTGRES_HOST=/cloudsql/agronomy-club:asia-southeast1:agronomy-club-postgres-prod
POSTGRES_NAME=agronomy_club
POSTGRES_USER=agronomy_club
POSTGRES_PASSWORD=Secret Manager reference
API_SECRET_KEY=Secret Manager reference
```

Before moving Cloud Run traffic, verify healthcheck, public API, Admin login, exact CORS headers for both frontend origins, and migration status. Use the full commands and rollback instructions in [PRODUCTION-RELEASE.md](PRODUCTION-RELEASE.md).

## Local development and checks

```bash
cp client/.env.example client/.env
cp server/.env.example server/.env

cd server
docker compose up -d
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver

# separate terminal
cd client
npm ci
npm run dev
```

Use `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/api` for ordinary local development. Do not point routine development at production.

```bash
cd client && npm test && npm run lint && npm run typecheck && npm run build
cd server && poetry run python manage.py test --settings=api.test_settings
```

## Security and operating controls

- Never commit `.env`, `.env.prod`, `client/.env.production`, service-account keys, database exports, or passwords.
- Production secrets remain in Secret Manager. Restrict access to the runtime identity or an explicitly authorised administrative identity.
- The API permits only the two exact frontend origins listed above. Add a browser origin only as part of a tested release.
- Cloud SQL currently has public IPv4 enabled. Plan a reviewed hardening task for network access; do not disable it until the Cloud Run connection and maintenance path have been verified.
- Durable Cloud Storage-backed media storage, backup, and restore procedures are not yet implemented. Do not rely on Admin uploads as durable production media until this is completed and tested.
- Compose, GHCR, Nginx, and Watchtower remain useful self-managed material, but are not the active production deployment path.

## Outstanding work

1. Provision `admin.agronomyclub.org` with DNS and an appropriate Cloud Run custom-domain/load-balancer configuration; test Django session and CSRF.
2. Plan and approve a Firestore member migration. Begin with the documented dry-run gate and reconcile counts before any write.
3. Establish Cloud Storage-backed media, database/media backup, and a restore exercise.
4. Review Cloud SQL network exposure, IAM, monitoring, and budget alerts.
5. Reconcile historic `.org` references after the domain strategy is decided.
6. Merge reviewed work into `main`. The current work is on `feat/plant-landing-security`; the last application hotfix is `f906d16`. Refresh this handover after each release.

## References

| Need                                    | Source                                                      |
| --------------------------------------- | ----------------------------------------------------------- |
| Current operations                      | This document                                               |
| Exact production release / rollback     | [PRODUCTION-RELEASE.md](PRODUCTION-RELEASE.md)              |
| Admin domain and password recovery      | [ADMIN-ACCESS.md](ADMIN-ACCESS.md)                          |
| Application architecture and data model | [PROJECT.md](PROJECT.md)                                    |
| Historic migration design               | [DEPLOYMENT-STRATEGY.md](DEPLOYMENT-STRATEGY.md)            |
| Persistent agent context                | [AGENT-MEMORY.md](AGENT-MEMORY.md)                          |
| Frontend routing                        | [firebase.json](../firebase.json), `client/next.config.mjs` |
| API configuration                       | `server/api/settings.py`, `deploy/cloudbuild-api-prod.yaml` |
