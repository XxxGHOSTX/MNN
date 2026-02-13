import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from weight_encryptor import EncryptedWeights, WeightEncryptor


DEFAULT_DSN = os.getenv("THALOS_DB_DSN")
CONNECT_TIMEOUT = int(os.getenv("THALOS_DB_CONNECT_TIMEOUT", "10"))
# Keep ordered from lowest to highest severity; filtering relies on this ordering.
SEVERITY_LEVELS = ("debug", "info", "warn", "error", "fatal")


class ThalosBridge:
    """Middleware bridge for manifold_coordinates, void_logs, and weights_vault tables."""

    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn or DEFAULT_DSN
        if not self.dsn:
            raise ValueError("Database DSN must be provided via argument or THALOS_DB_DSN.")
        self.encryptor = WeightEncryptor()

    @staticmethod
    def _resolve_aad(model_name: str, associated_data: Optional[bytes]) -> bytes:
        return associated_data if associated_data is not None else model_name.encode("utf-8")

    @contextmanager
    def connection(self):
        conn = psycopg2.connect(self.dsn, connect_timeout=CONNECT_TIMEOUT)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def apply_schema(self, schema_path: Optional[str] = None) -> None:
        path = Path(schema_path) if schema_path else Path(__file__).with_name("thalos_db_schema.sql")
        with path.open("r", encoding="utf-8") as ddl_file:
            ddl = ddl_file.read()
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(ddl)

    def write_manifold_coordinate(
        self,
        source: str,
        coordinate: Dict[str, Any],
        embedding: Iterable[float],
        confidence: Optional[float] = None,
        tags: Optional[List[str]] = None,
    ) -> int:
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO manifold_coordinates (source, coordinate, embedding, confidence, tags)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (source, Json(coordinate), list(embedding), confidence, tags or []),
            )
            return cur.fetchone()[0]

    def fetch_manifold_coordinates(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, created_at, source, coordinate, embedding, confidence, tags
                FROM manifold_coordinates
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]

    def write_void_log(
        self,
        severity: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        coordinate_ref: Optional[int] = None,
    ) -> int:
        with self.connection() as conn, conn.cursor() as cur:
            if severity not in SEVERITY_LEVELS:
                raise ValueError(f"Invalid severity '{severity}'. Expected one of {SEVERITY_LEVELS}.")
            cur.execute(
                """
                INSERT INTO void_logs (severity, message, context, coordinate_ref)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (severity, message, Json(context) if context is not None else None, coordinate_ref),
            )
            return cur.fetchone()[0]

    def fetch_void_logs(self, limit: int = 200, min_severity: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            if min_severity:
                if min_severity not in SEVERITY_LEVELS:
                    raise ValueError(f"Invalid severity '{min_severity}'. Expected one of {SEVERITY_LEVELS}.")
                min_idx = SEVERITY_LEVELS.index(min_severity)
                allowed_levels = list(SEVERITY_LEVELS[min_idx:])
                cur.execute(
                    """
                    SELECT id, logged_at, severity, message, context, coordinate_ref
                    FROM void_logs
                    WHERE severity = ANY(%s)
                    ORDER BY logged_at DESC
                    LIMIT %s
                    """,
                    (allowed_levels, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT id, logged_at, severity, message, context, coordinate_ref
                    FROM void_logs
                    ORDER BY logged_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            rows = cur.fetchall()
            return [dict(row) for row in rows]

    def upsert_encrypted_weights(
        self,
        model_name: str,
        weights: bytes,
        metadata: Optional[Dict[str, Any]] = None,
        associated_data: Optional[bytes] = None,
    ) -> int:
        aad = self._resolve_aad(model_name, associated_data)
        payload = self.encryptor.encrypt(weights, associated_data=aad)
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO weights_vault (model_name, hardware_fingerprint, nonce, salt, ciphertext, checksum, metadata, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (model_name, hardware_fingerprint)
                DO UPDATE SET nonce = EXCLUDED.nonce,
                              salt = EXCLUDED.salt,
                              ciphertext = EXCLUDED.ciphertext,
                              checksum = EXCLUDED.checksum,
                              metadata = EXCLUDED.metadata,
                              updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (
                    model_name,
                    payload.hardware_fingerprint,
                    payload.nonce,
                    payload.salt,
                    payload.ciphertext,
                    payload.checksum,
                    Json(metadata or {}),
                ),
            )
            return cur.fetchone()[0]

    def load_encrypted_weights(self, model_name: str, associated_data: Optional[bytes] = None) -> bytes:
        with self.connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT model_name, hardware_fingerprint, nonce, salt, ciphertext, checksum
                FROM weights_vault
                WHERE model_name = %s
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (model_name,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"No weights found for model '{model_name}'")
            payload = EncryptedWeights(
                ciphertext=bytes(row["ciphertext"]),
                nonce=bytes(row["nonce"]),
                salt=bytes(row["salt"]),
                hardware_fingerprint=row["hardware_fingerprint"],
                checksum=row["checksum"],
            )
            aad = self._resolve_aad(model_name, associated_data)
            return self.encryptor.decrypt(payload, associated_data=aad)
