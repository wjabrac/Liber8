#!/bin/bash
curl -s http://127.0.0.1:8080/healthz
echo ""
curl -X POST -H 'Content-Type: application/json' -d '{"task": "ping"}' -s http://127.0.0.1:8080/v1/runs
echo ""
