-- Thalos database schema for MNN persistence
CREATE TABLE IF NOT EXISTS manifold_coordinates (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(128) NOT NULL,
    coordinate JSONB NOT NULL,
    embedding DOUBLE PRECISION[] NOT NULL,
    confidence NUMERIC(3, 2) CHECK (confidence >= 0 AND confidence <= 1),
    tags TEXT[] DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_manifold_coordinates_created_at ON manifold_coordinates (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_manifold_coordinates_tags ON manifold_coordinates USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_manifold_coordinates_coordinate ON manifold_coordinates USING GIN (coordinate);

CREATE TABLE IF NOT EXISTS void_logs (
    id BIGSERIAL PRIMARY KEY,
    logged_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(16) NOT NULL CHECK (severity IN ('debug', 'info', 'warn', 'error', 'fatal')),
    message TEXT NOT NULL,
    context JSONB,
    coordinate_ref BIGINT REFERENCES manifold_coordinates (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_void_logs_severity_logged_at ON void_logs (severity, logged_at DESC);

CREATE TABLE IF NOT EXISTS weights_vault (
    id BIGSERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    hardware_fingerprint TEXT NOT NULL,
    nonce BYTEA NOT NULL,
    salt BYTEA NOT NULL,
    ciphertext BYTEA NOT NULL,
    checksum TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (model_name, hardware_fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_weights_vault_model ON weights_vault (model_name);
