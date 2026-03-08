#!/usr/bin/env bash
set -euo pipefail

IMAGE_A="mnn-hermetic:build-a"
IMAGE_B="mnn-hermetic:build-b"
DOCKERFILE="devops/docker/Dockerfile.hermetic"

echo "[repro] Building first image (${IMAGE_A})"
docker build --no-cache --provenance=false --sbom=false -f "${DOCKERFILE}" -t "${IMAGE_A}" .
ID_A=$(docker image inspect "${IMAGE_A}" --format '{{.Id}}')

echo "[repro] Building second image (${IMAGE_B})"
docker build --no-cache --provenance=false --sbom=false -f "${DOCKERFILE}" -t "${IMAGE_B}" .
ID_B=$(docker image inspect "${IMAGE_B}" --format '{{.Id}}')

echo "[repro] IMAGE_A=${ID_A}"
echo "[repro] IMAGE_B=${ID_B}"

if [[ "${ID_A}" != "${ID_B}" ]]; then
  echo "[repro] FAILURE: image IDs differ" >&2
  exit 1
fi

echo "[repro] SUCCESS: image IDs are identical"
