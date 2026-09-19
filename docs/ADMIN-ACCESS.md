# Permanent Django Admin access

## Approved public address

The permanent Django Admin address is:

```text
https://admin.agronomyclub.org/admin/
```

It is a dedicated administrative subdomain, separate from the public website at `www.agronomyclub.au` and the Firebase Hosting fallback at `agronomy-club.web.app`.

Do not route Django Admin through `www.agronomyclub.org/admin/`. The public site is served by Firebase Hosting, while Django Admin uses session and CSRF cookies. Sending that session-based application through the public Hosting route risks incorrect proxy and cookie behaviour.

## Target service

`admin.agronomyclub.org` must terminate TLS and route HTTPS traffic directly to the production Django Cloud Run service:

```text
agronomy-club-api-prod
https://agronomy-club-api-prod-869412139245.asia-southeast1.run.app
```

The generated Cloud Run URL remains an operational fallback only. Staff should use the permanent `admin.agronomyclub.org/admin/` address once DNS and certificate provisioning are complete.

## Provisioning checklist

1. Configure the `admin.agronomyclub.org` DNS record with the chosen Google Cloud HTTPS/custom-domain routing service.
2. Attach a managed TLS certificate for `admin.agronomyclub.org` and wait for it to become active.
3. Route the hostname only to `agronomy-club-api-prod`; do not route it through Firebase Hosting.
4. Update the Cloud Run service environment so `API_ALLOWED_HOSTS` includes both the generated Cloud Run hostname and `admin.agronomyclub.org`.
5. Deploy the service configuration and verify `https://admin.agronomyclub.org/admin/` redirects unauthenticated visitors to `/admin/login/?next=/admin/`.
6. Sign in with a Django staff account, make one harmless read-only change, sign out, and confirm the next request returns to the login page.
7. Keep the public website origins in `FRONTEND_URL` and `FRONTEND_EXTRA_ORIGINS`. The admin hostname does not need browser CORS access because its Django session stays same-origin.

## Staff account recovery

The initial password for `agronomy-club@uwa.edu.au` is stored in Secret Manager. An authorised project owner can retrieve it from Cloud Shell:

```bash
gcloud secrets versions access latest \
  --secret=agronomy-club-admin-bootstrap-prod \
  --project=agronomy-club
```

Use the password only for the first sign-in, then change it immediately in Django Admin. If the password has already been changed and is unavailable, reset it through a one-off, recorded Django administrative job rather than weakening the sign-in configuration.
