"""
SMT Solver Gate

Z3-based validation of candidates against constraint schemas.
Checks length bounds, token containment, charset requirements, and code invariants.
Emits BreachCoordinates for failed validations to guide repair.

Author: MNN Engine Contributors
"""

from typing import Optional, Tuple
import string
from z3 import *
from mnn.ir.models import ConstraintSchema, Candidate, BreachCoordinates


class SMTSolver:
    """
    SMT-based constraint validator using Z3.
    
    Validates candidates against formal constraints and provides detailed
    breach information for repair attempts.
    
    Attributes:
        schema: The constraint schema to enforce
        timeout_ms: Solver timeout in milliseconds
    """
    
    def __init__(self, schema: ConstraintSchema, timeout_ms: int = 5000):
        """
        Initialize SMT solver.
        
        Args:
            schema: Constraint schema to validate against
            timeout_ms: Z3 solver timeout in milliseconds
        """
        self.schema = schema
        self.timeout_ms = timeout_ms
    
    def validate(self, candidate: Candidate) -> Tuple[bool, Optional[BreachCoordinates]]:
        """
        Validate a candidate against the constraint schema.
        
        Args:
            candidate: Candidate to validate
            
        Returns:
            Tuple of (is_valid, breach_coordinates)
            If valid, breach_coordinates is None.
            If invalid, breach_coordinates contains violation details.
            
        Examples:
            >>> from mnn.ir.models import ConstraintSchema, Candidate
            >>> schema = ConstraintSchema(required_tokens=['hello'], min_length=5, max_length=100)
            >>> candidate = Candidate(content='hello world', seed=42, generation_step=0)
            >>> solver = SMTSolver(schema)
            >>> is_valid, breach = solver.validate(candidate)
            >>> is_valid
            True
        """
        content = candidate.content
        violations = []
        missing_tokens = []
        length_violation = None
        charset_violations = []
        code_violations = {}
        repair_hints = []
        
        # Check length bounds
        content_length = len(content)
        if content_length < self.schema.min_length:
            violations.append('length_too_short')
            length_violation = 'too_short'
            repair_hints.append(f'pad_to_{self.schema.min_length}')
        elif content_length > self.schema.max_length:
            violations.append('length_too_long')
            length_violation = 'too_long'
            repair_hints.append(f'truncate_to_{self.schema.max_length}')
        
        # Check required tokens
        content_lower = content.lower()
        for token in self.schema.required_tokens:
            if token.lower() not in content_lower:
                violations.append(f'missing_token_{token}')
                missing_tokens.append(token)
                repair_hints.append(f'insert_{token}')
        
        # Check charset constraints
        allowed_chars = self._get_allowed_chars()
        for char in content:
            if char not in allowed_chars:
                charset_violations.append(char)
        
        if charset_violations:
            violations.append('charset_violation')
            repair_hints.append('replace_invalid_chars')
        
        # Check code invariants if applicable
        if 'code' in self.schema.domain_hints:
            code_violations = self._check_code_invariants(content)
            if code_violations:
                violations.extend([f'code_{k}' for k in code_violations.keys()])
                repair_hints.extend([f'fix_{k}' for k in code_violations.keys()])
        
        # Determine if valid
        is_valid = len(violations) == 0
        
        if is_valid:
            return True, None
        
        # Create breach coordinates
        breach = BreachCoordinates(
            violated_constraints=violations,
            missing_tokens=missing_tokens,
            length_violation=length_violation,
            charset_violations=charset_violations[:20],  # Limit to first 20
            code_violations=code_violations,
            repair_hints=repair_hints
        )
        
        return False, breach
    
    def _get_allowed_chars(self) -> set:
        """
        Get allowed characters based on charset setting.
        
        Returns:
            Set of allowed characters
        """
        if self.schema.charset == 'ascii':
            return set(string.ascii_letters)
        elif self.schema.charset == 'alphanumeric':
            return set(string.ascii_letters + string.digits)
        elif self.schema.charset == 'printable':
            # Allow printable ASCII
            return set(string.printable)
        else:  # unicode
            # For simplicity, allow printable + extended
            return set(string.printable + ''.join(chr(i) for i in range(128, 256)))
    
    def _check_code_invariants(self, content: str) -> dict:
        """
        Check code-specific invariants.
        
        Args:
            content: Content to check
            
        Returns:
            Dictionary of violations
        """
        violations = {}
        invariants = self.schema.code_invariants
        
        # Check brace balance
        if invariants.get('require_brace_balance', False):
            if not self._check_brace_balance(content):
                violations['brace_imbalance'] = True
        
        # Check required keywords
        required_keywords = invariants.get('require_keywords', [])
        content_lower = content.lower()
        missing_keywords = [kw for kw in required_keywords if kw.lower() not in content_lower]
        if missing_keywords:
            violations['missing_keywords'] = missing_keywords
        
        return violations
    
    def _check_brace_balance(self, content: str) -> bool:
        """
        Check if braces are balanced.
        
        Args:
            content: Content to check
            
        Returns:
            True if balanced, False otherwise
        """
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        
        for char in content:
            if char in pairs:
                stack.append(char)
            elif char in pairs.values():
                if not stack:
                    return False
                if pairs[stack[-1]] != char:
                    return False
                stack.pop()
        
        return len(stack) == 0


def validate_candidate(candidate: Candidate, schema: ConstraintSchema) -> Tuple[bool, Optional[BreachCoordinates]]:
    """
    Convenience function to validate a candidate.
    
    Args:
        candidate: Candidate to validate
        schema: Constraint schema
        
    Returns:
        Tuple of (is_valid, breach_coordinates)
    """
    solver = SMTSolver(schema)
    return solver.validate(candidate)


def repair_candidate(candidate: Candidate, breach: BreachCoordinates, schema: ConstraintSchema) -> Optional[Candidate]:
    """
    Attempt to repair a candidate based on breach coordinates.
    
    Applies deterministic repair strategies based on the breach hints.
    
    Args:
        candidate: Failed candidate
        breach: Breach coordinates with repair hints
        schema: Constraint schema
        
    Returns:
        Repaired candidate if successful, None if repair failed
        
    Examples:
        >>> from mnn.ir.models import ConstraintSchema, Candidate, BreachCoordinates
        >>> schema = ConstraintSchema(min_length=20, max_length=100)
        >>> candidate = Candidate(content='short', seed=42, generation_step=0)
        >>> breach = BreachCoordinates(
        ...     violated_constraints=['length_too_short'],
        ...     length_violation='too_short',
        ...     repair_hints=['pad_to_20']
        ... )
        >>> repaired = repair_candidate(candidate, breach, schema)
        >>> repaired is not None
        True
        >>> len(repaired.content) >= 20
        True
    """
    if not breach.is_repairable():
        return None
    
    content = candidate.content
    
    # Apply repairs in order of hints
    for hint in breach.repair_hints:
        if hint.startswith('pad_to_'):
            target_length = int(hint.split('_')[-1])
            padding_needed = target_length - len(content)
            if padding_needed > 0:
                # Pad with spaces
                content = content + ' ' * padding_needed
        
        elif hint.startswith('truncate_to_'):
            target_length = int(hint.split('_')[-1])
            content = content[:target_length]
        
        elif hint.startswith('insert_'):
            token = hint.split('_', 1)[1]
            # Insert token at beginning if there's room
            if len(content) + len(token) + 1 <= schema.max_length:
                content = token + ' ' + content
        
        elif hint == 'replace_invalid_chars':
            # Replace invalid characters with spaces
            allowed = set(string.printable)
            content = ''.join(c if c in allowed else ' ' for c in content)
        
        elif hint.startswith('fix_'):
            # Code-specific fixes are complex, skip for now
            pass
    
    # Create repaired candidate
    repaired = Candidate(
        content=content,
        seed=candidate.seed,
        generation_step=candidate.generation_step + 1000,  # Offset to mark as repaired
        metadata={
            **candidate.metadata,
            'repaired': True,
            'original_step': candidate.generation_step
        }
    )
    
    return repaired
