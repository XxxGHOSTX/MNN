"""
Guardrails Module for MNN Pipeline

Provides input validation, length enforcement, and safety checks for the
MNN pipeline. Ensures all inputs meet requirements and prevents common
security and quality issues.
"""

import re
from typing import Optional


class ValidationError(ValueError):
    """Custom exception for validation errors."""
    pass


def validate_query_length(
    query: str,
    min_length: int = 1,
    max_length: int = 1000
) -> None:
    """
    Validate query length is within bounds.
    
    Args:
        query: Query string to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Raises:
        ValidationError: If query length is out of bounds
    """
    if len(query) < min_length:
        raise ValidationError(
            f"Query too short: {len(query)} characters "
            f"(minimum: {min_length})"
        )
    
    if len(query) > max_length:
        raise ValidationError(
            f"Query too long: {len(query)} characters "
            f"(maximum: {max_length})"
        )


def validate_query_characters(query: str, allowed_pattern: Optional[str] = None) -> None:
    """
    Validate query contains only allowed characters.
    
    Args:
        query: Query string to validate
        allowed_pattern: Optional regex pattern for allowed characters
                        (default: alphanumeric + common punctuation + spaces)
        
    Raises:
        ValidationError: If query contains invalid characters
    """
    if allowed_pattern is None:
        # Default: alphanumeric, spaces, and common punctuation
        allowed_pattern = r'^[a-zA-Z0-9\s.,!?\'\"-]+$'
    
    if not re.match(allowed_pattern, query):
        raise ValidationError(
            f"Query contains invalid characters. "
            f"Allowed: alphanumeric, spaces, and common punctuation"
        )


def validate_max_results(max_results: int, upper_limit: int = 100) -> None:
    """
    Validate max_results parameter.
    
    Args:
        max_results: Requested maximum results
        upper_limit: Upper limit for max_results
        
    Raises:
        ValidationError: If max_results is invalid
    """
    if max_results < 1:
        raise ValidationError(
            f"Invalid max_results: {max_results} (must be at least 1)"
        )
    
    if max_results > upper_limit:
        raise ValidationError(
            f"Invalid max_results: {max_results} (maximum: {upper_limit})"
        )


def validate_normalized_query(normalized: str) -> None:
    """
    Validate that normalized query is not empty.
    
    Args:
        normalized: Normalized query string
        
    Raises:
        ValidationError: If normalized query is empty
    """
    if not normalized or not normalized.strip():
        raise ValidationError(
            "Query cannot be empty after normalization. "
            "Please provide a query with alphanumeric characters."
        )


def sanitize_error_message(message: str, max_length: int = 200) -> str:
    """
    Sanitize error message for safe display.
    
    Removes potentially sensitive information and truncates long messages.
    
    Args:
        message: Original error message
        max_length: Maximum length for sanitized message
        
    Returns:
        Sanitized error message
    """
    # Remove file paths
    message = re.sub(r'(/[a-zA-Z0-9_/.-]+)', '[PATH]', message)
    
    # Remove IP addresses
    message = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', message)
    
    # Truncate if too long
    if len(message) > max_length:
        message = message[:max_length] + "..."
    
    return message


def enforce_output_limits(
    sequences: list,
    max_sequences: int = 1000,
    max_sequence_length: int = 10000
) -> list:
    """
    Enforce limits on generated sequences.
    
    Args:
        sequences: List of sequences to validate
        max_sequences: Maximum number of sequences allowed
        max_sequence_length: Maximum length of each sequence
        
    Returns:
        Validated sequences (possibly truncated)
        
    Raises:
        ValidationError: If limits are severely exceeded
    """
    if len(sequences) > max_sequences * 2:
        raise ValidationError(
            f"Too many sequences generated: {len(sequences)} "
            f"(reasonable limit: {max_sequences})"
        )
    
    # Truncate to max_sequences if needed
    sequences = sequences[:max_sequences]
    
    # Validate/truncate sequence lengths
    validated = []
    for seq in sequences:
        if isinstance(seq, dict) and 'sequence' in seq:
            seq_text = seq['sequence']
            if len(seq_text) > max_sequence_length:
                seq['sequence'] = seq_text[:max_sequence_length] + "..."
        validated.append(seq)
    
    return validated


def validate_full_query(
    query: str,
    min_length: int = 1,
    max_length: int = 1000,
    allowed_pattern: Optional[str] = None
) -> None:
    """
    Perform full query validation (length + characters).
    
    Args:
        query: Query string to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        allowed_pattern: Optional regex pattern for allowed characters
        
    Raises:
        ValidationError: If any validation fails
    """
    validate_query_length(query, min_length, max_length)
    validate_query_characters(query, allowed_pattern)
