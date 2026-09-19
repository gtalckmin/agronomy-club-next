# Plant landing page and security hardening

## Objective

Create a fast, accessible Agronomy Club landing page with a procedural low-poly plant that grows as visitors scroll, then harden the public API and production deployment before release.

## Landing page

The homepage keeps all key information in semantic HTML, with a fixed WebGL canvas used only as the visual layer. The content column remains keyboard accessible and readable when WebGL is unavailable or reduced motion is enabled.

### Scene

- A Three.js scene mounts in a client-only `PlantScene` component.
- A seedling starts at the base of the viewport. Scroll progress drives a clamped growth value from 0 to 1; a short initial interpolation avoids a blank first render.
- The plant is generated from a small set of low-poly cylinders and tapered branch segments. Each branch has a configured growth threshold and its leaves use a delayed local interpolation so they appear after their supporting stem.
- Leaves use simple faceted geometry and green `MeshStandardMaterial`; stems use a darker, rougher material. Ambient and directional lighting create soft depth without textures or remote asset requests.
- The renderer uses device-pixel-ratio limits, a single requestAnimationFrame loop, resize-aware perspective camera, paused rendering when offscreen, and disposal of geometries, materials, renderer, and listeners during unmount.
- The scene observes `prefers-reduced-motion`; it renders a complete, still plant and does not bind growth to scroll in that mode.

### Layout and interaction

- The existing Agronomy Club title, mission, and sign-up/explore actions remain real HTML above the canvas.
- On wide screens, content is a left-side editorial column and the plant occupies the right-side visual anchor. On mobile, the canvas becomes a restrained background behind a single-column content flow.
- A lightweight loading state covers only the canvas until the renderer has produced its first frame.
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

- Frontend: TypeScript, ESLint, build, browser checks at desktop and mobile widths, reduced-motion behavior, scroll-growth behavior, and no-WebGL fallback.
- Backend: Django tests for public serializer privacy, production setting validation, and file validation.
- Deployment: `docker compose config`, a reverse-proxy header check, and a manual image-tag release rehearsal.

## Constraints and risks

- The current local Docker installation cannot unpack the PostgreSQL image because of a host `unpigz`/zlib error. Local frontend verification remains available; full API and database checks require a functioning Docker environment.
- The repository lockfile is currently out of sync with the client package manifest. This should be repaired in the same pull request to restore `npm ci` and CI reproducibility.
