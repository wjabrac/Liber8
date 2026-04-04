# Execution Environment

**Canonical Environment**: WSL (Windows Subsystem for Linux)
**Project Root**: `/home/willux/LIBR8_WORKSPACE/LIBR8`
**Interpreter**: `.venv/bin/python` from the project root

## Running Targeted Regressions

From the project root in WSL:

```bash
source .venv/bin/activate
python -m unittest \
  tests.test_regressions_steps_2_5 \
  tests.test_regressions_steps_6_9 \
  tests.test_cli_smoke \
  tests.test_contracts \
  tests.test_eventlog \
  tests.test_memory_adapter \
  tests.test_router_smoke
```

## Running the Full Test Suite

```bash
source .venv/bin/activate
python -m unittest discover tests
```

## Notes

- The Windows shell available in Codex can read the repository through UNC paths, but it cannot directly execute the Linux virtualenv launchers.
- Prefer WSL-native execution for Python test runs and artifact inspection.
- The current default entrypoint path uses the fallback backend.
