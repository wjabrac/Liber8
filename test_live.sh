#!/bin/bash
set -euo pipefail

# Isolated resources for this test run
PORT=$(python - <<'PY'
import socket
with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    print(s.getsockname()[1])
PY
)
STORAGE_DIR=$(mktemp -d)
SERVICE_LOG=$(mktemp)
SERVICE_PID=""

cleanup() {
    echo "Cleaning up..."
    if [ -n "$SERVICE_PID" ] && kill -0 "$SERVICE_PID" 2>/dev/null; then
        kill "$SERVICE_PID" 2>/dev/null || true
        wait "$SERVICE_PID" 2>/dev/null || true
    fi
    rm -rf "$STORAGE_DIR"
    rm -f "$SERVICE_LOG"
}
trap cleanup EXIT

echo "Starting LIBR8 service on port $PORT with storage $STORAGE_DIR..."
python main.py serve --port "$PORT" --storage-dir "$STORAGE_DIR" > "$SERVICE_LOG" 2>&1 &
SERVICE_PID=$!

echo "Waiting for service to be ready..."
MAX_RETRIES=10
for ((attempt=1; attempt<=MAX_RETRIES; attempt++)); do
    if curl -fsS "http://127.0.0.1:$PORT/healthz" > /dev/null 2>&1; then
        break
    fi

    if ! kill -0 "$SERVICE_PID" 2>/dev/null; then
        echo "Service exited before becoming ready. service.log:"
        cat "$SERVICE_LOG"
        exit 1
    fi

    if [ "$attempt" -eq "$MAX_RETRIES" ]; then
        echo "Service failed to start within timeout. service.log:"
        cat "$SERVICE_LOG"
        exit 1
    fi

    sleep 1
done

echo "Service is ready. Running healthcheck..."
curl -fsS "http://127.0.0.1:$PORT/healthz"
echo ""

echo "Submitting a test task..."
curl -fsS -X POST -H 'Content-Type: application/json' -d '{"task": "ping"}' "http://127.0.0.1:$PORT/v1/runs"
echo ""

echo "Live test completed successfully."
