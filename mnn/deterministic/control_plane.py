"""Neuro-symbolic deterministic control plane runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List

from .audit import HashChainAuditLogger
from .exceptions import DeterministicHalt
from .lifecycle import LifecycleController, LifecycleState
from .utils import canonical_json, sha256_hex


@dataclass
class NeuroSymbolicControlPlane:
    """NEXUS v3.0-inspired deterministic governance layer.

    - Nucleus: deterministic ingestion + validation
    - Spine: hash-chained provenance log
    - Mitochondria: execution guard and halt policy
    """

    log_path: Path = Path("/app/logs/deterministic/run.jsonl")
    root_seed: int = 2026

    def run_query(self, query: str, execute_fn: Callable[[str], List[Dict[str, Any]]]) -> Dict[str, Any]:
        run_id = sha256_hex(f"{self.root_seed}|{query}")[:16]
        lifecycle = LifecycleController(run_id=run_id)
        logger = HashChainAuditLogger(path=self.log_path)

        try:
            lifecycle.transition(LifecycleState.INITIALIZE, {"query": query})
            logger.log_event("initialize", {"query_hash": sha256_hex(query), "root_seed": self.root_seed})

            normalized = " ".join(query.split())
            lifecycle.transition(LifecycleState.VALIDATE, {"normalized_query": normalized})
            logger.log_event("validate", {"normalized_query_hash": sha256_hex(normalized)})

            results = execute_fn(normalized)
            result_hash = sha256_hex(canonical_json(results))
            lifecycle.transition(LifecycleState.OPERATE, {"result_count": len(results), "state_digest": result_hash})
            logger.log_event("operate", {"result_hash": result_hash, "result_count": len(results)})

            lifecycle.transition(
                LifecycleState.RECONCILE,
                {"state_digest": result_hash},
                expected_hash=result_hash,
            )
            logger.log_event("reconcile", {"state_digest": result_hash})

            lifecycle.transition(
                LifecycleState.CHECKPOINT,
                {"state_digest": result_hash},
                expected_hash=result_hash,
            )
            logger.log_event("checkpoint", {"state_digest": result_hash})

            lifecycle.transition(LifecycleState.TERMINATE, {"status": "ok"})
            logger.log_event("terminate", {"status": "ok"})

            return {
                "results": results,
                "result_hash": result_hash,
                "run_id": run_id,
            }
        except DeterministicHalt:
            logger.log_event("deterministic_halt", {"query_hash": sha256_hex(query)})
            raise
