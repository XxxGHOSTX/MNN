-- Relational Buffer schema for /artifacts/{appId}/public/data/
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE SCHEMA IF NOT EXISTS mnn;

CREATE TABLE IF NOT EXISTS mnn.applications (
    app_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mnn.artifacts (
    artifact_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    app_id UUID NOT NULL REFERENCES mnn.applications(app_id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    description TEXT,
    storage_path TEXT GENERATED ALWAYS AS (format('/artifacts/%s/public/data/%s', app_id::text, artifact_id::text)) STORED,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (app_id, version)
);

CREATE TABLE IF NOT EXISTS mnn.manifolds (
    manifold_id BIGSERIAL PRIMARY KEY,
    artifact_id UUID NOT NULL REFERENCES mnn.artifacts(artifact_id) ON DELETE CASCADE,
    dimension SMALLINT NOT NULL CHECK (dimension > 0),
    coordinate_system TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mnn.manifold_coordinates (
    coordinate_id BIGSERIAL PRIMARY KEY,
    manifold_id BIGINT NOT NULL REFERENCES mnn.manifolds(manifold_id) ON DELETE CASCADE,
    tensor_index BIGINT NOT NULL,
    coordinates DOUBLE PRECISION[] NOT NULL,
    value DOUBLE PRECISION,
    mask BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (manifold_id, tensor_index)
);

CREATE INDEX IF NOT EXISTS idx_manifold_coordinates_lookup
    ON mnn.manifold_coordinates (manifold_id, tensor_index);

CREATE TABLE IF NOT EXISTS mnn.void_spaces (
    void_id BIGSERIAL PRIMARY KEY,
    manifold_id BIGINT NOT NULL REFERENCES mnn.manifolds(manifold_id) ON DELETE CASCADE,
    min_bounds DOUBLE PRECISION[] NOT NULL,
    max_bounds DOUBLE PRECISION[] NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (array_length(min_bounds, 1) = array_length(max_bounds, 1))
);

CREATE INDEX IF NOT EXISTS idx_void_spaces_manifold
    ON mnn.void_spaces (manifold_id);

-- Tracks physical slices of the relational buffer within /artifacts/{appId}/public/data/
CREATE TABLE IF NOT EXISTS mnn.buffer_segments (
    segment_id BIGSERIAL PRIMARY KEY,
    artifact_id UUID NOT NULL REFERENCES mnn.artifacts(artifact_id) ON DELETE CASCADE,
    manifold_id BIGINT NOT NULL REFERENCES mnn.manifolds(manifold_id) ON DELETE CASCADE,
    min_bounds DOUBLE PRECISION[] NOT NULL,
    max_bounds DOUBLE PRECISION[] NOT NULL,
    relative_path TEXT NOT NULL,
    checksum TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (array_length(min_bounds, 1) = array_length(max_bounds, 1)),
    UNIQUE (artifact_id, manifold_id, relative_path)
);

CREATE INDEX IF NOT EXISTS idx_buffer_segments_lookup
    ON mnn.buffer_segments (artifact_id, manifold_id);
