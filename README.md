# MNN

Infrastructure and persistence helpers for Matrix Neural Network (MNN).

## Database setup

1. Provision PostgreSQL and set `THALOS_DB_DSN`, e.g.:
   ```bash
   export THALOS_DB_DSN=postgresql://thalos:thalos@localhost:5432/thalos
   ```
2. Apply the schema:
   ```bash
   python -c "from middleware import ThalosBridge; ThalosBridge().apply_schema()"
   ```

Tables created:
- `manifold_coordinates` – relational buffer for embeddings and metadata
- `void_logs` – safety log sink
- `weights_vault` – encrypted vault for model weights bound to a hardware fingerprint

## Using the middleware

```python
from middleware import ThalosBridge

bridge = ThalosBridge()
coord_id = bridge.write_manifold_coordinate(
    source="sensor_A",
    coordinate={"x": 1.2, "y": -0.7},
    embedding=[0.1, 0.2, 0.3],
    confidence=0.98,
)
bridge.write_void_log("info", "coordinate captured", {"id": coord_id}, coordinate_ref=coord_id)

# Store and load weights (bytes)
with open("weights.bin", "rb") as fh:
    weight_bytes = fh.read()
bridge.upsert_encrypted_weights("mnn-core", weight_bytes)
restored = bridge.load_encrypted_weights("mnn-core")
```

## Hardware-bound encryption

`weight_encryptor.py` binds AES-GCM encryption to a hardware fingerprint derived from the host. Override with `THALOS_HARDWARE_ID` for stable CI or clustered deployments. Checksums ensure tamper detection during decrypt.
