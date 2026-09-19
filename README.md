# Agronomy Club

The public website and member services for Agronomy Club. It is a full-stack application maintained from this repository and deployed as container images.

## What is here

- `client/` — Next.js 16 and React 19 frontend.
- `server/` — Django API, Django admin, and PostgreSQL models.
- `docker/` — development and production container definitions, plus Nginx configuration.
- `.github/workflows/` — frontend, backend, and container-image checks.

The main features are chapter profiles, events, resources, quizzes, alumni records, and member/chapter memberships. Detailed architecture and operational notes are in [docs/PROJECT.md](docs/PROJECT.md).

## Start developing

The recommended workflow is the Dev Container in VS Code. It provides the required Node, Python, Poetry, Docker, and database tooling.

For a local setup, copy the example environment files, start PostgreSQL, then run the API and frontend in separate terminals:

```bash
cp client/.env.example client/.env
cp server/.env.example server/.env

cd server
docker compose up -d
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver
```

```bash
cd client
npm ci
npm run dev
```

The frontend runs at `http://localhost:3000`; Django, its API, and its admin interface run at `http://localhost:8000`.

## Checks

```bash
cd client && npm run format:check && npm run lint && npm run typecheck
cd server && poetry run python manage.py test
```

## Production

Pushing to `main` builds and publishes frontend and backend images to GitHub Container Registry. The production Compose file is [docker-compose.prod.yml](docker-compose.prod.yml) and is configured for this fork's image names; configure a private `.env.prod` on the host from `.env.prod.example` before deploying.

## Repository relationships

This repository is a fork of [codersforcauses/agronomy-club](https://github.com/codersforcauses/agronomy-club). The former Firebase/Next.js site is preserved separately at [gtalckmin/Agronomy-Club](https://github.com/gtalckmin/Agronomy-Club); it is not the deployment source for this application.

See [AGENTS.md](AGENTS.md) for agent and contributor operating rules.
