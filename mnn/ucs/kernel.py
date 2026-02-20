"""
UCS Kernel - Unified Calculus of Sense

Master formula, NUME (Neural Universal Metric of Entropy),
Xuan-Liang semantic distance, and Verlinde entropic force.

All physical constants are derived from the Golden Ratio φ ≈ 1.618.
All computations are deterministic: identical inputs produce identical outputs.

Author: MNN Engine Contributors
"""

import math
import hashlib
from typing import List, Sequence


# Golden Ratio: φ = (1 + √5) / 2 ≈ 1.6180339887498948482
PHI: float = (1.0 + math.sqrt(5.0)) / 2.0


class UCSConstants:
    """
    Physical constants derived entirely from the Golden Ratio φ.

    Every constant is expressed as a rational power or simple arithmetic
    combination of φ so that the system is self-contained.

    Attributes:
        PHI:             Golden Ratio φ = (1 + √5)/2
        PHI_INV:         Reciprocal 1/φ  = φ - 1
        PHI_SQ:          φ²              = φ + 1
        PHI_CUBE:        φ³              = 2φ + 1
        COUPLING:        Coupling scale  = 1/φ²  ≈ 0.3820
        ENERGY_SCALE:    Energy scale    = φ³    ≈ 4.2361
        ENTROPY_UNIT:    Entropy unit    = ln(φ) ≈ 0.4812
        MASS_RATIO:      Mass ratio      = φ²    ≈ 2.6180
        TEMPERATURE:     Temperature     = 1/φ   ≈ 0.6180
    """

    PHI: float = PHI
    PHI_INV: float = 1.0 / PHI          # φ - 1  ≈ 0.618033...
    PHI_SQ: float = PHI * PHI           # φ + 1  ≈ 2.618033...
    PHI_CUBE: float = PHI ** 3          # 2φ + 1 ≈ 4.236067...
    COUPLING: float = 1.0 / (PHI * PHI)    # ≈ 0.381966...
    ENERGY_SCALE: float = PHI ** 3         # ≈ 4.236067...
    ENTROPY_UNIT: float = math.log(PHI)    # ≈ 0.481211...
    MASS_RATIO: float = PHI ** 2           # ≈ 2.618033...
    TEMPERATURE: float = 1.0 / PHI        # ≈ 0.618033...


class NUMECalculator:
    """
    Neural Universal Metric of Entropy (NUME).

    NUME quantifies the semantic information density of a text sequence
    using Shannon entropy weighted by the Golden Ratio:

        NUME(x) = φ · H(x) · C

    where H(x) is the normalised Shannon entropy over the character
    distribution of x and C = COUPLING = 1/φ².

    Being derived purely from character frequencies and fixed constants,
    the result is fully deterministic.

    Attributes:
        constants: UCSConstants instance providing φ-derived constants.
    """

    def __init__(self) -> None:
        self.constants = UCSConstants()

    def compute(self, text: str) -> float:
        """
        Compute the NUME score for a text string.

        Args:
            text: Input text to measure.

        Returns:
            Non-negative NUME score. Returns 0.0 for empty input.

        Examples:
            >>> calc = NUMECalculator()
            >>> score = calc.compute("hello world")
            >>> score >= 0.0
            True
            >>> calc.compute("aaa") < calc.compute("hello world")
            True
        """
        if not text:
            return 0.0

        # Character frequency distribution
        freq: dict[str, int] = {}
        for ch in text:
            freq[ch] = freq.get(ch, 0) + 1

        n = len(text)
        entropy = 0.0
        for count in freq.values():
            p = count / n
            entropy -= p * math.log2(p)

        # Normalise by log2 of alphabet size (max entropy for this alphabet)
        alphabet_size = len(freq)
        max_entropy = math.log2(alphabet_size) if alphabet_size > 1 else 1.0
        normalised_entropy = entropy / max_entropy if max_entropy > 0.0 else 0.0

        # Apply Golden Ratio weighting
        return self.constants.PHI * normalised_entropy * self.constants.COUPLING


class XuanLiangMetric:
    """
    Xuan-Liang semantic distance metric.

    Measures the conceptual distance between two texts using a
    φ-weighted Jaccard-style token overlap combined with an
    entropy differential:

        d(a, b) = φ_inv · (1 - J(a, b)) + COUPLING · |NUME(a) - NUME(b)|

    where J(a, b) is the normalised token Jaccard similarity and
    COUPLING = 1/φ².  A distance of 0.0 means the texts are identical
    in both token composition and entropy profile.

    Attributes:
        constants: UCSConstants instance.
        _nume: NUMECalculator used for entropy differential.
    """

    def __init__(self) -> None:
        self.constants = UCSConstants()
        self._nume = NUMECalculator()

    def distance(self, text_a: str, text_b: str) -> float:
        """
        Compute the Xuan-Liang distance between two texts.

        Args:
            text_a: First text.
            text_b: Second text.

        Returns:
            Non-negative distance value. 0.0 for identical texts.

        Examples:
            >>> m = XuanLiangMetric()
            >>> m.distance("hello", "hello")
            0.0
            >>> m.distance("hello", "world") > 0.0
            True
        """
        if text_a == text_b:
            return 0.0

        tokens_a = set(text_a.lower().split())
        tokens_b = set(text_b.lower().split())

        # Jaccard similarity
        if tokens_a or tokens_b:
            intersection = len(tokens_a & tokens_b)
            union = len(tokens_a | tokens_b)
            jaccard = intersection / union if union > 0 else 0.0
        else:
            jaccard = 1.0

        # Entropy differential
        entropy_diff = abs(self._nume.compute(text_a) - self._nume.compute(text_b))

        return self.constants.PHI_INV * (1.0 - jaccard) + self.constants.COUPLING * entropy_diff

    def similarity(self, text_a: str, text_b: str) -> float:
        """
        Compute semantic similarity as 1 / (1 + distance).

        Args:
            text_a: First text.
            text_b: Second text.

        Returns:
            Similarity in (0, 1].  1.0 for identical texts.

        Examples:
            >>> m = XuanLiangMetric()
            >>> m.similarity("hello", "hello")
            1.0
            >>> 0.0 < m.similarity("hello", "world") < 1.0
            True
        """
        return 1.0 / (1.0 + self.distance(text_a, text_b))


class VerlindeEntropicForce:
    """
    Verlinde-inspired Entropic Force calculator.

    Computes an analogue of Verlinde's entropic gravitational force
    using φ-derived constants:

        F = T · ΔS / Δx

    where:
        T  = TEMPERATURE = 1/φ  (holographic temperature)
        ΔS = ENTROPY_UNIT · Δs  (entropy change, Δs = normalised input)
        Δx = displacement (positive, default 1.0)

    Args:
        temperature: Override holographic temperature (default: 1/φ).

    Attributes:
        constants: UCSConstants instance.
        temperature: Holographic temperature used in force calculation.
    """

    def __init__(self, temperature: float | None = None) -> None:
        self.constants = UCSConstants()
        self.temperature: float = (
            temperature if temperature is not None else self.constants.TEMPERATURE
        )

    def compute(self, delta_entropy: float, displacement: float = 1.0) -> float:
        """
        Compute the entropic force.

        Args:
            delta_entropy: Dimensionless entropy change Δs ∈ [0, 1].
            displacement:  Positive displacement Δx (default 1.0).

        Returns:
            Entropic force value F ≥ 0.

        Raises:
            ValueError: If displacement ≤ 0.

        Examples:
            >>> vf = VerlindeEntropicForce()
            >>> vf.compute(0.5) > 0.0
            True
            >>> vf.compute(0.0)
            0.0
        """
        if displacement <= 0.0:
            raise ValueError(f"displacement must be positive, got {displacement}")
        delta_s = self.constants.ENTROPY_UNIT * delta_entropy
        return self.temperature * delta_s / displacement


class MasterFormula:
    """
    Master Formula of the Unified Calculus of Sense.

    Combines NUME, Xuan-Liang metric, and Verlinde force into a single
    unified score for a candidate text relative to a reference query:

        score(q, c) = NUME(c) + φ · sim(q, c) + φ² · F(Δs, 1)

    where:
        NUME(c)    = NUME score of candidate c
        sim(q, c)  = Xuan-Liang similarity between query q and candidate c
        F(Δs, 1)   = Verlinde force at Δs = |NUME(c) - NUME(q)|, Δx = 1

    The result is normalised to [0, 1] using a φ-scaled sigmoid.

    Attributes:
        constants:  UCSConstants.
        nume:       NUMECalculator.
        metric:     XuanLiangMetric.
        verlinde:   VerlindeEntropicForce.
    """

    def __init__(self) -> None:
        self.constants = UCSConstants()
        self.nume = NUMECalculator()
        self.metric = XuanLiangMetric()
        self.verlinde = VerlindeEntropicForce()

    def score(self, query: str, candidate: str) -> float:
        """
        Compute the master UCS score for a candidate relative to a query.

        Args:
            query:     Reference query string.
            candidate: Candidate text to score.

        Returns:
            Score in [0, 1].  Higher is better.

        Examples:
            >>> mf = MasterFormula()
            >>> s = mf.score("hello world", "hello world")
            >>> 0.0 <= s <= 1.0
            True
            >>> mf.score("hello", "hello") >= mf.score("hello", "goodbye")
            True
        """
        nome_c = self.nume.compute(candidate)
        nome_q = self.nume.compute(query)
        sim = self.metric.similarity(query, candidate)
        delta_s = abs(nome_c - nome_q)
        force = self.verlinde.compute(delta_s) if delta_s > 0.0 else 0.0

        raw = nome_c + self.constants.PHI * sim + self.constants.PHI_SQ * force

        # φ-scaled sigmoid to map raw score → (0, 1)
        return 1.0 / (1.0 + math.exp(-raw * self.constants.PHI_INV))

    def rank(self, query: str, candidates: Sequence[str]) -> List[dict]:
        """
        Rank a list of candidates by their master formula score.

        Args:
            query:      Reference query.
            candidates: Iterable of candidate strings.

        Returns:
            List of dicts with keys 'rank', 'score', 'candidate', sorted
            descending by score (rank 1 = best).

        Examples:
            >>> mf = MasterFormula()
            >>> results = mf.rank("hello", ["hello world", "goodbye"])
            >>> results[0]['rank']
            1
            >>> results[0]['score'] >= results[1]['score']
            True
        """
        scored = [
            {"candidate": c, "score": self.score(query, c)} for c in candidates
        ]
        # Stable sort: descending score, tie-break by candidate text for determinism
        scored.sort(key=lambda x: (-x["score"], x["candidate"]))
        for i, item in enumerate(scored):
            item["rank"] = i + 1
        return scored


def derive_constant_from_phi(exponent: float) -> float:
    """
    Derive a physical constant as φ^exponent.

    Args:
        exponent: Real-valued exponent.

    Returns:
        φ^exponent.

    Examples:
        >>> abs(derive_constant_from_phi(2) - PHI**2) < 1e-12
        True
        >>> derive_constant_from_phi(0)
        1.0
    """
    return PHI ** exponent
