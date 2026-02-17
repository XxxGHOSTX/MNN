"""
IR Models for SMT-Arbiter Pipeline

Typed schemas for constraint compilation, candidate generation, and breach detection.
All models use Pydantic for validation and type safety.

Author: MNN Engine Contributors
"""

from typing import List, Set, Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ConstraintSchema(BaseModel):
    """
    Constraint Compilation Schema (CCS)
    
    Represents the formalized constraints derived from a user query.
    These constraints are used to validate candidate outputs via SMT solving.
    
    Attributes:
        required_tokens: Tokens that must appear in valid candidates
        domain_hints: Domain classification hints (e.g., 'text', 'code', 'python', 'javascript')
        min_length: Minimum character length for valid candidates
        max_length: Maximum character length for valid candidates
        charset: Allowed character set (e.g., 'ascii', 'alphanumeric', 'printable')
        code_invariants: Additional invariants for code domain (brace balance, keyword presence)
    """
    model_config = ConfigDict(frozen=True)
    
    required_tokens: List[str] = Field(default_factory=list, description="Required tokens in output")
    domain_hints: List[str] = Field(default_factory=list, description="Domain classification hints")
    min_length: int = Field(default=1, ge=1, description="Minimum output length")
    max_length: int = Field(default=1000, ge=1, description="Maximum output length")
    charset: Literal['ascii', 'alphanumeric', 'printable', 'unicode'] = Field(
        default='printable', 
        description="Allowed character set"
    )
    code_invariants: dict = Field(default_factory=dict, description="Code-specific invariants")
    
    @field_validator('max_length')
    @classmethod
    def validate_length_bounds(cls, v, info):
        """Ensure max_length >= min_length"""
        if 'min_length' in info.data and v < info.data['min_length']:
            raise ValueError(f"max_length ({v}) must be >= min_length ({info.data['min_length']})")
        return v


class Candidate(BaseModel):
    """
    A candidate output proposed by the lattice generator.
    
    Attributes:
        content: The actual text/code content
        seed: The deterministic seed used to generate this candidate
        generation_step: The step number in the generation process
        metadata: Additional metadata for traceability
    """
    model_config = ConfigDict(frozen=True)
    
    content: str = Field(description="Candidate output content")
    seed: int = Field(description="Deterministic seed")
    generation_step: int = Field(ge=0, description="Generation step index")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class BreachCoordinates(BaseModel):
    """
    Coordinates of constraint violations for repair pivoting.
    
    When SMT validation fails, this model captures the specific violations
    to guide deterministic repair attempts.
    
    Attributes:
        violated_constraints: List of constraint types that were violated
        missing_tokens: Required tokens that are missing
        length_violation: 'too_short', 'too_long', or None
        charset_violations: Specific character violations
        code_violations: Code-specific violations (unbalanced braces, missing keywords)
        repair_hints: Suggested repair strategies
    """
    model_config = ConfigDict(frozen=True)
    
    violated_constraints: List[str] = Field(default_factory=list, description="Types of violations")
    missing_tokens: List[str] = Field(default_factory=list, description="Missing required tokens")
    length_violation: Optional[Literal['too_short', 'too_long']] = Field(
        default=None, 
        description="Length constraint violation"
    )
    charset_violations: List[str] = Field(default_factory=list, description="Invalid characters")
    code_violations: dict = Field(default_factory=dict, description="Code-specific violations")
    repair_hints: List[str] = Field(default_factory=list, description="Repair strategies")
    
    def is_repairable(self) -> bool:
        """
        Determine if the breach is likely repairable.
        
        Returns:
            True if repair is feasible, False otherwise
        """
        # If too many constraints are violated, repair is unlikely
        if len(self.violated_constraints) > 5:
            return False
        # If charset violations are extensive, repair is unlikely
        if len(self.charset_violations) > 10:
            return False
        return True
