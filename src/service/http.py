"""HTTP transport for the LIBR8 service."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Tuple

from src.service.app import Libr8Service
from src.service.migrations import list_postgres_migrations
from src.service.schema import service_endpoint_catalog

MAX_REQUEST_BODY_BYTES = 1_048_576


def dispatch_http_request(
    service: Libr8Service, 
    method: str, 
    path: str, 
    body: Dict[str, Any] | None = None,
    headers: Dict[str, str] | None = None
) -> Tuple[int, Dict[str, Any]]:
    body = body or {}
    headers = headers or {}
    
    # Auth bypass for health checks
    if method == "GET" and path in {"/healthz", "/readyz"}:
        pass
    elif service.config.requires_auth:
        request_key = headers.get("X-API-Key") or headers.get("x-api-key")
        if service.config.api_key:
            if request_key != service.config.api_key:
                return 401, {"error": "unauthorized"}
        else:
            # Requires auth because non-loopback, but no key is even configured
            return 403, {"error": "forbidden - non-loopback binding requires LIBR8_API_KEY"}

    if method == "GET" and path == "/healthz":
        return 200, service.health()
    if method == "GET" and path == "/readyz":
        health = service.health()
        return (200 if health.get("status") == "ok" else 503), health
    if method == "GET" and path == "/retention/preview":
        return 200, service.retention_preview()
    if method == "GET" and path == "/admin/migrations":
        return 200, {"postgres": [item.to_dict() for item in list_postgres_migrations()]}
    if method == "GET" and path == "/admin/snapshot":
        return 200, service.admin_snapshot()
    if method == "GET" and path == "/admin/schema":
        return 200, {"endpoints": service_endpoint_catalog()}
    if method == "GET" and path == "/v1/approvals":
        return 200, service.list_pending_approvals()
    if method == "POST" and path == "/v1/approvals":
        task_id = str(body.get("task_id", "")).strip()
        scope = str(body.get("scope", "")).strip()
        reason = str(body.get("reason", "")).strip()
        if not task_id or not scope or not reason:
            return 400, {"error": "task_id, scope, and reason are required"}
        return 201, service.submit_approval(task_id, scope, reason)
    if method == "POST" and path.startswith("/v1/approvals/") and path.endswith("/resolve"):
        request_id = path.split("/")[3]
        status = str(body.get("status", "")).strip()
        if status not in {"approved", "rejected"}:
            return 400, {"error": "status must be approved or rejected"}
        resolved = service.resolve_approval(request_id, status)
        if resolved is None:
            return 404, {"error": "approval not found"}
        return 200, resolved
    if method == "GET" and path == "/v1/exports":
        return 200, service.list_export_jobs()
    if method == "POST" and path == "/v1/exports":
        run_id = str(body.get("run_id", "")).strip()
        job_kind = str(body.get("job_kind", "markdown_report")).strip() or "markdown_report"
        if not run_id:
            return 400, {"error": "run_id is required"}
        return 201, service.submit_export_job(run_id, job_kind)
    if method == "POST" and path.startswith("/v1/exports/") and path.endswith("/process"):
        job_id = path.split("/")[3]
        processed = service.process_export_job(job_id)
        if processed is None:
            return 404, {"error": "export job not found"}
        return 200, processed
    if method == "POST" and path == "/v1/runs":
        task = str(body.get("task", "")).strip()
        if not task:
            return 400, {"error": "task is required"}
        return 202, service.submit_task(task)
    if method == "POST" and path == "/v1/runs/async":
        task = str(body.get("task", "")).strip()
        if not task:
            return 400, {"error": "task is required"}
        return 202, service.submit_task_async(task)
    if method == "GET" and path.startswith("/v1/runs/"):
        task_id = path.rsplit("/", 1)[-1]
        record = service.get_task(task_id)
        if record is None:
            return 404, {"error": "task not found"}
        return 200, record
    return 404, {"error": "not found"}


def build_handler_class(service: Libr8Service):
    class Libr8RequestHandler(BaseHTTPRequestHandler):
        def _write_json_response(self, status: int, payload: Dict[str, Any]) -> None:
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self) -> None:
            self._handle("GET")

        def do_POST(self) -> None:
            self._handle("POST")

        def _handle(self, method: str) -> None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._write_json_response(400, {"error": "invalid content-length"})
                return

            if length < 0:
                self._write_json_response(400, {"error": "invalid content-length"})
                return

            if length > MAX_REQUEST_BODY_BYTES:
                self._write_json_response(413, {"error": "request body too large"})
                return

            raw = self.rfile.read(length) if length else b""

            if method == "POST":
                content_type = self.headers.get("Content-Type", "")
                if content_type and "application/json" not in content_type.lower():
                    self._write_json_response(415, {"error": "content-type must be application/json"})
                    return

            try:
                body = json.loads(raw.decode("utf-8")) if raw else {}
                if not isinstance(body, dict):
                    self._write_json_response(400, {"error": "request body must be a JSON object"})
                    return
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._write_json_response(400, {"error": "malformed json"})
                return

            headers = {k: v for k, v in self.headers.items()}
            try:
                status, payload = dispatch_http_request(service, method, self.path, body, headers)
            except Exception:
                service.logger.emit("request_error", method=method, path=self.path)
                self._write_json_response(500, {"error": "internal_server_error"})
                return

            self._write_json_response(status, payload)

        def log_message(self, format: str, *args: Any) -> None:
            return None

    return Libr8RequestHandler


def serve_forever(service: Libr8Service) -> None:
    server = ThreadingHTTPServer((service.config.host, service.config.port), build_handler_class(service))
    service.logger.emit("service_start", host=service.config.host, port=service.config.port)
    server.serve_forever()
