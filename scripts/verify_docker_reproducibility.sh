#!/usr/bin/env bash
set -euo pipefail

IMAGE_A="mnn-hermetic:build-a"
IMAGE_B="mnn-hermetic:build-b"
DOCKERFILE="devops/docker/Dockerfile.hermetic"

echo "[repro] Building first image (${IMAGE_A})"
SOURCE_DATE_EPOCH=0 docker build --no-cache --provenance=false --sbom=false \
  --build-arg SOURCE_DATE_EPOCH=0 \
  -f "${DOCKERFILE}" -t "${IMAGE_A}" .

echo "[repro] Building second image (${IMAGE_B})"
SOURCE_DATE_EPOCH=0 docker build --no-cache --provenance=false --sbom=false \
  --build-arg SOURCE_DATE_EPOCH=0 \
  -f "${DOCKERFILE}" -t "${IMAGE_B}" .

echo "[repro] Comparing image content (file hashes + metadata; timestamps excluded)"

# Docker BuildKit records ctime (change time) in layer tars, not mtime,
# so image IDs always differ between two separate builds even with identical
# Dockerfile and source.  The meaningful reproducibility check is that every
# file's *content* (sha256), permissions, uid, gid, type and link-target are
# identical between the two builds.
python3 /dev/stdin "${IMAGE_A}" "${IMAGE_B}" <<'PYEOF'
import sys, io, json, tarfile, hashlib, subprocess

def image_content_fingerprint(image):
    """Return {path: (content_sha256_or_None, mode, uid, gid, size, type, linkname)}
    accumulated across all layers (later layers overwrite earlier ones, same as overlay)."""
    proc = subprocess.run(["docker", "save", image], capture_output=True)
    if proc.returncode != 0:
        print(f"docker save {image} failed: {proc.stderr.decode()}", file=sys.stderr)
        sys.exit(1)

    files = {}
    with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as outer:
        manifest = json.loads(outer.extractfile("manifest.json").read())
        for layer_path in manifest[0]["Layers"]:
            layer_bytes = outer.extractfile(layer_path).read()
            with tarfile.open(fileobj=io.BytesIO(layer_bytes)) as layer:
                for m in layer.getmembers():
                    # whiteout entries mark deletions – keep them as-is
                    if m.isfile():
                        data = layer.extractfile(m).read()
                        h = hashlib.sha256(data).hexdigest()
                    else:
                        h = None
                    files[m.name] = (h, m.mode, m.uid, m.gid, m.size,
                                     m.type, m.linkname or "")
    return files

image_a, image_b = sys.argv[1], sys.argv[2]
ca = image_content_fingerprint(image_a)
cb = image_content_fingerprint(image_b)

keys = sorted(set(list(ca) + list(cb)))
diffs = []
for k in keys:
    if k not in ca:
        diffs.append(f"ONLY_IN_B: {k}")
    elif k not in cb:
        diffs.append(f"ONLY_IN_A: {k}")
    elif ca[k] != cb[k]:
        diffs.append(f"CONTENT_DIFF: {k}\n  A={ca[k]}\n  B={cb[k]}")

if diffs:
    for d in diffs[:30]:
        print(d, file=sys.stderr)
    sys.exit(1)

print("[repro] Content fingerprints match across all layers")
PYEOF

echo "[repro] SUCCESS: image content is identical (timestamps excluded)"
