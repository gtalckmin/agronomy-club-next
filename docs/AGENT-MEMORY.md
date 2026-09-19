# Agronomy Club agent memory

This is concise persistent context for future operators and coding agents. Read [HANDOVER.md](HANDOVER.md) for procedures and background.

## Current facts

- Active repository: `gtalckmin/agronomy-club-next`; upstream: `codersforcauses/agronomy-club`.
- Current working branch: `feat/plant-landing-security`; `f906d16` fixed the Chapters detail hook-order failure and `8946960` removed the pagination URL feedback loop. Pagination must read `?page=` directly; do not add a router effect that writes the same URL back to the browser.
- Public production: `https://www.agronomyclub.au`; Firebase Hosting fallback: `https://agronomy-club.web.app`.
- Hosting serves `client/out`; build with `npm run build` from `client/`, then use `firebase deploy --only hosting --project agronomy-club --non-interactive`.
- Production Django runs in Cloud Run service `agronomy-club-api-prod` in `asia-southeast1`; data is Cloud SQL PostgreSQL instance `agronomy-club-postgres-prod`.
- The compiled client calls `https://agronomy-club-api-prod-869412139245.asia-southeast1.run.app/api`. Cloud Run currently reports a different generated service URL. Both work; change hosts only in a coordinated frontend/API release.
- API CORS permits `https://agronomy-club.web.app` and `https://www.agronomyclub.au`.
- One UWA chapter exists in production. Legacy Firestore `users` have **not** been imported. The importer must remain dry-run-only until separately approved.
- Firebase Authentication is member identity. Django Admin is separate staff access. The direct Admin fallback is the production Cloud Run host `/admin/`.
- `admin.agronomyclub.org` is planned, not provisioned. Do not assume any `.org` public-domain configuration is live.
- Production secrets stay in Secret Manager. Never request, print, commit, or expose their values. The bootstrap-admin password retrieval command is in `ADMIN-ACCESS.md`.

## Always do before production work

1. Read `HANDOVER.md` and `PRODUCTION-RELEASE.md`.
2. Keep credentials and exports outside Git.
3. Run client tests, lint, typecheck, and production build for frontend work; run Django tests and migrations for API/model work.
4. Deploy frontend and backend separately; a Git push does not deploy the managed production site.
5. Smoke-test both `web.app` and `www.agronomyclub.au`, including `/chapters?page=1` → **View** → `?chapter=1`.
6. Record production revision, result, and rollback information.
