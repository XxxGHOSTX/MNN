"""
Logic Guard - Z3-backed soundness gate with 99% threshold.

The LogicGuard wraps the existing SMT solver and computes a *soundness
score* for each candidate by running multiple constraint checks.  Any
candidate whose soundness score falls below SOUNDNESS_THRESHOLD (0.99)
is rejected.

Soundness score definition
--------------------------
Given a set of N constraint checks, soundness = passed / N.
A candidate is sound iff soundness >= SOUNDNESS_THRESHOLD.

Author: MNN Engine Contributors
"""

from typing import List, Optional
from dataclasses import dataclass, field

from mnn.ir.models import ConstraintSchema, Candidate, BreachCoordinates
from mnn.solver.smt_solver import SMTSolver


# 99% soundness threshold as required by the Library of Sense specification.
SOUNDNESS_THRESHOLD: float = 0.99


@dataclass
class GuardResult:
    """
    Result of a Logic Guard soundness evaluation.

    Attributes:
        is_sound:          True iff soundness >= SOUNDNESS_THRESHOLD.
        soundness:         Fraction of checks passed in [0.0, 1.0].
        passed_checks:     Names of checks that passed.
        failed_checks:     Names of checks that failed.
        breach:            SMT breach coordinates when smt_check failed, else None.
        candidate_content: Content of the evaluated candidate.
    """

    is_sound: bool
    soundness: float
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    breach: Optional[BreachCoordinates] = None
    candidate_content: str = ""


class LogicGuard:
    """
    Z3-backed Logic Guard that enforces a 99% soundness threshold.

    Each evaluation runs the following checks:
        1. ``smt_check``       – Z3 constraint validation via SMTSolver.
        2. ``length_check``    – Character length within schema bounds.
        3. ``token_check``     – All required tokens are present.
        4. ``charset_check``   – Characters are within the declared charset.
        5. ``nonempty_check``  – Candidate content is not empty.

    Soundness = (number of passed checks) / (total checks).
    A candidate passes the guard iff soundness >= SOUNDNESS_THRESHOLD.

    Attributes:
        schema:    The constraint schema to enforce.
        threshold: Soundness threshold (default: SOUNDNESS_THRESHOLD = 0.99).
    """

    _CHECKS: List[str] = [
        "nonempty_check",
        "length_check",
        "charset_check",
        "token_check",
        "smt_check",
    ]

    def __init__(
        self,
        schema: ConstraintSchema,
        threshold: float = SOUNDNESS_THRESHOLD,
    ) -> None:
        self.schema = schema
        self.threshold = threshold
        self._solver = SMTSolver(schema)

    def evaluate(self, candidate: Candidate) -> GuardResult:
        """
        Evaluate a candidate and return a GuardResult.

        Args:
            candidate: Candidate to evaluate.

        Returns:
            GuardResult with soundness score and pass/fail details.

        Examples:
            >>> from mnn.ir.models import ConstraintSchema, Candidate
            >>> schema = ConstraintSchema(min_length=5, max_length=100)
            >>> guard = LogicGuard(schema)
            >>> candidate = Candidate(content="hello world", seed=0, generation_step=0)
            >>> result = guard.evaluate(candidate)
            >>> result.is_sound
            True
            >>> result.soundness >= 0.99
            True
        """
        passed: List[str] = []
        failed: List[str] = []
        breach: Optional[BreachCoordinates] = None
        content = candidate.content

        # 1. nonempty_check
        if content:
            passed.append("nonempty_check")
        else:
            failed.append("nonempty_check")

        # 2. length_check
        if self.schema.min_length <= len(content) <= self.schema.max_length:
            passed.append("length_check")
        else:
            failed.append("length_check")

        # 3. charset_check
        if self._passes_charset(content):
            passed.append("charset_check")
        else:
            failed.append("charset_check")

        # 4. token_check
        if self._passes_tokens(content):
            passed.append("token_check")
        else:
            failed.append("token_check")

        # 5. smt_check
        is_valid, smt_breach = self._solver.validate(candidate)
        if is_valid:
            passed.append("smt_check")
        else:
            failed.append("smt_check")
            breach = smt_breach

        total = len(self._CHECKS)
        soundness = len(passed) / total
        is_sound = soundness >= self.threshold

        return GuardResult(
            is_sound=is_sound,
            soundness=soundness,
            passed_checks=passed,
            failed_checks=failed,
            breach=breach,
            candidate_content=content,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _passes_charset(self, content: str) -> bool:
        """Return True if all characters are within the allowed charset."""
        import string

        if self.schema.charset == "ascii":
            allowed = set(string.ascii_letters)
        elif self.schema.charset == "alphanumeric":
            allowed = set(string.ascii_letters + string.digits)
        elif self.schema.charset == "printable":
            allowed = set(string.printable)
        else:  # unicode
            allowed = set(string.printable + "".join(chr(i) for i in range(128, 256)))
        return all(ch in allowed for ch in content)

    def _passes_tokens(self, content: str) -> bool:
        """Return True if all required tokens are present (case-insensitive)."""
        content_lower = content.lower()
        return all(t.lower() in content_lower for t in self.schema.required_tokens)
