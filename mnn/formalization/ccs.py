"""
Constraint Compilation Schema (CCS) Formalization

Transforms user queries into formal constraint schemas for SMT validation.
Analyzes queries to derive required tokens, domain hints, length windows, and charset requirements.

Author: MNN Engine Contributors
"""

import re
from typing import List, Dict, Set
from mnn.ir.models import ConstraintSchema


def detect_domain(query: str) -> List[str]:
    """
    Detect domain hints from the query text.
    
    Args:
        query: User query string
        
    Returns:
        List of domain hints (e.g., ['code', 'python'])
        
    Examples:
        >>> detect_domain("write a python function")
        ['code', 'python']
        >>> detect_domain("explain the algorithm")
        ['text']
    """
    query_lower = query.lower()
    domains = []
    
    # Code-related keywords
    code_keywords = {
        'function', 'class', 'method', 'algorithm', 'code', 'program',
        'script', 'implementation', 'api', 'library', 'module'
    }
    
    # Language-specific keywords
    language_map = {
        'python': ['python', 'py', 'django', 'flask', 'numpy', 'pandas'],
        'javascript': ['javascript', 'js', 'node', 'react', 'vue', 'angular'],
        'java': ['java', 'spring', 'maven', 'gradle'],
        'cpp': ['c++', 'cpp'],
        'rust': ['rust', 'cargo'],
        'go': ['golang', 'go'],
    }
    
    # Check for code-related content
    if any(keyword in query_lower for keyword in code_keywords):
        domains.append('code')
    
    # Check for specific languages
    for lang, keywords in language_map.items():
        if any(keyword in query_lower for keyword in keywords):
            domains.append(lang)
            if 'code' not in domains:
                domains.append('code')
    
    # Default to text if no specific domain detected
    if not domains:
        domains.append('text')
    
    return domains


def extract_required_tokens(query: str) -> List[str]:
    """
    Extract tokens that should appear in valid outputs.
    
    Analyzes query for explicit requirements and key terms.
    
    Args:
        query: User query string
        
    Returns:
        List of required tokens
        
    Examples:
        >>> extract_required_tokens("find pages with 'hello world'")
        ['hello', 'world']
    """
    tokens = []
    
    # Extract quoted strings as required tokens
    quoted = re.findall(r'["\']([^"\']+)["\']', query)
    for q in quoted:
        # Split quoted text into tokens
        tokens.extend(q.strip().split())
    
    # Extract significant words (length > 3, alphanumeric)
    words = re.findall(r'\b[a-z]{4,}\b', query.lower())
    
    # Filter out common stop words
    stop_words = {
        'that', 'this', 'with', 'from', 'have', 'more', 'will',
        'would', 'could', 'should', 'about', 'which', 'their',
        'there', 'these', 'those', 'when', 'where', 'what',
    }
    
    for word in words:
        if word not in stop_words and word not in tokens:
            tokens.append(word)
    
    # Limit to top tokens to avoid over-constraining
    return tokens[:10]


def infer_length_bounds(query: str, domains: List[str]) -> tuple[int, int]:
    """
    Infer appropriate length bounds based on query and domain.
    
    Args:
        query: User query string
        domains: Detected domain hints
        
    Returns:
        Tuple of (min_length, max_length)
        
    Examples:
        >>> infer_length_bounds("short snippet", ['code'])
        (10, 500)
    """
    query_lower = query.lower()
    
    # Check for explicit length hints
    if any(word in query_lower for word in ['short', 'brief', 'small', 'snippet']):
        if 'code' in domains:
            return (10, 500)
        return (10, 200)
    
    if any(word in query_lower for word in ['long', 'detailed', 'comprehensive', 'full']):
        if 'code' in domains:
            return (100, 2000)
        return (100, 1000)
    
    # Default bounds based on domain
    if 'code' in domains:
        return (20, 1000)
    
    # Text domain defaults
    return (10, 500)


def determine_charset(domains: List[str]) -> str:
    """
    Determine appropriate character set based on domains.
    
    Args:
        domains: List of domain hints
        
    Returns:
        Charset identifier ('ascii', 'alphanumeric', 'printable', 'unicode')
    """
    if 'code' in domains:
        # Code typically uses printable ASCII
        return 'printable'
    
    # Default to printable for text
    return 'printable'


def extract_code_invariants(query: str, domains: List[str]) -> Dict:
    """
    Extract code-specific invariants from query and domains.
    
    Args:
        query: User query string
        domains: Domain hints
        
    Returns:
        Dictionary of code invariants
    """
    if 'code' not in domains:
        return {}
    
    invariants = {
        'require_brace_balance': True,
        'require_keywords': [],
    }
    
    # Language-specific keywords
    keyword_map = {
        'python': ['def', 'class', 'import'],
        'javascript': ['function', 'const', 'let', 'var'],
        'java': ['class', 'public', 'void'],
        'cpp': ['void', 'int', 'class'],
        'rust': ['fn', 'let', 'mut'],
    }
    
    # Add language-specific required keywords
    for lang in domains:
        if lang in keyword_map:
            invariants['require_keywords'].extend(keyword_map[lang])
    
    return invariants


def formalize_query(query: str) -> ConstraintSchema:
    """
    Convert a user query into a formal Constraint Compilation Schema.
    
    This is the main entry point for query formalization.
    
    Args:
        query: User query string
        
    Returns:
        ConstraintSchema object with derived constraints
        
    Examples:
        >>> schema = formalize_query("write a python function")
        >>> 'code' in schema.domain_hints
        True
        >>> 'python' in schema.domain_hints
        True
    """
    # Normalize query
    query = query.strip()
    if not query:
        # Minimal constraints for empty query
        return ConstraintSchema(
            required_tokens=[],
            domain_hints=['text'],
            min_length=1,
            max_length=100,
            charset='printable',
            code_invariants={}
        )
    
    # Detect domain
    domains = detect_domain(query)
    
    # Extract required tokens
    required_tokens = extract_required_tokens(query)
    
    # Infer length bounds
    min_length, max_length = infer_length_bounds(query, domains)
    
    # Determine charset
    charset = determine_charset(domains)
    
    # Extract code invariants if applicable
    code_invariants = extract_code_invariants(query, domains)
    
    # Build and return schema
    return ConstraintSchema(
        required_tokens=required_tokens,
        domain_hints=domains,
        min_length=min_length,
        max_length=max_length,
        charset=charset,
        code_invariants=code_invariants
    )


def derive_constraints(query: str) -> ConstraintSchema:
    """
    Alias for formalize_query for backward compatibility.
    
    Args:
        query: User query string
        
    Returns:
        ConstraintSchema object
    """
    return formalize_query(query)
