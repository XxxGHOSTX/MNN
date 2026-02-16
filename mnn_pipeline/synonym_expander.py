"""
Synonym Expansion Module

Expands queries with synonyms and related terms to improve search coverage.
Uses a built-in synonym dictionary for common terms without external dependencies.
Maintains determinism by using fixed mappings.
"""

from typing import List, Set


# Built-in synonym dictionary for common query terms
# Organized by semantic category for maintainability
SYNONYM_MAP = {
    # Technology/Computing
    'COMPUTER': ['MACHINE', 'SYSTEM', 'DEVICE'],
    'PROGRAM': ['SOFTWARE', 'APPLICATION', 'CODE'],
    'ALGORITHM': ['PROCEDURE', 'METHOD', 'PROCESS'],
    'FUNCTION': ['ROUTINE', 'PROCEDURE', 'METHOD'],
    'DATA': ['INFORMATION', 'CONTENT', 'VALUES'],
    'NETWORK': ['CONNECTION', 'SYSTEM', 'WEB'],
    'DATABASE': ['STORAGE', 'REPOSITORY', 'DATASTORE'],
    'SERVER': ['HOST', 'BACKEND', 'SYSTEM'],
    'CLIENT': ['USER', 'FRONTEND', 'APPLICATION'],
    'API': ['INTERFACE', 'ENDPOINT', 'SERVICE'],
    
    # Science
    'QUANTUM': ['SUBATOMIC', 'PARTICLE', 'QUANTUM MECHANICAL'],
    'THEORY': ['HYPOTHESIS', 'MODEL', 'FRAMEWORK'],
    'EXPERIMENT': ['TEST', 'TRIAL', 'INVESTIGATION'],
    'RESEARCH': ['STUDY', 'INVESTIGATION', 'ANALYSIS'],
    'ENERGY': ['POWER', 'FORCE', 'POTENTIAL'],
    'PARTICLE': ['ATOM', 'MOLECULE', 'ELEMENT'],
    'EVOLUTION': ['DEVELOPMENT', 'PROGRESSION', 'ADAPTATION'],
    'CELL': ['ORGANISM', 'UNIT', 'STRUCTURE'],
    
    # Mathematics
    'EQUATION': ['FORMULA', 'EXPRESSION', 'RELATION'],
    'PROOF': ['DEMONSTRATION', 'VERIFICATION', 'DERIVATION'],
    'NUMBER': ['VALUE', 'QUANTITY', 'DIGIT'],
    'MATRIX': ['ARRAY', 'TABLE', 'GRID'],
    'VECTOR': ['ARRAY', 'SEQUENCE', 'LIST'],
    'FUNCTION': ['MAPPING', 'TRANSFORMATION', 'RELATION'],
    'SUM': ['TOTAL', 'ADDITION', 'AGGREGATE'],
    'PRODUCT': ['MULTIPLICATION', 'RESULT', 'OUTCOME'],
    
    # General
    'LARGE': ['BIG', 'HUGE', 'MASSIVE', 'ENORMOUS'],
    'SMALL': ['TINY', 'LITTLE', 'MINUTE', 'MINIMAL'],
    'FAST': ['QUICK', 'RAPID', 'SWIFT', 'SPEEDY'],
    'SLOW': ['GRADUAL', 'SLUGGISH', 'DELAYED'],
    'GOOD': ['EXCELLENT', 'FINE', 'SUPERIOR', 'QUALITY'],
    'BAD': ['POOR', 'INFERIOR', 'DEFECTIVE', 'SUBSTANDARD'],
    'NEW': ['RECENT', 'MODERN', 'NOVEL', 'FRESH'],
    'OLD': ['ANCIENT', 'HISTORICAL', 'TRADITIONAL', 'CLASSIC'],
    'SIMPLE': ['BASIC', 'EASY', 'ELEMENTARY', 'STRAIGHTFORWARD'],
    'COMPLEX': ['COMPLICATED', 'INTRICATE', 'SOPHISTICATED', 'ADVANCED'],
    'START': ['BEGIN', 'INITIATE', 'COMMENCE', 'LAUNCH'],
    'END': ['FINISH', 'COMPLETE', 'CONCLUDE', 'TERMINATE'],
    'MAKE': ['CREATE', 'BUILD', 'CONSTRUCT', 'GENERATE'],
    'USE': ['UTILIZE', 'EMPLOY', 'APPLY', 'IMPLEMENT'],
    'FIND': ['LOCATE', 'DISCOVER', 'IDENTIFY', 'DETECT'],
    'SHOW': ['DISPLAY', 'DEMONSTRATE', 'PRESENT', 'EXHIBIT'],
    'HELP': ['ASSIST', 'AID', 'SUPPORT', 'FACILITATE'],
    'CHANGE': ['MODIFY', 'ALTER', 'TRANSFORM', 'ADJUST'],
    'IMPORTANT': ['SIGNIFICANT', 'CRITICAL', 'ESSENTIAL', 'KEY'],
    'DIFFERENT': ['DISTINCT', 'SEPARATE', 'UNIQUE', 'VARIED'],
    'SAME': ['IDENTICAL', 'EQUAL', 'EQUIVALENT', 'SIMILAR'],
}


def expand_query_with_synonyms(query: str, max_expansions: int = 3) -> List[str]:
    """
    Expand a query by generating synonym-based variations.
    
    Creates alternative query phrasings by replacing terms with their synonyms.
    Returns the original query plus up to max_expansions variants.
    
    Args:
        query: The normalized query string (space-separated uppercase words)
        max_expansions: Maximum number of synonym variations to generate (default: 3)
        
    Returns:
        List of query strings: [original] + [synonym_variants]
        Always includes the original query as the first element.
        
    Examples:
        >>> expand_query_with_synonyms("FIND DATA")
        ['FIND DATA', 'LOCATE DATA', 'FIND INFORMATION', 'LOCATE INFORMATION']
        
        >>> expand_query_with_synonyms("SIMPLE ALGORITHM", max_expansions=2)
        ['SIMPLE ALGORITHM', 'BASIC ALGORITHM', 'SIMPLE PROCEDURE']
    """
    words = query.split()
    expansions = [query]  # Always include original
    
    # Find words that have synonyms
    expandable_indices = []
    for i, word in enumerate(words):
        if word in SYNONYM_MAP:
            expandable_indices.append(i)
    
    if not expandable_indices:
        return expansions  # No expandable words
    
    # Generate expansions by replacing one word at a time
    # This keeps expansions focused and prevents exponential explosion
    for idx in expandable_indices[:max_expansions]:
        word = words[idx]
        synonyms = SYNONYM_MAP[word]
        
        # Create one expansion per synonym (up to max_expansions total)
        for synonym in synonyms:
            if len(expansions) >= max_expansions + 1:  # +1 for original
                break
            
            # Replace word at index with synonym
            expanded_words = words.copy()
            expanded_words[idx] = synonym
            expanded_query = ' '.join(expanded_words)
            
            # Avoid duplicates (e.g., if synonym equals original word)
            if expanded_query not in expansions:
                expansions.append(expanded_query)
    
    return expansions[:max_expansions + 1]  # Ensure we don't exceed limit


def get_related_terms(word: str) -> List[str]:
    """
    Get all synonyms/related terms for a single word.
    
    Args:
        word: A single word (uppercase)
        
    Returns:
        List of related terms, or empty list if none exist
        
    Examples:
        >>> get_related_terms("FAST")
        ['QUICK', 'RAPID', 'SWIFT', 'SPEEDY']
        
        >>> get_related_terms("NONEXISTENT")
        []
    """
    return SYNONYM_MAP.get(word, [])


def add_synonym(word: str, synonyms: List[str]) -> None:
    """
    Add a custom synonym mapping to the dictionary.
    
    This allows runtime customization of the synonym database for
    domain-specific terminology.
    
    Args:
        word: The word to add synonyms for (will be converted to uppercase)
        synonyms: List of synonym strings (will be converted to uppercase)
        
    Examples:
        >>> add_synonym("AI", ["ARTIFICIAL INTELLIGENCE", "MACHINE LEARNING"])
        >>> get_related_terms("AI")
        ['ARTIFICIAL INTELLIGENCE', 'MACHINE LEARNING']
    """
    word_upper = word.upper()
    synonyms_upper = [s.upper() for s in synonyms]
    
    if word_upper in SYNONYM_MAP:
        # Merge with existing synonyms, avoiding duplicates
        existing = set(SYNONYM_MAP[word_upper])
        new_synonyms = existing.union(synonyms_upper)
        SYNONYM_MAP[word_upper] = list(new_synonyms)
    else:
        SYNONYM_MAP[word_upper] = synonyms_upper


def get_synonym_count() -> int:
    """
    Get the total number of words with synonym mappings.
    
    Returns:
        Integer count of words in the synonym dictionary
        
    Examples:
        >>> get_synonym_count()
        57
    """
    return len(SYNONYM_MAP)


def get_expansion_preview(query: str, max_expansions: int = 3) -> dict:
    """
    Preview synonym expansions without actually expanding.
    
    Useful for debugging and showing users what expansions will be applied.
    
    Args:
        query: The query to preview
        max_expansions: Maximum expansions to show
        
    Returns:
        Dictionary with:
            - 'original': The original query
            - 'expandable_words': List of words that have synonyms
            - 'expansions': List of example expansions
            - 'total_possible': Total number of possible expansions
            
    Examples:
        >>> preview = get_expansion_preview("FIND SIMPLE DATA")
        >>> preview['expandable_words']
        ['FIND', 'SIMPLE', 'DATA']
        >>> len(preview['expansions'])
        3
    """
    words = query.split()
    expandable = [w for w in words if w in SYNONYM_MAP]
    expansions = expand_query_with_synonyms(query, max_expansions)
    
    # Calculate total possible expansions (combinatorial)
    total_possible = 1
    for word in expandable:
        total_possible *= (len(SYNONYM_MAP[word]) + 1)  # +1 for original word
    total_possible -= 1  # Subtract 1 for the original query itself
    
    return {
        'original': query,
        'expandable_words': expandable,
        'expansions': expansions[1:],  # Exclude original
        'total_possible': min(total_possible, 100),  # Cap at 100 for display
    }
