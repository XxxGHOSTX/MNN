"""
SMT-Arbiter "Babel Siphon" Pipeline

End-to-end deterministic pipeline for SMT-validated output generation.

Pipeline stages:
1. Formalize query into Constraint Compilation Schema (CCS)
2. Generate candidates from semantic lattice
3. Validate candidates via SMT solver
4. Repair failed candidates (with budget)
5. Score and rank validated candidates
6. Return top-N results or clean error

Author: MNN Engine Contributors
"""

from typing import List, Dict, Any, Optional
from mnn.formalization.ccs import formalize_query
from mnn.core.seed_registry import SeedRegistry
from mnn.core.semantic_lattice import generate_candidates
from mnn.solver.smt_solver import SMTSolver, repair_candidate
from mnn.scoring.ranker import score_and_rank_candidates
from mnn.ir.models import Candidate


class BabelSiphonPipeline:
    """
    SMT-Arbiter pipeline for deterministic, validated output generation.
    
    Ensures all outputs satisfy formal constraints via SMT validation.
    Never emits unvalidated noise.
    
    Attributes:
        seed_registry: Deterministic seed management
        max_candidates: Maximum number of candidates to generate
        max_repair_attempts: Maximum repair attempts per candidate
        top_n: Number of top results to return
    """
    
    def __init__(
        self,
        base_seed: int = 0,
        max_candidates: int = 50,
        max_repair_attempts: int = 3,
        top_n: int = 10
    ):
        """
        Initialize the pipeline.
        
        Args:
            base_seed: Base seed for deterministic generation
            max_candidates: Maximum candidates to generate per query
            max_repair_attempts: Maximum repair attempts per failed candidate
            top_n: Number of top results to return
        """
        self.seed_registry = SeedRegistry(base_seed=base_seed)
        self.max_candidates = max_candidates
        self.max_repair_attempts = max_repair_attempts
        self.top_n = top_n
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        Execute the complete pipeline for a query.
        
        Args:
            query: User query string
            
        Returns:
            Dictionary containing:
                - status: 'success' or 'no_valid_candidates'
                - results: List of validated results (if status='success')
                - statistics: Pipeline execution statistics
                
        Examples:
            >>> pipeline = BabelSiphonPipeline(base_seed=42)
            >>> result = pipeline.run("find text with hello")
            >>> result['status'] in ['success', 'no_valid_candidates']
            True
        """
        statistics = {
            'candidates_generated': 0,
            'candidates_validated': 0,
            'candidates_failed': 0,
            'repair_attempts': 0,
            'repair_successes': 0,
        }
        
        # Stage 1: Formalize query to CCS
        schema = formalize_query(query)
        
        # Stage 2: Derive deterministic seed for this query
        query_seed = self.seed_registry.derive_seed(query)
        
        # Stage 3: Generate candidates from semantic lattice
        candidates = generate_candidates(schema, query_seed, count=self.max_candidates)
        statistics['candidates_generated'] = len(candidates)
        
        # Stage 4: Validate candidates via SMT solver
        solver = SMTSolver(schema)
        validated_candidates: List[Candidate] = []
        
        for candidate in candidates:
            is_valid, breach = solver.validate(candidate)
            
            if is_valid:
                validated_candidates.append(candidate)
                statistics['candidates_validated'] += 1
            else:
                statistics['candidates_failed'] += 1
                
                # Stage 5: Attempt repair if breach is repairable
                if breach and breach.is_repairable():
                    for attempt in range(self.max_repair_attempts):
                        statistics['repair_attempts'] += 1
                        repaired = repair_candidate(candidate, breach, schema)
                        
                        if repaired:
                            # Validate repaired candidate
                            is_valid, new_breach = solver.validate(repaired)
                            if is_valid:
                                validated_candidates.append(repaired)
                                statistics['candidates_validated'] += 1
                                statistics['repair_successes'] += 1
                                break
                            else:
                                # Update breach for next attempt
                                breach = new_breach
        
        # Check if we have any validated candidates
        if not validated_candidates:
            return {
                'status': 'no_valid_candidates',
                'message': 'No candidates satisfied the constraints within the attempt budget.',
                'schema': schema.model_dump(),
                'statistics': statistics,
            }
        
        # Stage 6: Score and rank validated candidates
        ranked = score_and_rank_candidates(validated_candidates, schema, top_n=self.top_n)
        
        # Stage 7: Format results
        results = []
        for item in ranked:
            results.append({
                'rank': item['rank'],
                'score': item['score'],
                'content': item['candidate'].content,
                'metadata': {
                    'seed': item['candidate'].seed,
                    'generation_step': item['candidate'].generation_step,
                    **item['candidate'].metadata
                }
            })
        
        return {
            'status': 'success',
            'results': results,
            'schema': schema.model_dump(),
            'statistics': statistics,
        }


def run_babel_siphon_pipeline(
    query: str,
    base_seed: int = 0,
    max_candidates: int = 50,
    top_n: int = 10
) -> Dict[str, Any]:
    """
    Convenience function to run the Babel Siphon pipeline.
    
    Args:
        query: User query string
        base_seed: Base seed for deterministic generation
        max_candidates: Maximum candidates to generate
        top_n: Number of top results to return
        
    Returns:
        Pipeline execution results
        
    Examples:
        >>> result = run_babel_siphon_pipeline("hello world", base_seed=42)
        >>> result['status'] in ['success', 'no_valid_candidates']
        True
    """
    pipeline = BabelSiphonPipeline(
        base_seed=base_seed,
        max_candidates=max_candidates,
        top_n=top_n
    )
    return pipeline.run(query)
