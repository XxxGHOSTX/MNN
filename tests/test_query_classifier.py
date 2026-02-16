"""
Tests for Query Classification Module

Tests the query classifier's ability to detect code, scientific, mathematical,
and natural language queries deterministically.
"""

import unittest
from mnn_pipeline.query_classifier import (
    classify_query,
    get_query_metadata,
    QueryClass,
)


class TestQueryClassifier(unittest.TestCase):
    """Test cases for query classification functionality."""
    
    def test_classify_code_query(self):
        """Test classification of code-related queries."""
        queries = [
            "FUNCTION FIBONACCI",
            "ALGORITHM QUICKSORT",
            "PYTHON DICT COMPREHENSION",
            "API ENDPOINT DESIGN",
            "CLASS INHERITANCE",
        ]
        
        for query in queries:
            with self.subTest(query=query):
                result = classify_query(query)
                self.assertEqual(result, QueryClass.CODE)
    
    def test_classify_scientific_query(self):
        """Test classification of scientific queries."""
        queries = [
            "QUANTUM ENTANGLEMENT",
            "PARTICLE PHYSICS",
            "DNA REPLICATION",
            "EVOLUTION THEORY",
            "COSMOLOGY STUDY",
        ]
        
        for query in queries:
            with self.subTest(query=query):
                result = classify_query(query)
                self.assertEqual(result, QueryClass.SCIENTIFIC)
    
    def test_classify_mathematical_query(self):
        """Test classification of mathematical queries."""
        queries = [
            "PYTHAGOREAN THEOREM",
            "DERIVATIVE CALCULUS",
            "MATRIX MULTIPLICATION",
            "PRIME NUMBER PROOF",
            "X SQUARED PLUS Y",
        ]
        
        for query in queries:
            with self.subTest(query=query):
                result = classify_query(query)
                self.assertEqual(result, QueryClass.MATHEMATICAL)
    
    def test_classify_natural_language_query(self):
        """Test classification of general natural language queries."""
        queries = [
            "HELLO WORLD",
            "ARTIFICIAL INTELLIGENCE",
            "MACHINE LEARNING",
            "SEARCH ENGINE",
            "CLOUD COMPUTING",
        ]
        
        for query in queries:
            with self.subTest(query=query):
                result = classify_query(query)
                self.assertEqual(result, QueryClass.NATURAL_LANGUAGE)
    
    def test_deterministic_classification(self):
        """Test that classification is deterministic."""
        query = "QUANTUM ALGORITHM"
        
        # Should classify as CODE (algorithm keyword takes precedence)
        result1 = classify_query(query)
        result2 = classify_query(query)
        result3 = classify_query(query)
        
        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)
    
    def test_get_query_metadata(self):
        """Test metadata retrieval for classified queries."""
        query = "FUNCTION SORT"
        query_class, metadata = get_query_metadata(query)
        
        self.assertEqual(query_class, QueryClass.CODE)
        self.assertEqual(metadata['class'], QueryClass.CODE)
        self.assertEqual(metadata['class_name'], 'code')
        self.assertIn('context_prefix', metadata)
        self.assertIn('context_suffix', metadata)
        self.assertEqual(metadata['context_prefix'], 'IMPLEMENTATION OF')
    
    def test_metadata_scientific(self):
        """Test metadata for scientific queries."""
        query = "QUANTUM PHYSICS"
        query_class, metadata = get_query_metadata(query)
        
        self.assertEqual(query_class, QueryClass.SCIENTIFIC)
        self.assertEqual(metadata['context_prefix'], 'RESEARCH ON')
        self.assertIn('SCIENCE', metadata['context_suffix'])
    
    def test_metadata_mathematical(self):
        """Test metadata for mathematical queries."""
        query = "THEOREM PROOF"
        query_class, metadata = get_query_metadata(query)
        
        self.assertEqual(query_class, QueryClass.MATHEMATICAL)
        self.assertEqual(metadata['context_prefix'], 'PROOF OF')
        self.assertIn('RIGOR', metadata['context_suffix'])
    
    def test_metadata_natural_language(self):
        """Test metadata for natural language queries."""
        query = "HELLO WORLD"
        query_class, metadata = get_query_metadata(query)
        
        self.assertEqual(query_class, QueryClass.NATURAL_LANGUAGE)
        self.assertEqual(metadata['context_prefix'], 'DISCUSSION OF')
    
    def test_case_insensitivity(self):
        """Test that classification is case-insensitive."""
        queries_pairs = [
            ("FUNCTION TEST", "function test"),
            ("QUANTUM PHYSICS", "Quantum Physics"),
            ("THEOREM PROOF", "ThEoReM pRoOf"),
        ]
        
        for upper, lower in queries_pairs:
            with self.subTest(upper=upper, lower=lower):
                result_upper = classify_query(upper)
                result_lower = classify_query(lower)
                self.assertEqual(result_upper, result_lower)
    
    def test_empty_query_defaults_to_natural_language(self):
        """Test that empty or unclassifiable queries default to natural language."""
        queries = [
            "",
            "   ",
            "ZZZZZ QQQQQ",  # Nonsense words
            "123 456",  # Numbers only
        ]
        
        for query in queries:
            with self.subTest(query=query):
                result = classify_query(query)
                self.assertEqual(result, QueryClass.NATURAL_LANGUAGE)
    
    def test_priority_code_over_scientific(self):
        """Test that code keywords take priority when ambiguous."""
        # "ALGORITHM" is a code keyword
        query = "QUANTUM ALGORITHM"
        result = classify_query(query)
        self.assertEqual(result, QueryClass.CODE)
    
    def test_priority_code_over_mathematical(self):
        """Test that code keywords take priority over mathematical."""
        # "FUNCTION" can be both code and math, but code comes first
        query = "FUNCTION DERIVATIVE"
        result = classify_query(query)
        self.assertEqual(result, QueryClass.CODE)


if __name__ == '__main__':
    unittest.main()
