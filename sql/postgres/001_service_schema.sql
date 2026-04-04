CREATE TABLE IF NOT EXISTS service_runs (
    task_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    task TEXT NOT NULL,
    status TEXT NOT NULL,
    outcome TEXT,
    failure_class TEXT,
    artifact_dir TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id BIGSERIAL PRIMARY KEY,
    task_id TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS plugin_registry (
    plugin_name TEXT PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    role_scope TEXT,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mcp_server_registry (
    server_name TEXT PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    transport TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS artifact_index (
    artifact_id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL,
    artifact_kind TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
