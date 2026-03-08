"""Deterministic runtime, formal verification, and replay tests."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from api import app, _get_auth_secret
from config import config
from mnn.deterministic.audit import HashChainAuditLogger, replay_and_validate_log
from mnn.deterministic.basile import coordinate_to_base29, generate_basile_volume
from mnn.deterministic.corpus import DeterministicCorpusEngine
from mnn.deterministic.formal import prove_lifecycle_invariants
from mnn.deterministic.lifecycle import LifecycleController, LifecycleState
from mnn.deterministic.rng import splitmix64_words
from mnn.deterministic.utils import sha256_hex


def _login(client: TestClient) -> str:
    response = client.post("/auth/login", json={"username": "admin", "password": "admin123!"})
    assert response.status_code == 200
    token = response.json().get("access_token")
    assert isinstance(token, str)
    return token


def test_lifecycle_state_order_enforced(tmp_path: Path):
    controller = LifecycleController(run_id="t1", halt_dump_dir=tmp_path)
    controller.transition(LifecycleState.INITIALIZE, {"x": 1})
    controller.transition(LifecycleState.VALIDATE, {"x": 2})
    controller.transition(LifecycleState.OPERATE, {"state_digest": "abc"})
    controller.transition(LifecycleState.RECONCILE, {"state_digest": "abc"}, expected_hash="abc")
    controller.transition(LifecycleState.CHECKPOINT, {"state_digest": "abc"}, expected_hash="abc")
    event = controller.transition(LifecycleState.TERMINATE, {"status": "ok"})
    assert event["to"] == "terminate"


def test_formal_invariants_pass():
    result = prove_lifecycle_invariants()
    assert result["z3"]["passed"] is True
    assert result["all_passed"] is True


def test_basile_generation_bit_stable():
    text_a = generate_basile_volume(coordinate=1234, seed=77, query="hello", volume_length=1_312_000)
    text_b = generate_basile_volume(coordinate=1234, seed=77, query="hello", volume_length=1_312_000)
    assert len(text_a) == 1_312_000
    assert text_a == text_b
    assert coordinate_to_base29(0) == "a"


def test_hash_chain_replay_and_regeneration(tmp_path: Path):
    log_path = tmp_path / "run.jsonl"
    logger = HashChainAuditLogger(log_path)

    generated = generate_basile_volume(coordinate=42, seed=2026, query="test", volume_length=1024)
    generated_hash = sha256_hex(generated)

    logger.log_event("initialize", {"action": "start"})
    logger.log_event(
        "operate",
        {
            "action": "basile_generate",
            "coordinate": 42,
            "seed": 2026,
            "query": "test",
            "volume_length": 1024,
            "output_hash": generated_hash,
        },
    )

    ok, errors, _ = replay_and_validate_log(log_path)
    assert ok is True
    assert errors == []


def test_rng_splitmix_words_stable():
    words_a = splitmix64_words(123456, 1, 6)
    words_b = splitmix64_words(123456, 1, 6)
    assert words_a == words_b
    assert len(words_a) == 6


def test_auth_secret_is_not_static_default():
    assert _get_auth_secret() != "mnn-dev-secret-change-me"


def test_corpus_engine_mmap_index(tmp_path: Path):
    corpus_path = tmp_path / "sample.txt"
    corpus_path.write_text("abcde abcde abcde xyzxy", encoding="ascii")
    engine = DeterministicCorpusEngine(corpus_path)
    ngrams = engine.ngram_counts(n=5)
    assert ngrams[0][0] == "abcde"
    assert ngrams[0][1] >= 3
    index = engine.build_columnar_index(top_k=5)
    assert index["rows"] >= 1


def test_api_deterministic_endpoints(tmp_path: Path):
    client = TestClient(app)
    login = client.post("/auth/login", json={"username": "admin", "password": "admin123!"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proof = client.get("/deterministic/proofs", headers=headers)
    assert proof.status_code == 200
    assert proof.json()["proof"]["z3"]["passed"] is True

    generated = client.post(
        "/deterministic/basile/generate",
        json={"coordinate": 9, "seed": 7, "query": "abc", "volume_length": 2048},
        headers=headers,
    )
    assert generated.status_code == 200
    output_hash = generated.json()["output_hash"]

    log_path = Path(config.DETERMINISTIC_AUDIT_LOG_PATH).parent / "test_replay_endpoint.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entries = [
        {
            "event_id": "init",
            "payload": {"action": "start"},
            "state_chain_prev": "0" * 64,
        },
        {
            "event_id": "operate",
            "payload": {
                "action": "basile_generate",
                "coordinate": 9,
                "seed": 7,
                "query": "abc",
                "volume_length": 2048,
                "output_hash": output_hash,
            },
            "state_chain_prev": "",
        },
    ]

    for i, entry in enumerate(entries):
        if i > 0:
            entry["state_chain_prev"] = entries[i - 1]["state_chain_hash"]
        body = {
            "event_id": entry["event_id"],
            "payload": entry["payload"],
            "state_chain_prev": entry["state_chain_prev"],
        }
        entry["state_chain_hash"] = sha256_hex(json.dumps(body, sort_keys=True, separators=(",", ":")))

    with log_path.open("w", encoding="utf-8") as fh:
        for row in entries:
            fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")

    replay = client.post(
        "/deterministic/replay",
        json={"log_path": str(log_path)},
        headers=headers,
    )
    assert replay.status_code == 200
    assert replay.json()["ok"] is True


def test_api_replay_rejects_outside_paths(tmp_path: Path):
    client = TestClient(app)
    token = _login(client)
    forbidden = tmp_path / "outside.jsonl"
    forbidden.write_text("{}\n", encoding="utf-8")
    response = client.post(
        "/deterministic/replay",
        json={"log_path": str(forbidden)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
