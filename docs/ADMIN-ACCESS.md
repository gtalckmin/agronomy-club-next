# Permanent Django Admin access

## Approved public address

The permanent Django Admin address is:

```text
https://admin.agronomyclub.org/admin/
```

**Provisioning status:** pending. As of 19 September 2026, the `admin` DNS name has no record and `agronomyclub.org` is not verified for a Cloud Run domain mapping in project `agronomy-club`.

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

1. Verify ownership of the base domain `agronomyclub.org` in Google Search Console using the Google account that administers project `agronomy-club`.
2. Create the `admin.agronomyclub.org` Cloud Run domain mapping for `agronomy-club-api-prod` in `asia-southeast1`.
3. Add the mapping's generated DNS resource records at the domain's DNS provider and wait for certificate provisioning.
4. Route the hostname only to `agronomy-club-api-prod`; do not route it through Firebase Hosting.
5. Update the Cloud Run service environment so `API_ALLOWED_HOSTS` includes both the generated Cloud Run hostname and `admin.agronomyclub.org`.
6. Deploy the service configuration and verify `https://admin.agronomyclub.org/admin/` redirects unauthenticated visitors to `/admin/login/?next=/admin/`.
7. Sign in with a Django staff account, make one harmless read-only change, sign out, and confirm the next request returns to the login page.
8. Keep the public website origins in `FRONTEND_URL` and `FRONTEND_EXTRA_ORIGINS`. The admin hostname does not need browser CORS access because its Django session stays same-origin.

## Staff account recovery

The initial password for `agronomy-club@uwa.edu.au` is stored in Secret Manager. An authorised project owner can retrieve it from Cloud Shell:

```bash
gcloud secrets versions access latest \
  --secret=agronomy-club-admin-bootstrap-prod \
  --project=agronomy-club
```

Use the password only for the first sign-in, then change it immediately in Django Admin. If the password has already been changed and is unavailable, reset it through a one-off, recorded Django administrative job rather than weakening the sign-in configuration.
