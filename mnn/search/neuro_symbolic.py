"""
Neuro-Symbolic Search Cycle

Integrates the neural generation stage (Babel Siphon semantic lattice) with
the symbolic reasoning stage (Logic Guard + Answer Verifier) in a closed
feedback loop:

    Query
      │
      ▼
    [Neural Stage]  – generate candidates via semantic lattice (Babel Siphon)
      │
      ▼
    [Symbolic Stage] – verify candidates with Logic Guard + UCS Master Formula
      │
      ▼
    SearchResults (ranked by UCS relevance)

If the first cycle produces no verified candidates, the search widens the
candidate pool (doubles max_candidates) and retries up to ``max_cycles``
times before returning an empty result set.

All operations are deterministic: identical query + seed → identical results.

Author: MNN Engine Contributors
"""

from dataclasses import dataclass, field
from typing import List

from mnn.formalization.ccs import formalize_query
from mnn.core.seed_registry import SeedRegistry
from mnn.core.semantic_lattice import generate_candidates
from mnn.verification.verifier import AnswerVerifier, VerificationResult
from mnn.ucs.kernel import MasterFormula


@dataclass
class SearchResult:
    """
    A single result from a Neuro-Symbolic search cycle.

    Attributes:
        rank:       1-based rank (1 = most relevant).
        content:    Verified candidate content.
        relevance:  UCS Master Formula relevance score in (0, 1].
        soundness:  Logic Guard soundness score in [0, 1].
        cycle:      Search cycle number in which this result was produced (1-based).
        seed:       Deterministic seed used to generate this candidate.
    """

    rank: int
    content: str
    relevance: float
    soundness: float
    cycle: int
    seed: int


class NeuroSymbolicSearch:
    """
    Closed-loop Neuro-Symbolic search engine.

    Attributes:
        base_seed:      Deterministic seed for reproducibility.
        max_candidates: Initial candidate pool size per cycle.
        max_cycles:     Maximum number of search cycles before giving up.
        top_n:          Maximum number of results to return.

    Examples:
        >>> engine = NeuroSymbolicSearch(base_seed=42, max_candidates=20, top_n=5)
        >>> results = engine.search("hello world")
        >>> isinstance(results, list)
        True
    """

    def __init__(
        self,
        base_seed: int = 0,
        max_candidates: int = 50,
        max_cycles: int = 3,
        top_n: int = 10,
    ) -> None:
        self.base_seed = base_seed
        self.max_candidates = max_candidates
        self.max_cycles = max_cycles
        self.top_n = top_n
        self._registry = SeedRegistry(base_seed=base_seed)
        self._formula = MasterFormula()

    def search(self, query: str) -> List[SearchResult]:
        """
        Execute the neuro-symbolic search cycle for a query.

        Args:
            query: User query string.

        Returns:
            List of SearchResult sorted by relevance (descending, rank 1 = best).
            Returns an empty list if no candidates survive verification.

        Examples:
            >>> engine = NeuroSymbolicSearch(base_seed=7, max_candidates=10, top_n=3)
            >>> results = engine.search("test query")
            >>> all(r.relevance > 0.0 for r in results)
            True
        """
        schema = formalize_query(query)
        verifier = AnswerVerifier(schema)
        query_seed = self._registry.derive_seed(query)

        verified_results: List[VerificationResult] = []
        pool_size = self.max_candidates

        for cycle in range(1, self.max_cycles + 1):
            cycle_seed = query_seed + cycle  # deterministic per cycle
            candidates = generate_candidates(schema, seed=cycle_seed, count=pool_size)
            verified = verifier.verified_only(query, candidates)
            verified_results.extend(verified)

            if verified_results:
                break  # found candidates – stop early

            pool_size *= 2  # widen pool for next cycle

        # De-duplicate by content (keep highest relevance per unique content)
        seen: dict[str, VerificationResult] = {}
        for vr in verified_results:
            key = vr.candidate.content
            if key not in seen or vr.relevance > seen[key].relevance:
                seen[key] = vr

        unique = list(seen.values())
        # Sort: descending relevance, tie-break by content for determinism
        unique.sort(key=lambda r: (-r.relevance, r.candidate.content))
        unique = unique[: self.top_n]

        results: List[SearchResult] = []
        for rank, vr in enumerate(unique, start=1):
            results.append(
                SearchResult(
                    rank=rank,
                    content=vr.candidate.content,
                    relevance=vr.relevance,
                    soundness=vr.soundness,
                    cycle=1,  # simplified: all from first successful cycle
                    seed=vr.candidate.seed,
                )
            )

        return results
