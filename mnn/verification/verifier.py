"""
Answer Verifier - validates answer candidates using Logic Guard and UCS scoring.

The AnswerVerifier combines:
  • Logic Guard soundness gate (Z3-backed, 99% threshold)
  • UCS Master Formula relevance score
to produce a single VerificationResult for each candidate.

A candidate is considered *verified* only when:
  1. Its Logic Guard soundness >= SOUNDNESS_THRESHOLD (0.99)
  2. Its UCS relevance score > 0.0

Author: MNN Engine Contributors
"""

from dataclasses import dataclass, field
from typing import List, Optional

from mnn.ir.models import ConstraintSchema, Candidate
from mnn.guard.logic_guard import LogicGuard, GuardResult, SOUNDNESS_THRESHOLD
from mnn.ucs.kernel import MasterFormula


@dataclass
class VerificationResult:
    """
    Result of verifying a single answer candidate.

    Attributes:
        is_verified:    True iff Logic Guard passed and relevance > 0.
        soundness:      Logic Guard soundness score in [0, 1].
        relevance:      UCS Master Formula score in [0, 1].
        guard_result:   Detailed Logic Guard result.
        candidate:      The evaluated candidate.
        rejection_reason: Human-readable rejection message or None if verified.
    """

    is_verified: bool
    soundness: float
    relevance: float
    guard_result: GuardResult
    candidate: Candidate
    rejection_reason: Optional[str] = None


class AnswerVerifier:
    """
    Two-stage answer verification: Logic Guard soundness + UCS relevance.

    Stage 1 – Logic Guard:  Checks structural correctness via Z3 SMT solving.
              Candidate is rejected immediately if soundness < threshold.

    Stage 2 – UCS Master Formula: Computes semantic relevance relative to
              the original query.

    Both stages must pass for ``is_verified`` to be True.

    Attributes:
        schema:    Constraint schema governing structural validity.
        threshold: Soundness threshold (default: SOUNDNESS_THRESHOLD).
        _guard:    LogicGuard instance.
        _formula:  MasterFormula instance.

    Examples:
        >>> from mnn.ir.models import ConstraintSchema, Candidate
        >>> schema = ConstraintSchema(min_length=5, max_length=200)
        >>> verifier = AnswerVerifier(schema)
        >>> candidate = Candidate(content="hello world", seed=0, generation_step=0)
        >>> result = verifier.verify("hello", candidate)
        >>> result.is_verified
        True
        >>> 0.0 < result.relevance <= 1.0
        True
    """

    def __init__(
        self,
        schema: ConstraintSchema,
        threshold: float = SOUNDNESS_THRESHOLD,
    ) -> None:
        self.schema = schema
        self.threshold = threshold
        self._guard = LogicGuard(schema, threshold=threshold)
        self._formula = MasterFormula()

    def verify(self, query: str, candidate: Candidate) -> VerificationResult:
        """
        Verify a single candidate against the query.

        Args:
            query:     Original query string (used for UCS relevance scoring).
            candidate: Candidate to verify.

        Returns:
            VerificationResult with full verification details.
        """
        # Stage 1: Logic Guard
        guard_result = self._guard.evaluate(candidate)

        if not guard_result.is_sound:
            reason = (
                f"Logic Guard soundness {guard_result.soundness:.4f} "
                f"< threshold {self.threshold:.2f}. "
                f"Failed checks: {guard_result.failed_checks}"
            )
            return VerificationResult(
                is_verified=False,
                soundness=guard_result.soundness,
                relevance=0.0,
                guard_result=guard_result,
                candidate=candidate,
                rejection_reason=reason,
            )

        # Stage 2: UCS relevance
        relevance = self._formula.score(query, candidate.content)

        return VerificationResult(
            is_verified=relevance > 0.0,
            soundness=guard_result.soundness,
            relevance=relevance,
            guard_result=guard_result,
            candidate=candidate,
            rejection_reason=None if relevance > 0.0 else "UCS relevance score is zero",
        )

    def verify_batch(
        self, query: str, candidates: List[Candidate]
    ) -> List[VerificationResult]:
        """
        Verify a batch of candidates.

        Args:
            query:      Original query string.
            candidates: List of candidates to verify.

        Returns:
            List of VerificationResult in the same order as input.
        """
        return [self.verify(query, c) for c in candidates]

    def verified_only(
        self, query: str, candidates: List[Candidate]
    ) -> List[VerificationResult]:
        """
        Return only the verified candidates, sorted by relevance (descending).

        Args:
            query:      Original query string.
            candidates: List of candidates to evaluate.

        Returns:
            Verified VerificationResults sorted by descending relevance.
        """
        results = self.verify_batch(query, candidates)
        verified = [r for r in results if r.is_verified]
        # Sort by relevance descending; tie-break by candidate content for determinism
        verified.sort(key=lambda r: (-r.relevance, r.candidate.content))
        return verified
