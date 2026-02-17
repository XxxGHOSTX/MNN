"""
Semantic Lattice Module

Deterministic candidate generation from constraint schemas.

Author: MNN Engine Contributors
"""

import random
import string
from typing import List, Iterator
from mnn.ir.models import ConstraintSchema, Candidate


class SemanticLattice:
    """
    Deterministic lattice proposer for generating candidates.
    
    Generates candidate outputs from a constraint schema and seed,
    ensuring full determinism for reproducibility.
    
    Attributes:
        schema: The constraint schema to satisfy
        seed: Base seed for deterministic generation
        _rng: Internal random number generator
    """
    
    def __init__(self, schema: ConstraintSchema, seed: int):
        """
        Initialize the semantic lattice.
        
        Args:
            schema: Constraint schema to guide generation
            seed: Deterministic seed
        """
        self.schema = schema
        self.seed = seed
        self._rng = random.Random(seed)
    
    def _get_charset_chars(self) -> str:
        """
        Get characters based on the schema charset.
        
        Returns:
            String of allowed characters
        """
        if self.schema.charset == 'ascii':
            return string.ascii_letters
        elif self.schema.charset == 'alphanumeric':
            return string.ascii_letters + string.digits
        elif self.schema.charset == 'printable':
            return string.printable.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')[:95]
        else:  # unicode
            # For simplicity, use printable for unicode too
            return string.printable.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')[:95]
    
    def _generate_base_content(self, target_length: int) -> str:
        """
        Generate base content of specified length.
        
        Args:
            target_length: Target content length
            
        Returns:
            Generated content string
        """
        charset = self._get_charset_chars()
        
        # For code domain, use more structured generation
        if 'code' in self.schema.domain_hints:
            return self._generate_code_structure(target_length)
        
        # For text domain, generate text-like content
        return self._generate_text_content(target_length, charset)
    
    def _generate_text_content(self, target_length: int, charset: str) -> str:
        """
        Generate text-like content.
        
        Args:
            target_length: Target length
            charset: Allowed characters
            
        Returns:
            Text content
        """
        content = []
        current_length = 0
        
        # Try to incorporate required tokens
        for token in self.schema.required_tokens:
            if current_length + len(token) + 1 <= target_length:
                content.append(token)
                current_length += len(token) + 1
        
        # Fill remaining space with random words
        while current_length < target_length:
            word_length = self._rng.randint(3, 8)
            if current_length + word_length > target_length:
                word_length = target_length - current_length
            
            if word_length > 0:
                word = ''.join(self._rng.choice(string.ascii_lowercase) for _ in range(word_length))
                content.append(word)
                current_length += word_length
                
                # Add space if there's room
                if current_length < target_length:
                    content.append(' ')
                    current_length += 1
        
        return ''.join(content)[:target_length]
    
    def _generate_code_structure(self, target_length: int) -> str:
        """
        Generate code-like content.
        
        Args:
            target_length: Target length
            
        Returns:
            Code-like content
        """
        lines = []
        
        # Add language-specific keywords if required
        if 'python' in self.schema.domain_hints:
            # Add import statement
            lines.append("import sys")
            lines.append("")
            lines.append("def function():")
            lines.append("    \"\"\"Function implementation.\"\"\"")
            
            # Try to incorporate required tokens as comments or variable names
            for token in self.schema.required_tokens[:3]:
                if len(token) < 20:  # Only use reasonable tokens
                    lines.append(f"    {token} = None")
            
            lines.append("    return True")
            lines.append("")
            
            # Add a class if needed
            if 'class' in self.schema.code_invariants.get('require_keywords', []):
                lines.append("class Example:")
                lines.append("    def method(self):")
                lines.append("        pass")
            
        elif 'javascript' in self.schema.domain_hints:
            lines.append("function main() {")
            lines.append("    // JavaScript code")
            
            # Try to incorporate required tokens
            for token in self.schema.required_tokens[:3]:
                if len(token) < 20 and token.replace('_', '').isalnum():
                    lines.append(f"    const {token} = null;")
                else:
                    lines.append(f"    // {token}")
            
            lines.append("    return true;")
            lines.append("}")
            
        elif 'java' in self.schema.domain_hints:
            lines.append("public class Main {")
            lines.append("    public void method() {")
            lines.append("        // Java code")
            
            for token in self.schema.required_tokens[:3]:
                lines.append(f"        // {token}")
            
            lines.append("    }")
            lines.append("}")
            
        else:
            # Generic code structure
            lines.append("function main() {")
            lines.append("    // Generic code")
            
            # Add required tokens as comments
            for token in self.schema.required_tokens[:3]:
                lines.append(f"    // {token}")
            
            lines.append("    return true;")
            lines.append("}")
        
        content = '\n'.join(lines)
        
        # Pad or trim to target length
        if len(content) < target_length:
            padding = target_length - len(content)
            # Add comments to reach target length
            comment_lines = []
            remaining = padding
            while remaining > 0:
                comment = f"# Additional comment line"
                if remaining < len(comment) + 1:
                    comment = comment[:remaining]
                comment_lines.append(comment)
                remaining -= len(comment) + 1
            
            if comment_lines:
                lines.extend(comment_lines)
            content = '\n'.join(lines)
        
        return content[:target_length]
    
    def propose_candidates(self, count: int = 10) -> Iterator[Candidate]:
        """
        Generate candidate proposals.
        
        Args:
            count: Number of candidates to generate
            
        Yields:
            Candidate objects
            
        Examples:
            >>> from mnn.ir.models import ConstraintSchema
            >>> schema = ConstraintSchema(min_length=10, max_length=50)
            >>> lattice = SemanticLattice(schema, seed=42)
            >>> candidates = list(lattice.propose_candidates(count=3))
            >>> len(candidates)
            3
            >>> all(isinstance(c, Candidate) for c in candidates)
            True
        """
        for step in range(count):
            # Deterministically vary length within bounds
            length_range = self.schema.max_length - self.schema.min_length
            if length_range > 0:
                offset = (step * 13) % (length_range + 1)
                target_length = self.schema.min_length + offset
            else:
                target_length = self.schema.min_length
            
            # Generate content
            content = self._generate_base_content(target_length)
            
            # Create candidate
            candidate = Candidate(
                content=content,
                seed=self.seed,
                generation_step=step,
                metadata={
                    'target_length': target_length,
                    'domain_hints': self.schema.domain_hints,
                }
            )
            
            yield candidate


def generate_candidates(schema: ConstraintSchema, seed: int, count: int = 10) -> List[Candidate]:
    """
    Convenience function to generate candidates.
    
    Args:
        schema: Constraint schema
        seed: Deterministic seed
        count: Number of candidates to generate
        
    Returns:
        List of Candidate objects
        
    Examples:
        >>> from mnn.formalization.ccs import formalize_query
        >>> schema = formalize_query("hello world")
        >>> candidates = generate_candidates(schema, seed=42, count=5)
        >>> len(candidates)
        5
    """
    lattice = SemanticLattice(schema, seed)
    return list(lattice.propose_candidates(count))
