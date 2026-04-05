# Secrets and Config

## Split of Responsibility

- checked-in files hold non-secret defaults and operator examples
- environment variables hold environment-specific overrides
- real secrets stay outside the repo

## Current Repository Files

- `.env.example`: non-secret local example values
- `src/cognition/config.py`: engine runtime settings
- `src/service/config.py`: service/API runtime settings

## Local Development

Local development may use a `.env` file that is not committed.

Typical values include:

- `LIBR8_COGNITION_BACKEND`
- `LIBR8_STORAGE_DIR`
- `LIBR8_SERVICE_HOST`
- `LIBR8_SERVICE_PORT`
- `LIBR8_POSTGRES_DSN`
- `LIBR8_REQUIRE_ISOLATION_FOR_WRITES`
- `LIBR8_EXECUTION_ISOLATION_BACKEND`

## Production Expectation

Production should inject configuration through:

- system environment variables
- mounted secret files translated into environment variables at startup
- a secret manager wired by the deployment environment

## Do Not Store In Repo

- database credentials
- API keys
- service account tokens
- VM or Hyper-V credentials
- an approval bypass tokens

## Local-First Authentication Policy

LIBR8 implements a "Local-First" security model to balance ease of use with production safety:

1. **Loopback Access**: By default, if the service is bound to `127.0.0.1`, `localhost`, or `::1`, no API key is required.
2. **Explicit Key**: If `LIBR8_API_KEY` is set in the environment or `.env` file, it is **always** enforced for protected routes via the `X-API-Key` HTTP header.
3. **Non-Loopback Protection**: If the service binds to a public or non-loopback IP (e.g., `0.0.0.0`) and no API key is configured, access is **denied** by default to prevent accidental exposure.
4. **Unsafe Override**: Non-loopback access without a key can be explicitly enabled by setting `LIBR8_ALLOW_UNAUTHENTICATED_NON_LOOPBACK=True`.
5. **Public Endpoints**: `/healthz` and `/readyz` are always public and do not require authentication.

