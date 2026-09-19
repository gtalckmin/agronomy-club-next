# Firebase and Google Cloud deployment strategy

**Status:** The isolated App Hosting staging backend is configured for a local-source rollout. Production uses a static Firebase Hosting deployment at `https://agronomy-club.web.app`; the legacy Firestore member migration is intentionally deferred so its users can be exported and uploaded later. Use [PRODUCTION-RELEASE.md](PRODUCTION-RELEASE.md) for the recorded release procedure. Custom-domain cutover remains outside this release.

## Why this changes the deployment model

The former Agronomy Club site was deployed from the separate `gtalckmin/Agronomy-Club` repository to the Firebase project `agronomy-club`. Its documented public Hosting address was `https://agronomy-club.web.app`, and its intended public domain was `www.agronomyclub.org`.

This repository has a different application architecture:

```text
Next.js client  →  Django API  →  PostgreSQL
```

The client can be statically exported to Firebase Hosting because authenticated and live data flows use the separate Django API. The checked-in production Compose file is useful for local and self-managed-host deployments, but it does not define a complete managed-cloud deployment: it has no configured public hostname, certificate source, hosted database, or persistent media store.

The recommended direction is to keep the established Firebase and Google Cloud estate, while moving this application to managed services that suit its architecture.

## Recommended target architecture

```text
Visitors
   │
   ▼
www.agronomyclub.org
   │
   ▼
Firebase Hosting
   └── Static Next.js export (`client/out`)
            │ HTTPS API requests
            ▼
     Cloud Run service
     └── Django application (`server/`)
              │
              ▼
        Cloud SQL for PostgreSQL

Cloud Storage ── Django static files and member-uploaded media
Secret Manager ── Django secret, database credentials, admin bootstrap secret
Cloud Logging/Monitoring ── application and deployment visibility
```

Firebase Hosting is the production frontend delivery path. It serves the tested static Next.js export through its CDN, while client-side requests use the explicit Django API origin. Firebase App Hosting remains useful for the separate staging backend. Cloud Run is the managed runtime for the existing Django container, while Cloud SQL provides the PostgreSQL database that Django expects.

This separates frontend and API deployments while avoiding a manually maintained virtual machine, a Docker auto-updater, and hand-managed TLS certificates.

## Current staging deployment

On 19 September 2026, the Next.js client was deployed from local source to this isolated Firebase App Hosting backend:

- **Backend:** `agronomy-club-next-staging`
- **Region:** `asia-southeast1`
- **Staging URL:** `https://agronomy-club-next-staging--agronomy-club.asia-southeast1.hosted.app`
- **Release source:** the `feat/plant-landing-security` branch, including commit `4670595`.

The deployment passed the production build, TypeScript, ESLint, Prettier, and production dependency-audit checks before the Firebase rollout. Firebase reported the rollout as successful, and the public staging URL returned HTTP 200 with the new landing page.

This staging deployment does **not** replace the existing `agronomy-club.web.app` Firebase Hosting site or either public custom domain.

The staging Django API and database were provisioned on 19 September 2026:

- **Cloud Run API:** `agronomy-club-api-staging` in `asia-southeast1`, with the generated staging URI `https://agronomy-club-api-staging-q7uvfi4yhq-as.a.run.app`.
- **Cloud SQL:** `agronomy-club-postgres-staging`, PostgreSQL 16 Enterprise edition on the `db-f1-micro` tier, with a 10 GB SSD disk, zonal availability, automated backups, and point-in-time recovery.
- **Database:** `agronomy_club`, reached only through the Cloud Run Cloud SQL socket. Its dedicated database password and the Django secret are separate Secret Manager secrets, each readable only by the dedicated `agronomy-club-api-staging` runtime service account.
- **Release image:** `asia-southeast1-docker.pkg.dev/agronomy-club/agronomy-club/agronomy-club-api-staging:b4c3f2f`.
- **Migration:** the `agronomy-club-migrate-staging` Cloud Run Job completed successfully after the release image and `FIREBASE_PROJECT_ID=agronomy-club` were applied. It must be run explicitly after future releases containing Django migrations.

The first migration attempt exposed a project configuration issue: the Cloud SQL Admin API was disabled, which prevented the Cloud Run Cloud SQL socket from mounting. It was enabled and the identical migration job then completed successfully. This is recorded so the service is not disabled accidentally during future project cleanup.

The staging API permits public invocation so the Firebase browser client can reach public club data. Django's exact allowed-host and CORS settings restrict browser origins to the staging App Hosting URL; Django Admin continues to require a staff login. The App Hosting configuration points `NEXT_PUBLIC_BACKEND_URL` at the generated Cloud Run staging API URL. Uploaded media is not yet persistent because this repository has not yet been configured with Cloud Storage-backed Django storage; do not use staff administration to upload production media during this staging phase.

## Domain and routing

The approved permanent Django Admin address is `https://admin.agronomyclub.org/admin/`. When provisioned, it routes directly to the production Cloud Run service and remains separate from Firebase Hosting so Django's session and CSRF cookies remain same-origin. See [ADMIN-ACCESS.md](ADMIN-ACCESS.md) for the required DNS, TLS, Cloud Run, verification, and staff-password recovery steps.

The production domain should remain `www.agronomyclub.org`; redirect the apex `agronomyclub.org` to it. Connect the custom domain through Firebase after a staging rollout succeeds.

The client should call the API through a single production HTTPS origin chosen during implementation:

1. **Preferred initially: `api.agronomyclub.org`.** Point this subdomain directly at the Cloud Run Django service. Set `NEXT_PUBLIC_BACKEND_URL` to `https://api.agronomyclub.org/api`, set Django `FRONTEND_URL` to `https://www.agronomyclub.org`, and restrict `API_ALLOWED_HOSTS` and CORS to the exact production hosts.
2. **Optional later: same-origin `/api` routing.** Firebase Hosting can rewrite requests to Cloud Run. Before adopting that layout, verify Django admin, CSRF protection, cookies, caching, and any authenticated request flows end to end. Firebase Hosting documents that cookies are generally stripped when Hosting proxies to Cloud Run, so this must not be assumed safe for session-based features.

Use the first option for the first rollout. It gives the API an explicit boundary and avoids introducing a proxy behavior before its authentication effects have been tested.

## Data and identity boundaries

The legacy project used Firebase Authentication and Firestore. This application has a Django-owned relational data model and a PostgreSQL database. Treat data and identity migration as a separate, gated project.

### Member administration and member accounts

The existing Django Admin interface can manage members, chapter memberships, chapters, events, resources, quizzes, and uploaded media. A restricted Django staff account is therefore the first administration interface to deploy at `/admin/`.

Member authentication uses Firebase Authentication as the identity provider and Cloud SQL as the member-profile source of truth. The Next.js client supports Firebase email/password registration, verification, sign-in, password reset, and sign-out. It sends a Firebase ID token to the Django member-profile API; Django verifies the token for the `agronomy-club` Firebase project and maps its UID to `agronomy_club.User.firebase_uid`. Member profile fields, roles, and chapter memberships stay in Django and are managed through Django Admin.

Firebase email verification is required before the API creates a member profile. The client never supplies a member role, Firebase UID, or profile email to Django: those are assigned from the verified token or server defaults. Existing Firebase users without a Cloud SQL profile complete the profile after sign-in. Existing Django profiles without a Firebase UID require a separately reviewed staff reconciliation; they are never linked automatically by email.

The staging App Hosting hostname `agronomy-club-next-staging--agronomy-club.asia-southeast1.hosted.app` is an authorised Firebase Authentication domain for web verification and password-reset actions. The Firebase Web SDK identifiers are public build-time configuration in `client/apphosting.yaml`; no service-account key is included in the frontend. The Cloud Run service requires `FIREBASE_PROJECT_ID=agronomy-club` and uses its runtime service account to verify ID tokens through the Firebase Admin SDK.

Before enabling self-service member accounts, choose one supported identity path and implement it explicitly:

1. **Django authentication:** link member profiles to Django's authentication users and implement signup, login, password-reset, authorization, and rate limiting in Django.
2. **Firebase Authentication:** retain Firebase as the identity provider and implement Firebase token verification plus a reliable member-profile mapping in Django. This is the implemented staging approach.

Do not treat the current `agronomy_club.User` profile model as an authentication account. It stores member data but does not contain credentials or participate in Django's authentication system.

Before importing any production data, decide all of the following:

- Which legacy records are still needed: chapters, events, resources, alumni, quizzes, and media.
- Whether members will use new Django accounts, or whether Firebase Authentication will remain an identity provider.
- How existing members will be notified and how account recovery will work. Firebase password hashes cannot be copied into a different authentication system as usable passwords.
- Who signs off on a dry-run import and the final production cutover.

Do not export service-account keys, production credentials, or an unreviewed Firestore export into this repository. Use a restricted export location and a repeatable, reviewed import command instead.

## Delivery phases

### 1. Stabilise the repository

- Finish the approved design work and security remediation.
- Restore a reproducible frontend dependency install with `npm ci`.
- Replace production defaults in the environment examples with required-value validation.
- Pin production image or source revisions and remove automatic mutable-image updates.
- Add deployment-aware Django settings for secure cookies, proxy TLS headers, allowed hosts, CSRF trusted origins, static/media storage, and production logging.

**Exit condition:** the application passes its frontend and backend checks locally, no production secret is committed, and the release configuration does not depend on a self-managed production database volume.

### 2. Build the cloud deployment configuration

- Create an App Hosting configuration with `client/` as its application root and a non-production branch/environment for staging. The committed `firebase.json` targets the `agronomy-club-next-staging` backend; deploy it with `firebase deploy --only apphosting:agronomy-club-next-staging --project agronomy-club`.
- Adapt the Django container for Cloud Run: listen on the platform-provided port, run migrations as a controlled release step, and do not create an administrator account automatically at every boot.
- Create a Cloud SQL PostgreSQL instance and least-privilege database user in the same region as Cloud Run.
- Store `API_SECRET_KEY`, database credentials, and any administrator bootstrap secret in Secret Manager; grant each runtime service only the access it requires.
- Configure Cloud Storage for Django static files and media, with a backup and retention policy for the database and uploads.

**Exit condition:** a staging site is reachable on a temporary Firebase/App Hosting domain and communicates only with the staging API and database.

### Django Cloud Run release contract

The API container starts the Django development server only when `APP_ENV=DEVELOPMENT`. A managed deployment must set `APP_ENV=PRODUCTION`; the container then starts Gunicorn on Cloud Run's `PORT` (default `8080`). Production startup deliberately does not wait for PostgreSQL, apply migrations, collect static files, or create a superuser. Run migrations as a separate, recorded Cloud Run Job after each release; create staff users through a separate one-off administrative command.

Production settings require non-empty values for `API_SECRET_KEY`, `FRONTEND_URL`, `API_ALLOWED_HOSTS`, and all `POSTGRES_*` connection settings. Cloud Run must provide the database password and Django secret from Secret Manager. The deployment uses Cloud Run's HTTPS proxy headers to enforce HTTPS, secure Django session/CSRF cookies, HSTS, exact CORS origins, and exact allowed hosts.

### 3. Verify staging

- Run Django migrations against the staging database.
- Create a restricted administrator account and test Django admin over HTTPS.
- Smoke-test public pages, API reads, image uploads, downloads, CORS/CSRF behavior, error pages, and cache headers.
- Run a backup and restore rehearsal for PostgreSQL and uploaded media.
- Set billing budgets and alert thresholds before production traffic is enabled.

**Exit condition:** the owner accepts the staging site and rollback procedure.

### 4. Migrate and release

- Run the reviewed, one-time Firestore importer through a production Cloud Run Job using Application Default Credentials; it reads only `users/{uid}` and reports aggregate counts without exporting member data.
- Reconcile record counts and a sample of key content with the source system.
- Create the production Firebase Hosting frontend, Cloud Run API, Cloud SQL database, secrets, and storage using the same configuration validated in staging.
- Add `www.agronomyclub.org` to Firebase and verify its certificate and redirect from the apex domain.
- Perform the final content import, deploy a pinned release revision, and monitor logs, errors, database health, and costs during the cutover window.

**Exit condition:** the custom domain serves the new site, monitoring is active, and the former deployment remains available long enough for a measured rollback if required.

## Release and rollback policy

- Use `main` only for releases that have passed pull-request checks and staging verification.
- Record the frontend commit, API image digest or revision, database migration version, and deployment timestamp for every production rollout.
- Roll back frontend and Cloud Run traffic to the previous healthy revision first. Do not roll back database migrations blindly; use a reviewed forward repair unless a migration was explicitly written as reversible.
- Keep the old Firebase deployment untouched until the new production site is accepted and a tested rollback window has elapsed.

## Access needed before implementation

The implementation phase needs access granted through normal owner accounts, not copied credentials:

- Firebase project `agronomy-club` with permission to administer App Hosting and custom domains.
- The associated Google Cloud project with permission to manage Cloud Run, Cloud SQL, Cloud Storage, Secret Manager, IAM, budgets, and logging.
- DNS access for `agronomyclub.org` and `www.agronomyclub.org` (currently documented as GoDaddy, and possibly Cloudflare if its proxy remains in use).
- Administrator access to `gtalckmin/agronomy-club-next` so GitHub can be connected to App Hosting and deployment status can be checked.

## Authoritative references

- [Firebase App Hosting overview](https://firebase.google.com/docs/app-hosting)
- [Firebase App Hosting configuration](https://firebase.google.com/docs/app-hosting/configure)
- [Firebase Hosting rewrites to Cloud Run](https://firebase.google.com/docs/hosting/full-config)
- [Google Cloud: running Django on Cloud Run](https://cloud.google.com/python/django/run)

These references were checked on 19 September 2026. Cloud product regions, prices, and quotas can change; select the final region and configure budget alerts when creating the staging environment.
