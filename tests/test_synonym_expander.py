"""
Tests for Synonym Expansion Module

Tests the synonym expander's ability to generate query variations
deterministically for improved search coverage.
"""

import unittest
from mnn_pipeline.synonym_expander import (
    expand_query_with_synonyms,
    get_related_terms,
    add_synonym,
    get_synonym_count,
    get_expansion_preview,
)


class TestSynonymExpander(unittest.TestCase):
    """Test cases for synonym expansion functionality."""
    
    def test_expand_query_single_word(self):
        """Test expansion of single-word query."""
        query = "FAST"
        expansions = expand_query_with_synonyms(query, max_expansions=3)
        
        # Should include original + up to 3 expansions
        self.assertIn(query, expansions)
        self.assertEqual(expansions[0], query)  # Original is first
        self.assertGreater(len(expansions), 1)  # At least one expansion
        self.assertLessEqual(len(expansions), 4)  # Original + 3 max
    
    def test_expand_query_multiple_words(self):
        """Test expansion of multi-word query."""
        query = "FAST ALGORITHM"
        expansions = expand_query_with_synonyms(query, max_expansions=3)
        
        self.assertIn(query, expansions)
        self.assertEqual(expansions[0], query)
        
        # Should have some expansions with synonyms
        self.assertGreater(len(expansions), 1)
    
    def test_expansion_deterministic(self):
        """Test that expansion is deterministic."""
        query = "SIMPLE DATA"
        
        result1 = expand_query_with_synonyms(query, max_expansions=3)
        result2 = expand_query_with_synonyms(query, max_expansions=3)
        result3 = expand_query_with_synonyms(query, max_expansions=3)
        
        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)
    
    def test_no_expansion_for_unknown_words(self):
        """Test that queries with no known synonyms return only original."""
        query = "ZZZZZ QQQQQ"  # Nonsense words
        expansions = expand_query_with_synonyms(query, max_expansions=3)
        
        self.assertEqual(len(expansions), 1)
        self.assertEqual(expansions[0], query)
    
    def test_max_expansions_limit(self):
        """Test that max_expansions parameter is respected."""
        query = "FAST SIMPLE GOOD"  # Many expandable words
        
        expansions_1 = expand_query_with_synonyms(query, max_expansions=1)
        expansions_3 = expand_query_with_synonyms(query, max_expansions=3)
        expansions_10 = expand_query_with_synonyms(query, max_expansions=10)
        
        self.assertLessEqual(len(expansions_1), 2)  # Original + 1
        self.assertLessEqual(len(expansions_3), 4)  # Original + 3
        self.assertLessEqual(len(expansions_10), 11)  # Original + 10
    
    def test_get_related_terms(self):
        """Test retrieval of related terms for a single word."""
        terms = get_related_terms("FAST")
        
        self.assertIsInstance(terms, list)
        self.assertGreater(len(terms), 0)
        self.assertIn("QUICK", terms)
        self.assertIn("RAPID", terms)
    
    def test_get_related_terms_unknown_word(self):
        """Test that unknown words return empty list."""
        terms = get_related_terms("NONEXISTENT")
        
        self.assertIsInstance(terms, list)
        self.assertEqual(len(terms), 0)
    
    def test_add_synonym(self):
        """Test adding custom synonyms."""
        # Get initial count
        initial_count = get_synonym_count()
        
        # Add a new synonym
        add_synonym("TESTWORD", ["SYNONYM1", "SYNONYM2"])
        
        # Verify it was added
        terms = get_related_terms("TESTWORD")
        self.assertIn("SYNONYM1", terms)
        self.assertIn("SYNONYM2", terms)
        
        # Count should increase if word was new
        new_count = get_synonym_count()
        self.assertGreaterEqual(new_count, initial_count)
    
    def test_add_synonym_merges_with_existing(self):
        """Test that adding synonyms to existing word merges lists."""
        # Add initial synonyms
        add_synonym("MERGETEST", ["SYN1", "SYN2"])
        
        # Add more synonyms to same word
        add_synonym("MERGETEST", ["SYN3", "SYN4"])
        
        # Should have all synonyms
        terms = get_related_terms("MERGETEST")
        self.assertIn("SYN1", terms)
        self.assertIn("SYN2", terms)
        self.assertIn("SYN3", terms)
        self.assertIn("SYN4", terms)
    
    def test_get_synonym_count(self):
        """Test that synonym count returns valid number."""
        count = get_synonym_count()
        
        self.assertIsInstance(count, int)
        self.assertGreater(count, 0)  # Should have built-in synonyms
    
    def test_expansion_preview(self):
        """Test preview of expansions without actually expanding."""
        query = "FIND SIMPLE DATA"
        preview = get_expansion_preview(query, max_expansions=2)
        
        self.assertEqual(preview['original'], query)
        self.assertIn('expandable_words', preview)
        self.assertIn('expansions', preview)
        self.assertIn('total_possible', preview)
        
        # Should identify expandable words
        self.assertGreater(len(preview['expandable_words']), 0)
        self.assertIn('FIND', preview['expandable_words'])
    
    def test_expansion_preview_no_expandable_words(self):
        """Test preview for query with no expandable words."""
        query = "ZZZZZ QQQQQ"
        preview = get_expansion_preview(query, max_expansions=2)
        
        self.assertEqual(preview['original'], query)
        self.assertEqual(len(preview['expandable_words']), 0)
        self.assertEqual(len(preview['expansions']), 0)
        self.assertEqual(preview['total_possible'], 0)
    
    def test_expansions_contain_original_words(self):
        """Test that expansions maintain original word structure."""
        query = "FAST ALGORITHM"
        expansions = expand_query_with_synonyms(query, max_expansions=3)
        
        # Each expansion should be 2 words
        for expansion in expansions:
            words = expansion.split()
            self.assertEqual(len(words), 2)
    
    def test_no_duplicate_expansions(self):
        """Test that duplicate expansions are avoided."""
        query = "SIMPLE TEST"
        expansions = expand_query_with_synonyms(query, max_expansions=5)
        
        # Convert to set and compare length
        unique_expansions = set(expansions)
        self.assertEqual(len(expansions), len(unique_expansions))
    
    def test_common_synonyms_exist(self):
        """Test that common words have synonym mappings."""
        common_words = [
            "FAST", "SLOW", "GOOD", "BAD", "LARGE", "SMALL",
            "SIMPLE", "COMPLEX", "START", "END", "MAKE", "USE",
        ]
        
        for word in common_words:
            with self.subTest(word=word):
                terms = get_related_terms(word)
                self.assertGreater(len(terms), 0, f"{word} should have synonyms")
    
    def test_technical_synonyms_exist(self):
        """Test that technical terms have synonym mappings."""
        technical_words = [
            "ALGORITHM", "FUNCTION", "DATA", "NETWORK",
            "QUANTUM", "THEORY", "EQUATION", "MATRIX",
        ]
        
        for word in technical_words:
            with self.subTest(word=word):
                terms = get_related_terms(word)
                self.assertGreater(len(terms), 0, f"{word} should have synonyms")


if __name__ == '__main__':
    unittest.main()
