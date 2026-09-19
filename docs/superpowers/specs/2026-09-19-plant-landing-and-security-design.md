# Plant landing page and security hardening

## Objective

Create a fast, accessible Agronomy Club landing page with an image-led organic visual treatment, then harden the public API and production deployment before release.

> **Design decision update — 19 September 2026:** The owner explicitly removed the Three.js requirement after the initial concept was approved. The WebGL design below is superseded. The implemented landing page uses responsive static photography, semantic HTML, and CSS motion only; it ships no Three.js runtime, canvas, or WebGL dependency.

## Landing page

The homepage keeps all key information in semantic HTML. Responsive photography and CSS provide the visual layer, while the content column remains keyboard accessible and readable with images or motion disabled.

### Visual treatment

- A responsive, locally optimised hero image provides the organic plant visual.
- The visual decoration does not gate content or interaction.
- CSS transitions honour `prefers-reduced-motion` and do not depend on scroll listeners or animation loops.

### Layout and interaction

- The existing Agronomy Club title, mission, and sign-up/explore actions remain real HTML above the imagery.
- On wide screens, content is a left-side editorial column and the image occupies the right-side visual anchor. On mobile, the layout becomes a single-column content flow.
- The page uses a precise green, cream, and harvest-yellow design system already present in the project. No new decorative badges, fake metrics, or image text are introduced.

## Security changes

1. Replace public serializers with audience-specific serializers: public alumni and committee responses do not include personal email addresses. Chapter contact email remains public because it is the intentional club contact channel.
2. Bind Django and Next.js ports to loopback in production. Nginx is the only externally exposed service.
3. Remove Watchtower and mutable automatic image deployment. Production uses explicit, immutable image tags supplied in `.env.prod` and a documented manual update command.
4. Require production environment variables for Django secrets and database credentials. Production cannot silently fall back to development credentials.
5. Add production HTTPS, secure-cookie, HSTS, frame, content-type, referrer, and permissions-policy settings; pass the original protocol through Nginx.
6. Add upload size limits and validate quiz JSON upload content type and structure before it is retained.

## Deployment

The deployment remains Docker Compose on a Linux host. GitHub Actions builds immutable, SHA-tagged GHCR images. The deployer selects a tested SHA in `.env.prod`, runs the migration job, and updates the Compose stack. Nginx terminates TLS using certificates supplied by the selected host. DNS and certificate provider details remain deployment-host inputs; no live deployment occurs until those are provided.

## Validation

- Frontend: TypeScript, ESLint, build, browser checks at desktop and mobile widths, and reduced-motion behavior.
- Backend: Django tests for public serializer privacy, production setting validation, and file validation.
- Deployment: `docker compose config`, a reverse-proxy header check, and a manual image-tag release rehearsal.

## Constraints and risks

- The current local Docker installation cannot unpack the PostgreSQL image because of a host `unpigz`/zlib error. Local frontend verification remains available; full API and database checks require a functioning Docker environment.
- The repository lockfile is currently out of sync with the client package manifest. This should be repaired in the same pull request to restore `npm ci` and CI reproducibility.
