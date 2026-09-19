# Plant Landing and Security Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the approved image-led landing page and security hardening.

> **Status:** Tasks 1–3 recorded the original Three.js concept. They were superseded on 19 September 2026 when the owner directed that Three.js be removed. The released landing page uses responsive static imagery and CSS; no WebGL scene is an acceptance requirement. Tasks 4–6 remain the historical security and deployment checklist.

**Architecture:** The homepage uses responsive static imagery and CSS. Django uses public serializers without personal emails; production Compose and Django settings require explicit secure configuration.

**Tech Stack:** Next.js, React, TypeScript, Tailwind CSS, Django, Docker Compose, Nginx.

**Spec:** `docs/superpowers/specs/2026-09-19-plant-landing-and-security-design.md`

## Global Constraints

- Keep all copy and actions in accessible HTML above the canvas.
- Use procedural low-poly geometry only and honour reduced motion.
- Never return personal member email fields from public API endpoints.
- Require explicit production secrets, immutable image tags, and loopback-only internal ports.

### Task 1: Synchronise frontend dependencies

**Files:** Modify `client/package.json`, `client/package-lock.json`.

- [ ] Install `three` and `@types/three` with `npm install three @types/three`.
- [ ] Run `rm -rf node_modules && npm ci`; it must finish without a lockfile mismatch.
- [ ] Commit with `chore: repair client lockfile and add three`.

### Task 2: Add the plant scene

**Files:** Create `client/src/components/plant-scene.tsx`; modify `client/src/app/page.tsx`.

- [ ] Define `PlantSceneProps { growth: number; reducedMotion: boolean }`.
- [ ] Build low-segment `MeshStandardMaterial` stems, branches, and leaf meshes, each with a `start`, `end`, and delayed-leaf threshold.
- [ ] Create one scene, camera, renderer, ambient light, directional light, and capped device pixel ratio in `useEffect`.
- [ ] Animate node scale from scroll growth via one requestAnimationFrame loop; set full growth for reduced-motion users.
- [ ] Use `ResizeObserver` to update camera aspect and renderer size.
- [ ] On cleanup cancel animation, disconnect observer, remove canvas, dispose materials/geometries, and dispose renderer.
- [ ] Add a canvas loading state and retain interactive content in a higher-z-index semantic region.
- [ ] Run `npm run lint`, `npm run typecheck`, and `npm run build`; verify desktop, mobile, scroll, and reduced-motion states.
- [ ] Commit with `feat: add scroll-grown low-poly plant landing scene`.

### Task 3: Apply layout and accessibility refinements

**Files:** Modify `client/src/app/page.tsx`, `client/src/styles/globals.css`, `client/src/components/ui/navbar.tsx`, `client/src/components/ui/footer.tsx`.

- [ ] Use a wide-screen editorial content column beside the scene and a single-column mobile layout with capped canvas height.
- [ ] Add harvest-yellow `:focus-visible` treatment and a global reduced-motion transition rule.
- [ ] Verify title wrapping, CTA contrast, mobile navigation, footer spacing, no canvas overlap, and keyboard navigation.
- [ ] Commit with `feat: refine Agronomy Club landing layout`.

### Task 4: Remove public personal-email disclosure

**Files:** Modify `server/agronomy_club/serializers.py`, `server/agronomy_club/tests.py`.

- [ ] Add failing API tests asserting that `/api/alumni/` and `/api/chapters/<id>/?committee=exec` return no `email` field.
- [ ] Remove personal `email` from alumni and committee serializers while preserving `Chapter.email` as public contact information.
- [ ] Run `poetry run python manage.py test agronomy_club.tests` and commit with `fix: remove personal emails from public API responses`.

### Task 5: Harden production deployment

**Files:** Modify `server/api/settings.py`, `docker/nginx/custom.conf`, `docker-compose.prod.yml`, `.env.prod.example`, `README.md`.

- [ ] Add a `required_env(name: str) -> str` helper and require the Django secret and database credentials outside development.
- [ ] Set production SSL proxy, HSTS, secure-cookie, content-type, frame, referrer, and permissions-policy settings.
- [ ] Forward `X-Forwarded-Proto` through Nginx and configure security headers.
- [ ] Bind Django and Next.js to `127.0.0.1`; remove Watchtower and mutable `latest` tags.
- [ ] Add explicit client/server SHA image tag variables to `.env.prod.example` and document manual `pull`/`up -d` release steps.
- [ ] Run `docker compose -f docker-compose.prod.yml --env-file .env.prod.example config` and backend tests; record the known Docker zlib limitation if it blocks integration tests.
- [ ] Commit with `fix: harden production deployment configuration`.

### Task 6: Publish and verify

**Files:** Modify `docs/PROJECT.md`.

- [ ] Run `npm ci`, format check, lint, typecheck, build, and Django tests.
- [ ] Test the deployed client visually at desktop and mobile dimensions; compare with the approved design spec.
- [ ] Push to `origin/main`, confirm Actions results, select immutable GHCR SHA tags, and add them to the production host `.env.prod`.
- [ ] Commit deployment documentation with `docs: add secure deployment checklist`.

## Plan self-review

- All approved visual, privacy, deployment, and verification requirements have a concrete task.
- Component and environment interfaces are defined before use.
