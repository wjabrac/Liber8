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
- approval bypass tokens
