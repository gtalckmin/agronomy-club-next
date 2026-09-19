# Working in this repository

## Purpose

Agronomy Club's active website codebase is a Next.js frontend, Django API, and PostgreSQL application. The previous Firebase site is a separate repository and is reference material only. Do not copy its credentials, Firebase configuration, or deployment files into this project.

## Code map

- `client/src/app/` contains page routes and their client components.
- `client/src/components/` contains reusable UI and feature components.
- `client/src/hooks/` contains API-facing React Query hooks.
- `client/src/lib/api.ts` creates the Axios client; `NEXT_PUBLIC_BACKEND_URL` controls its base URL.
- `server/agronomy_club/` owns models, serializers, views, routes, migrations, and Django-admin registrations.
- `server/api/` contains Django settings and top-level routes. API endpoints are under `/api/`; Django admin is `/admin/`.
- `docker-compose.yml` runs the development database. `docker-compose.prod.yml` composes PostgreSQL, API, frontend, Nginx, and Watchtower for a production host.

## Development rules

1. Keep frontend data access in the existing API client and hooks; do not embed service URLs in components.
2. When modifying a Django model, create and commit a migration. Do not edit existing migrations that may have been deployed.
3. Keep API serializers, views, and TypeScript consumers consistent when changing a resource shape.
4. Preserve responsive behaviour and the existing UI component system.
5. Never commit `.env`, `.env.prod`, database data, credentials, access tokens, or private keys. Update the relevant `.env.example` when a new non-secret setting is required.
6. Avoid changing CI/CD, Docker, or deployment files as incidental cleanup; these files define the production release path.

## Verify changes

Run the checks that cover the files changed:

```bash
cd client && npm run format:check && npm run lint && npm run typecheck
cd server && poetry run python manage.py test
```

For model or API changes, also apply migrations against a local PostgreSQL database and exercise the affected endpoint. For client changes, run the page locally at port 3000.

## Git and release workflow

- Develop in a feature branch and open a pull request into `main`.
- GitHub Actions checks formatting, linting, TypeScript, Python linting, Django migrations, and backend tests.
- A push to `main` publishes multi-architecture frontend and server images to GHCR. The deployment host's Watchtower service updates containers from those images.
- Keep `origin` pointed to this fork. Add `upstream` pointing to `https://github.com/codersforcauses/agronomy-club.git` when synchronising changes from Coders for Causes.
