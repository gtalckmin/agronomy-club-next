# Project guide

## Status and ownership

This is the active, modernised Agronomy Club website. It replaces the older Firebase-hosted Next.js site formerly maintained at `gtalckmin/Agronomy-Club`. The two repositories have incompatible application architectures and deployment paths. Treat the former site as a content and business-reference source, not as a branch to merge.

The maintained fork is `gtalckmin/agronomy-club-next`; its upstream is `codersforcauses/agronomy-club`. Keep upstream changes reviewable by fetching and merging them through a normal branch/PR workflow.

Managed production is live on Firebase Hosting, Cloud Run, and Cloud SQL. The container/Nginx architecture below remains useful for local and self-managed deployments, but it is not the active production path. Read [HANDOVER.md](HANDOVER.md) before releasing or administering production.

## Architecture

```text
Browser
  │
  ▼
Next.js client (client/, port 3000) ─── Axios ───► Django API (server/, port 8081 in Compose)
  │                                                     │
  └──────────────────── Nginx in production ───────────┤
                                                        ▼
                                                  PostgreSQL 16
```

Next.js renders public content and uses React Query hooks to fetch data. Firebase Authentication owns member email/password identity; the browser sends Firebase ID tokens to Django for member-profile requests. Django owns the application API, member roles, administration interface, validation, migrations, media, and persistence. PostgreSQL stores club data. Nginx fronts the frontend, API, and static assets in production.

## Domain model

| Area      | Django model                  | Notes                                                                           |
| --------- | ----------------------------- | ------------------------------------------------------------------------------- |
| Chapters  | `Chapter`                     | Club name, branding, location, email, and events/resources relation.            |
| Events    | `Event`                       | Chapter-owned title, description, date, location, thumbnail, and optional link. |
| Resources | `Resource`, `ResourceTypeTag` | Public/private chapter resources with filters.                                  |
| Quizzes   | `Quiz`                        | Chapter-owned JSON quiz uploads, with public visibility.                        |
| People    | `User`, `ChapterMembership`   | Alumni/member profile, global role, chapter role, and committee position.       |

## Local environment

Create local environment files from the examples and keep them untracked:

```bash
cp client/.env.example client/.env
cp server/.env.example server/.env
```

Set `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` in the client environment when running locally. The server environment supplies Django's secret key, allowed hosts, database credentials, frontend URL, and optional superuser values. Start PostgreSQL with `cd server && docker compose up -d`; then run migrations before using the API.

## Test and quality gates

The repository checks frontend Prettier, ESLint, and TypeScript; backend Flake8; and Django migrations/tests against PostgreSQL. GitHub Actions runs these workflows for pull requests and pushes to `main`.

Use `npm ci`, rather than `npm install`, for reproducible frontend dependency installation. Poetry manages Python dependencies through `server/pyproject.toml` and `server/poetry.lock`.

## Self-managed container deployment model

The deployment workflow builds both client and server images on each push to `main`. Images are published to this fork's GHCR namespace. The checked-in Compose configuration is for a self-managed host, where it starts PostgreSQL, the API, frontend, and Nginx from recorded image digests.

Before the first production deployment:

1. Create a strong, unique `.env.prod` from `.env.prod.example`; do not commit it. Set `CLIENT_IMAGE` and `SERVER_IMAGE` to the release digests published by GHCR.
2. Configure the production domain in `API_ALLOWED_HOSTS`, `FRONTEND_URL`, and the frontend backend URL. Set `FIREBASE_PROJECT_ID=agronomy-club` when Firebase member authentication is enabled.
3. Provision `opt/tls/fullchain.pem` and `opt/tls/privkey.pem`, then verify the Nginx HTTPS configuration and domain routing.
4. Run `docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm migrate` before each release that contains Django migrations, then start the application with `docker compose --env-file .env.prod -f docker-compose.prod.yml up -d`.
5. Create an administrator account on the production environment.

This is not the recommended long-term production architecture. The approved direction is to retain the Agronomy Club Firebase/Google Cloud estate, serve the Next.js client with Firebase App Hosting, deploy the Django API to Cloud Run, and use Cloud SQL for PostgreSQL. The migration approach, routing decision, verification steps, and required account access are in [DEPLOYMENT-STRATEGY.md](DEPLOYMENT-STRATEGY.md).

## Legacy migration boundaries

The older repository contains Firebase Authentication/Firestore data and a local service-account key that was tracked historically. Rotate that key and any related Firebase secrets before sharing or reusing the older repository. Data migration from Firebase into PostgreSQL needs a separately reviewed export, transformation, and import plan; no credentials or production data should be moved through Git.

The active site uses Firebase Authentication only for identity. It does not read or write the legacy Firestore `users` collection. A verified Firebase UID is stored against each Cloud SQL member profile, allowing Django Admin to manage member roles and chapter memberships without storing passwords.

## Member and staff access

Firebase member sign-in and Django administration are separate access paths. A member who registers through `/sign-up` receives a Firebase identity and a Django member profile with the global role `user`; that does not create a Django staff account and does not expose chapter-management controls in the public site.

Staff manage chapters, events, memberships, committee positions, and member roles through Django Admin at `/admin/` on the API host. After a staff user signs in, select **Chapters → Add chapter** to create a chapter, then use **Users** and **Chapter memberships** to assign members and committee roles.

Provision staff accounts deliberately. On a self-managed Compose host, run the following interactively from the release directory:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm --entrypoint python server manage.py createsuperuser
```

For Cloud Run, use a recorded one-off administrative job with the same `createsuperuser` command and the service's existing database and secret configuration. Do not promote a Firebase user to Django staff status automatically, and never place administrator credentials in Git or frontend configuration.
