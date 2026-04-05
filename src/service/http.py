"""HTTP transport for the LIBR8 service."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Tuple

from src.service.app import Libr8Service
from src.service.migrations import list_postgres_migrations
from src.service.schema import service_endpoint_catalog


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
        try:
            return 202, service.submit_task(task)
        except RuntimeError as exc:
            return 503, {"error": str(exc)}
    if method == "GET" and path.startswith("/v1/runs/"):
        task_id = path.rsplit("/", 1)[-1]
        try:
            record = service.get_task(task_id)
        except RuntimeError as exc:
            return 503, {"error": str(exc)}
        if record is None:
            return 404, {"error": "task not found"}
        return 200, record
    return 404, {"error": "not found"}


def build_handler_class(service: Libr8Service):
    class Libr8RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._handle("GET")

        def do_POST(self) -> None:
            self._handle("POST")

        def _handle(self, method: str) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b""
            body = json.loads(raw.decode("utf-8")) if raw else {}
            
            headers = {k: v for k, v in self.headers.items()}
            status, payload = dispatch_http_request(service, method, self.path, body, headers)
            
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args: Any) -> None:
            return None

    return Libr8RequestHandler


def serve_forever(service: Libr8Service) -> None:
    server = ThreadingHTTPServer((service.config.host, service.config.port), build_handler_class(service))
    service.logger.emit("service_start", host=service.config.host, port=service.config.port)
    server.serve_forever()
