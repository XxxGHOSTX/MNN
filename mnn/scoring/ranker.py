"""
Deterministic Ranking and Scoring

Scores validated candidates based on structural density, minimality, and constraint satisfaction.
Provides deterministic tie-breaking for reproducible rankings.

Author: MNN Engine Contributors
"""

from typing import List, Dict, Any
from mnn.ir.models import Candidate, ConstraintSchema


class Ranker:
    """
    Deterministic ranker for validated candidates.
    
    Scores candidates based on:
    - Token coverage (how many required tokens are present)
    - Length optimality (closer to middle of range is better)
    - Structural density (ratio of meaningful content to total length)
    
    Attributes:
        schema: Constraint schema for scoring context
    """
    
    def __init__(self, schema: ConstraintSchema):
        """
        Initialize ranker.
        
        Args:
            schema: Constraint schema for context
        """
        self.schema = schema
    
    def score(self, candidate: Candidate) -> float:
        """
        Compute a score for a candidate.
        
        Higher scores are better. Score is deterministic given the same candidate.
        
        Args:
            candidate: Candidate to score
            
        Returns:
            Numeric score (higher is better)
            
        Examples:
            >>> from mnn.ir.models import ConstraintSchema, Candidate
            >>> schema = ConstraintSchema(required_tokens=['test'], min_length=10, max_length=100)
            >>> candidate = Candidate(content='test content here', seed=42, generation_step=0)
            >>> ranker = Ranker(schema)
            >>> score = ranker.score(candidate)
            >>> score > 0
            True
        """
        content = candidate.content
        score = 0.0
        
        # Token coverage score (0-100 points)
        if self.schema.required_tokens:
            content_lower = content.lower()
            tokens_present = sum(1 for token in self.schema.required_tokens if token.lower() in content_lower)
            token_coverage = tokens_present / len(self.schema.required_tokens)
            score += token_coverage * 100
        else:
            # If no required tokens, give baseline score
            score += 50
        
        # Length optimality score (0-50 points)
        # Prefer lengths closer to the middle of the range
        target_length = (self.schema.min_length + self.schema.max_length) / 2
        length_range = self.schema.max_length - self.schema.min_length
        if length_range > 0:
            distance_from_target = abs(len(content) - target_length)
            normalized_distance = distance_from_target / length_range
            length_score = (1 - normalized_distance) * 50
            score += max(0, length_score)
        else:
            score += 25
        
        # Structural density score (0-50 points)
        # Ratio of non-whitespace to total length
        non_whitespace = sum(1 for c in content if not c.isspace())
        if len(content) > 0:
            density = non_whitespace / len(content)
            score += density * 50
        
        return score
    
    def rank(self, candidates: List[Candidate]) -> List[Dict[str, Any]]:
        """
        Rank candidates in descending order of score.
        
        Uses deterministic tie-breaking based on generation_step.
        
        Args:
            candidates: List of candidates to rank
            
        Returns:
            List of dictionaries with 'candidate', 'score', and 'rank' keys
            
        Examples:
            >>> from mnn.ir.models import ConstraintSchema, Candidate
            >>> schema = ConstraintSchema(min_length=5, max_length=50)
            >>> candidates = [
            ...     Candidate(content='short', seed=42, generation_step=0),
            ...     Candidate(content='this is longer content', seed=42, generation_step=1),
            ... ]
            >>> ranker = Ranker(schema)
            >>> ranked = ranker.rank(candidates)
            >>> len(ranked)
            2
            >>> ranked[0]['rank']
            1
        """
        # Score all candidates
        scored = []
        for candidate in candidates:
            score = self.score(candidate)
            scored.append({
                'candidate': candidate,
                'score': score,
            })
        
        # Sort by score (descending), then by generation_step (ascending) for tie-break
        scored.sort(key=lambda x: (-x['score'], x['candidate'].generation_step))
        
        # Add rank numbers
        for rank, item in enumerate(scored, start=1):
            item['rank'] = rank
        
        return scored


def score_and_rank_candidates(
    candidates: List[Candidate],
    schema: ConstraintSchema,
    top_n: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to score and rank candidates.
    
    Args:
        candidates: List of candidates to rank
        schema: Constraint schema for scoring context
        top_n: Optional limit on number of results to return
        
    Returns:
        List of ranked candidates with scores
        
    Examples:
        >>> from mnn.ir.models import ConstraintSchema, Candidate
        >>> schema = ConstraintSchema(min_length=5, max_length=50)
        >>> candidates = [
        ...     Candidate(content='test', seed=42, generation_step=i)
        ...     for i in range(5)
        ... ]
        >>> ranked = score_and_rank_candidates(candidates, schema, top_n=3)
        >>> len(ranked) <= 3
        True
    """
    from typing import Optional
    
    ranker = Ranker(schema)
    ranked = ranker.rank(candidates)
    
    if top_n is not None:
        return ranked[:top_n]
    
    return ranked
