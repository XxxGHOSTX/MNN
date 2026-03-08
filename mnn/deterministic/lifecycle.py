"""Deterministic lifecycle state-machine enforcement."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .exceptions import DeterministicHalt
from .utils import canonical_json, sha256_hex


class LifecycleState(str, Enum):
    INITIALIZE = "initialize"
    VALIDATE = "validate"
    OPERATE = "operate"
    RECONCILE = "reconcile"
    CHECKPOINT = "checkpoint"
    TERMINATE = "terminate"


_ORDER: List[LifecycleState] = [
    LifecycleState.INITIALIZE,
    LifecycleState.VALIDATE,
    LifecycleState.OPERATE,
    LifecycleState.RECONCILE,
    LifecycleState.CHECKPOINT,
    LifecycleState.TERMINATE,
]


@dataclass
class LifecycleController:
    """Strict lifecycle controller with deterministic halt snapshot support."""

    run_id: str
    current_state: Optional[LifecycleState] = None
    state_chain_hash: str = field(default_factory=lambda: "0" * 64)
    transitions: List[Dict[str, Any]] = field(default_factory=list)
    halt_dump_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "logs" / "deterministic_halts")

    def transition(
        self,
        next_state: LifecycleState,
        payload: Dict[str, Any] | None = None,
        expected_hash: str | None = None,
    ) -> Dict[str, Any]:
        payload = payload or {}
        if self.current_state is None:
            expected_prev = _ORDER[0]
        else:
            current_idx = _ORDER.index(self.current_state)
            if current_idx >= len(_ORDER) - 1:
                self._halt(
                    message="Lifecycle already terminated",
                    reason={"current": self.current_state.value, "received": next_state.value},
                )
            expected_prev = _ORDER[current_idx + 1]

        if next_state != expected_prev:
            self._halt(
                message="Invalid lifecycle transition",
                reason={"expected": expected_prev.value, "received": next_state.value},
            )

        entry_body = {
            "run_id": self.run_id,
            "from": self.current_state.value if self.current_state else None,
            "to": next_state.value,
            "payload": payload,
            "state_chain_prev": self.state_chain_hash,
        }
        entry_digest = sha256_hex(canonical_json(entry_body))

        if next_state in {LifecycleState.RECONCILE, LifecycleState.CHECKPOINT} and expected_hash:
            observed_hash = payload.get("state_digest")
            if observed_hash != expected_hash:
                self._halt(
                    message="Hash mismatch on guarded lifecycle state",
                    reason={
                        "state": next_state.value,
                        "expected_hash": expected_hash,
                        "observed_hash": observed_hash,
                    },
                )

        event = {
            **entry_body,
            "state_digest": entry_digest,
        }
        self.transitions.append(event)
        self.state_chain_hash = entry_digest
        self.current_state = next_state
        return event

    def _halt(self, message: str, reason: Dict[str, Any]) -> None:
        snapshot = {
            "run_id": self.run_id,
            "message": message,
            "reason": reason,
            "current_state": self.current_state.value if self.current_state else None,
            "state_chain_hash": self.state_chain_hash,
            "transition_count": len(self.transitions),
            "transitions": self.transitions,
        }
        self.halt_dump_dir.mkdir(parents=True, exist_ok=True)
        dump_path = self.halt_dump_dir / f"{self.run_id}.json"
        dump_path.write_text(canonical_json(snapshot))
        raise DeterministicHalt(message=message, snapshot=snapshot)
