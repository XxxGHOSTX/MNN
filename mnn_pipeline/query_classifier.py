"""
Query Classifier Module

Detects query class (code, scientific, mathematical, natural language) to enable
specialized sequence generation strategies. This improves relevance by tailoring
context generation to the query type.
"""

import re
from enum import Enum
from typing import Tuple


class QueryClass(Enum):
    """Enumeration of supported query classes."""
    CODE = "code"
    SCIENTIFIC = "scientific"
    MATHEMATICAL = "mathematical"
    NATURAL_LANGUAGE = "natural_language"


def classify_query(query: str) -> QueryClass:
    """
    Classify a query into one of four categories based on content analysis.
    
    This enables specialized handling for different query types:
    - CODE: Programming-related queries (functions, variables, syntax)
    - SCIENTIFIC: Scientific terms and concepts
    - MATHEMATICAL: Mathematical expressions and notation
    - NATURAL_LANGUAGE: General queries (default)
    
    Classification is deterministic and based on pattern matching.
    
    Args:
        query: The normalized query string (uppercase)
        
    Returns:
        QueryClass enum indicating the detected class
        
    Examples:
        >>> classify_query("FUNCTION FIBONACCI")
        QueryClass.CODE
        >>> classify_query("QUANTUM ENTANGLEMENT")
        QueryClass.SCIENTIFIC
        >>> classify_query("X SQUARED PLUS Y")
        QueryClass.MATHEMATICAL
        >>> classify_query("HELLO WORLD")
        QueryClass.NATURAL_LANGUAGE
    """
    query_lower = query.lower()
    
    # Code patterns: programming keywords, syntax elements
    code_patterns = [
        r'\b(function|def|class|import|return|if|else|for|while|try|catch)\b',
        r'\b(variable|parameter|argument|method|object|array|list|dict)\b',
        r'\b(algorithm|recursion|iteration|loop|pointer|reference)\b',
        r'\b(python|javascript|java|cpp|rust|golang)\b',
        r'[{}()\[\];]',  # Code punctuation
        r'\b(api|http|rest|json|xml|sql|database)\b',
    ]
    
    for pattern in code_patterns:
        if re.search(pattern, query_lower):
            return QueryClass.CODE
    
    # Scientific patterns: scientific terminology
    scientific_patterns = [
        r'\b(quantum|particle|atom|molecule|electron|proton|neutron)\b',
        r'\b(theory|hypothesis|experiment|observation|empirical)\b',
        r'\b(physics|chemistry|biology|astronomy|cosmology)\b',
        r'\b(energy|mass|velocity|acceleration|force|momentum)\b',
        r'\b(dna|rna|protein|cell|organism|species|evolution)\b',
        r'\b(planet|star|galaxy|universe|light year|nebula)\b',
        r'\b(scientific|research|study|analysis|discovery)\b',
    ]
    
    for pattern in scientific_patterns:
        if re.search(pattern, query_lower):
            return QueryClass.SCIENTIFIC
    
    # Mathematical patterns: math notation and terms
    mathematical_patterns = [
        r'\b(equation|formula|theorem|proof|lemma|corollary)\b',
        r'\b(sum|product|derivative|integral|limit|infinity)\b',
        r'\b(matrix|vector|tensor|scalar|dimension)\b',
        r'\b(prime|composite|factor|divisor|multiple)\b',
        r'\b(algebra|geometry|calculus|trigonometry|statistics)\b',
        r'\b(plus|minus|times|divided|equals|squared|cubed)\b',
        r'[+\-*/=<>≤≥≠∑∏∫]',  # Math operators
        r'\b(x|y|z)\b.*\b(x|y|z)\b',  # Multiple variables
    ]
    
    for pattern in mathematical_patterns:
        if re.search(pattern, query_lower):
            return QueryClass.MATHEMATICAL
    
    # Default: Natural language
    return QueryClass.NATURAL_LANGUAGE


def get_query_metadata(query: str) -> Tuple[QueryClass, dict]:
    """
    Classify query and return metadata for specialized handling.
    
    Args:
        query: The normalized query string
        
    Returns:
        Tuple of (QueryClass, metadata_dict) where metadata contains:
            - 'class': QueryClass enum
            - 'class_name': String representation
            - 'context_prefix': Suggested context prefix
            - 'context_suffix': Suggested context suffix
            
    Examples:
        >>> cls, meta = get_query_metadata("FUNCTION SORT")
        >>> meta['class_name']
        'code'
        >>> meta['context_prefix']
        'IMPLEMENTATION OF'
    """
    query_class = classify_query(query)
    
    # Context templates for each query class
    context_templates = {
        QueryClass.CODE: {
            'context_prefix': 'IMPLEMENTATION OF',
            'context_suffix': 'WITH OPTIMAL COMPLEXITY',
            'examples': ['FUNCTION', 'ALGORITHM', 'DATA STRUCTURE'],
        },
        QueryClass.SCIENTIFIC: {
            'context_prefix': 'RESEARCH ON',
            'context_suffix': 'IN MODERN SCIENCE',
            'examples': ['THEORY', 'EXPERIMENT', 'OBSERVATION'],
        },
        QueryClass.MATHEMATICAL: {
            'context_prefix': 'PROOF OF',
            'context_suffix': 'USING MATHEMATICAL RIGOR',
            'examples': ['THEOREM', 'EQUATION', 'FORMULA'],
        },
        QueryClass.NATURAL_LANGUAGE: {
            'context_prefix': 'DISCUSSION OF',
            'context_suffix': 'IN GENERAL CONTEXT',
            'examples': ['CONCEPT', 'IDEA', 'TOPIC'],
        },
    }
    
    template = context_templates[query_class]
    
    metadata = {
        'class': query_class,
        'class_name': query_class.value,
        'context_prefix': template['context_prefix'],
        'context_suffix': template['context_suffix'],
        'examples': template['examples'],
    }
    
    return query_class, metadata
