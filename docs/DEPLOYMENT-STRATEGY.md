# Firebase and Google Cloud deployment strategy

**Status:** The isolated App Hosting staging backend is configured for a local-source rollout. The document records the production architecture; it does not authorise a custom-domain cutover or production data migration.

## Why this changes the deployment model

The former Agronomy Club site was deployed from the separate `gtalckmin/Agronomy-Club` repository to the Firebase project `agronomy-club`. Its documented public Hosting address was `https://agronomy-club.web.app`, and its intended public domain was `www.agronomyclub.org`.

This repository has a different application architecture:

```text
Next.js client  →  Django API  →  PostgreSQL
```

It cannot be deployed as the former static/Firebase-Functions application without changing its backend and data model. The checked-in production Compose file is useful for local and self-managed-host deployments, but it does not define a complete managed-cloud deployment: it has no configured public hostname, certificate source, hosted database, or persistent media store.

The recommended direction is to keep the established Firebase and Google Cloud estate, while moving this application to managed services that suit its architecture.

## Recommended target architecture

```text
Visitors
   │
   ▼
www.agronomyclub.org
   │
   ▼
Firebase App Hosting
   └── Next.js application (`client/`)
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

Firebase App Hosting is the recommended frontend delivery path because it has managed Next.js support and GitHub-connected rollouts. It builds the client in Google Cloud, runs it on Cloud Run, and delivers it through Cloud CDN. Cloud Run is the appropriate managed runtime for the existing Django container, while Cloud SQL provides the PostgreSQL database that Django expects.

This separates frontend and API deployments while avoiding a manually maintained virtual machine, a Docker auto-updater, and hand-managed TLS certificates.

## Current staging deployment

On 19 September 2026, the Next.js client was deployed from local source to this isolated Firebase App Hosting backend:

- **Backend:** `agronomy-club-next-staging`
- **Region:** `asia-southeast1`
- **Staging URL:** `https://agronomy-club-next-staging--agronomy-club.asia-southeast1.hosted.app`
- **Release source:** the `feat/plant-landing-security` branch, including commit `50c6f76`

The deployment passed the production build, TypeScript, ESLint, Prettier, and production dependency-audit checks before the Firebase rollout. Firebase reported the rollout as successful, and the public staging URL returned HTTP 200 with the new landing page.

This staging deployment does **not** replace the existing `agronomy-club.web.app` Firebase Hosting site or either public custom domain. It deploys the Next.js client only. The Django API, Cloud SQL database, media storage, and data migration remain separate work; pages that depend on live club data must not be treated as production-ready until that API is deployed and verified.

## Domain and routing

The production domain should remain `www.agronomyclub.org`; redirect the apex `agronomyclub.org` to it. Connect the custom domain through Firebase after a staging rollout succeeds.

The client should call the API through a single production HTTPS origin chosen during implementation:

1. **Preferred initially: `api.agronomyclub.org`.** Point this subdomain directly at the Cloud Run Django service. Set `NEXT_PUBLIC_BACKEND_URL` to `https://api.agronomyclub.org/api`, set Django `FRONTEND_URL` to `https://www.agronomyclub.org`, and restrict `API_ALLOWED_HOSTS` and CORS to the exact production hosts.
2. **Optional later: same-origin `/api` routing.** Firebase Hosting can rewrite requests to Cloud Run. Before adopting that layout, verify Django admin, CSRF protection, cookies, caching, and any authenticated request flows end to end. Firebase Hosting documents that cookies are generally stripped when Hosting proxies to Cloud Run, so this must not be assumed safe for session-based features.

Use the first option for the first rollout. It gives the API an explicit boundary and avoids introducing a proxy behavior before its authentication effects have been tested.

## Data and identity boundaries

The legacy project used Firebase Authentication and Firestore. This application has a Django-owned relational data model and a PostgreSQL database. Treat data and identity migration as a separate, gated project.

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

### 3. Verify staging

- Run Django migrations against the staging database.
- Create a restricted administrator account and test Django admin over HTTPS.
- Smoke-test public pages, API reads, image uploads, downloads, CORS/CSRF behavior, error pages, and cache headers.
- Run a backup and restore rehearsal for PostgreSQL and uploaded media.
- Set billing budgets and alert thresholds before production traffic is enabled.

**Exit condition:** the owner accepts the staging site and rollback procedure.

### 4. Migrate and release

- Take a read-only legacy export, transform it outside Git, and perform a staged import.
- Reconcile record counts and a sample of key content with the source system.
- Create the production App Hosting backend, Cloud Run API, Cloud SQL database, secrets, and storage using the same configuration validated in staging.
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
