"""Deterministic runtime endpoint regression tests for lifecycle/proofs/basile/replay and auth dashboard continuity."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api import app
from config import config
from mnn.deterministic.basile import coordinate_to_base29, generate_basile_volume
from mnn.deterministic.utils import sha256_hex


# Auth and deterministic endpoint smoke helpers

def _login(client: TestClient) -> str:
    response = client.post("/auth/login", json={"username": "admin", "password": "admin123!"})
    assert response.status_code == 200
    token = response.json().get("access_token")
    assert isinstance(token, str) and len(token) > 20
    return token


def test_query_lifecycle_enforced_when_deterministic_mode_true():
    client = TestClient(app)
    original = config.DETERMINISTIC_MODE
    try:
        config.DETERMINISTIC_MODE = True
        response = client.post("/query", json={"query": "deterministic lifecycle check"})
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "DETERMINISTIC LIFECYCLE CHECK"
        assert data["count"] == 5
        assert isinstance(data["results"], list)
    finally:
        config.DETERMINISTIC_MODE = original


def test_query_no_regression_when_deterministic_mode_false():
    client = TestClient(app)
    original = config.DETERMINISTIC_MODE
    try:
        config.DETERMINISTIC_MODE = False
        response = client.post("/query", json={"query": "deterministic lifecycle check"})
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "DETERMINISTIC LIFECYCLE CHECK"
        assert data["count"] == 5
        assert isinstance(data["results"], list)
    finally:
        config.DETERMINISTIC_MODE = original


def test_deterministic_proofs_authenticated_success():
    client = TestClient(app)
    token = _login(client)
    response = client.get("/deterministic/proofs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    proof = response.json()["proof"]
    assert proof["z3"]["passed"] is True
    assert proof["all_passed"] is True


def test_deterministic_basile_generate_returns_stable_hash_and_base29():
    client = TestClient(app)
    token = _login(client)

    payload = {"coordinate": 12345, "seed": 2026, "query": "basile test", "volume_length": 4096}
    response_1 = client.post("/deterministic/basile/generate", json=payload, headers={"Authorization": f"Bearer {token}"})
    response_2 = client.post("/deterministic/basile/generate", json=payload, headers={"Authorization": f"Bearer {token}"})

    assert response_1.status_code == 200
    assert response_2.status_code == 200

    data_1 = response_1.json()
    data_2 = response_2.json()

    expected_hash = sha256_hex(
        generate_basile_volume(
            coordinate=payload["coordinate"],
            seed=payload["seed"],
            query=payload["query"],
            volume_length=payload["volume_length"],
        )
    )
    assert data_1["output_hash"] == expected_hash
    assert data_2["output_hash"] == expected_hash
    assert data_1["base29"] == coordinate_to_base29(payload["coordinate"])


def test_deterministic_replay_validates_hash_chained_logs(tmp_path):
    client = TestClient(app)
    token = _login(client)

    output_hash = sha256_hex(generate_basile_volume(coordinate=11, seed=2, query="abc", volume_length=256))

    log_path = tmp_path / "deterministic_replay.jsonl"
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
                "coordinate": 11,
                "seed": 2,
                "query": "abc",
                "volume_length": 256,
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
        headers={"Authorization": f"Bearer {token}"},
    )
    assert replay.status_code == 200
    replay_data = replay.json()
    assert replay_data["ok"] is True
    assert replay_data["errors"] == []
    assert isinstance(replay_data["final_hash"], str)


def test_existing_auth_dashboard_flow_still_functional():
    client = TestClient(app)
    token = _login(client)

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "admin"

    dashboard = client.get("/dashboard/overview", headers={"Authorization": f"Bearer {token}"})
    assert dashboard.status_code == 200
    dashboard_data = dashboard.json()
    assert isinstance(dashboard_data.get("metrics"), dict)
    assert isinstance(dashboard_data.get("infra"), list)
