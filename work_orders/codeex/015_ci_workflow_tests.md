# CX-015 CI workflow: run tests on push/PR

Objective
Add GitHub Actions workflow to run unit tests.

Scope
- Add .github/workflows/ci.yml running:
  - python (minimum one version)
  - python -m unittest discover -s tests -v

Acceptance criteria
- CI runs and passes on default branch for current tests.
