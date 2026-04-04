#!/bin/bash
set -e

# Port for the live test
PORT=8099
STORAGE_DIR=$(mktemp -d)

# Cleanup on exit
trap 'echo "Cleaning up..."; kill $SERVICE_PID 2>/dev/null || true; rm -rf $STORAGE_DIR' EXIT

echo "Starting LIBR8 service on port $PORT with storage $STORAGE_DIR..."
python main.py serve --port $PORT --storage-dir "$STORAGE_DIR" > service.log 2>&1 &
SERVICE_PID=$!

echo "Waiting for service to be ready..."
MAX_RETRIES=10
RETRY_COUNT=0
until curl -s http://127.0.0.1:$PORT/healthz > /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Service failed to start within timeout. service.log:"
        cat service.log
        exit 1
    fi
    sleep 1
done

echo "Service is ready. Running healthcheck..."
curl -s http://127.0.0.1:$PORT/healthz
echo ""

echo "Submitting a test task..."
curl -X POST -H 'Content-Type: application/json' -d '{"task": "ping"}' -s http://127.0.0.1:$PORT/v1/runs
echo ""

echo "Live test completed successfully."
