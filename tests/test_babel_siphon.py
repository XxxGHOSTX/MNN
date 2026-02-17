"""
Tests for SMT-Arbiter Babel Siphon Pipeline

Tests for determinism, validation, repair, scoring, and complete pipeline execution.

Author: MNN Engine Contributors
"""

import unittest
from mnn.ir.models import ConstraintSchema, Candidate, BreachCoordinates
from mnn.core.seed_registry import SeedRegistry, deterministic_hash
from mnn.formalization.ccs import formalize_query, detect_domain, extract_required_tokens
from mnn.core.semantic_lattice import SemanticLattice, generate_candidates
from mnn.solver.smt_solver import SMTSolver, validate_candidate, repair_candidate
from mnn.scoring.ranker import Ranker, score_and_rank_candidates
from mnn.babel_siphon import BabelSiphonPipeline, run_babel_siphon_pipeline


class TestIRModels(unittest.TestCase):
    """Test IR model validation and constraints."""
    
    def test_constraint_schema_creation(self):
        """Test ConstraintSchema creation with valid data."""
        schema = ConstraintSchema(
            required_tokens=['hello'],
            domain_hints=['text'],
            min_length=10,
            max_length=100,
            charset='printable'
        )
        self.assertEqual(schema.min_length, 10)
        self.assertEqual(schema.max_length, 100)
        self.assertIn('hello', schema.required_tokens)
    
    def test_constraint_schema_validation(self):
        """Test ConstraintSchema length validation."""
        with self.assertRaises(ValueError):
            # max_length < min_length should fail
            ConstraintSchema(min_length=100, max_length=50)
    
    def test_candidate_creation(self):
        """Test Candidate creation."""
        candidate = Candidate(
            content='test content',
            seed=42,
            generation_step=0
        )
        self.assertEqual(candidate.content, 'test content')
        self.assertEqual(candidate.seed, 42)
    
    def test_breach_coordinates_repairable(self):
        """Test breach repairability logic."""
        # Few violations - repairable
        breach = BreachCoordinates(
            violated_constraints=['length_too_short'],
            missing_tokens=['hello']
        )
        self.assertTrue(breach.is_repairable())
        
        # Too many violations - not repairable
        breach = BreachCoordinates(
            violated_constraints=['v1', 'v2', 'v3', 'v4', 'v5', 'v6']
        )
        self.assertFalse(breach.is_repairable())


class TestSeedRegistry(unittest.TestCase):
    """Test deterministic seed management."""
    
    def test_deterministic_hash(self):
        """Test that hash is deterministic."""
        h1 = deterministic_hash('test')
        h2 = deterministic_hash('test')
        self.assertEqual(h1, h2)
    
    def test_different_inputs_different_hashes(self):
        """Test that different inputs produce different hashes."""
        h1 = deterministic_hash('a')
        h2 = deterministic_hash('b')
        self.assertNotEqual(h1, h2)
    
    def test_seed_derivation(self):
        """Test deterministic seed derivation."""
        registry = SeedRegistry(base_seed=42)
        seed1 = registry.derive_seed('context1')
        seed2 = registry.derive_seed('context1')
        self.assertEqual(seed1, seed2)
    
    def test_seed_sequence(self):
        """Test deterministic seed sequence generation."""
        registry = SeedRegistry(base_seed=100)
        seq1 = registry.get_sequence(5)
        seq2 = registry.get_sequence(5)
        self.assertEqual(seq1, seq2)


class TestFormalization(unittest.TestCase):
    """Test query formalization to CCS."""
    
    def test_detect_text_domain(self):
        """Test text domain detection."""
        domains = detect_domain('explain the concept')
        self.assertIn('text', domains)
    
    def test_detect_code_domain(self):
        """Test code domain detection."""
        domains = detect_domain('write a python function')
        self.assertIn('code', domains)
        self.assertIn('python', domains)
    
    def test_extract_required_tokens(self):
        """Test token extraction."""
        tokens = extract_required_tokens('find hello world')
        self.assertIn('hello', tokens)
        self.assertIn('world', tokens)
    
    def test_formalize_query_text(self):
        """Test text query formalization."""
        schema = formalize_query('hello world')
        self.assertIn('text', schema.domain_hints)
        self.assertGreater(schema.min_length, 0)
        self.assertGreater(schema.max_length, schema.min_length)
    
    def test_formalize_query_code(self):
        """Test code query formalization."""
        schema = formalize_query('write a python function')
        self.assertIn('code', schema.domain_hints)
        self.assertIn('python', schema.domain_hints)
        self.assertTrue(schema.code_invariants.get('require_brace_balance', False))


class TestSemanticLattice(unittest.TestCase):
    """Test candidate generation."""
    
    def test_generate_candidates(self):
        """Test candidate generation."""
        schema = ConstraintSchema(min_length=10, max_length=50)
        lattice = SemanticLattice(schema, seed=42)
        candidates = list(lattice.propose_candidates(count=5))
        self.assertEqual(len(candidates), 5)
        for candidate in candidates:
            self.assertIsInstance(candidate, Candidate)
    
    def test_deterministic_generation(self):
        """Test that generation is deterministic."""
        schema = ConstraintSchema(min_length=10, max_length=50)
        candidates1 = generate_candidates(schema, seed=42, count=5)
        candidates2 = generate_candidates(schema, seed=42, count=5)
        
        for c1, c2 in zip(candidates1, candidates2):
            self.assertEqual(c1.content, c2.content)


class TestSMTSolver(unittest.TestCase):
    """Test SMT validation and repair."""
    
    def test_validate_valid_candidate(self):
        """Test validation of valid candidate."""
        schema = ConstraintSchema(
            required_tokens=['hello'],
            min_length=5,
            max_length=100
        )
        candidate = Candidate(
            content='hello world',
            seed=42,
            generation_step=0
        )
        solver = SMTSolver(schema)
        is_valid, breach = solver.validate(candidate)
        self.assertTrue(is_valid)
        self.assertIsNone(breach)
    
    def test_validate_missing_token(self):
        """Test validation failure for missing token."""
        schema = ConstraintSchema(
            required_tokens=['hello'],
            min_length=5,
            max_length=100
        )
        candidate = Candidate(
            content='world only',
            seed=42,
            generation_step=0
        )
        solver = SMTSolver(schema)
        is_valid, breach = solver.validate(candidate)
        self.assertFalse(is_valid)
        self.assertIsNotNone(breach)
        self.assertIn('hello', breach.missing_tokens)
    
    def test_validate_length_violation(self):
        """Test validation failure for length."""
        schema = ConstraintSchema(min_length=20, max_length=100)
        candidate = Candidate(content='short', seed=42, generation_step=0)
        solver = SMTSolver(schema)
        is_valid, breach = solver.validate(candidate)
        self.assertFalse(is_valid)
        self.assertEqual(breach.length_violation, 'too_short')
    
    def test_repair_candidate(self):
        """Test candidate repair."""
        schema = ConstraintSchema(min_length=20, max_length=100)
        candidate = Candidate(content='short', seed=42, generation_step=0)
        breach = BreachCoordinates(
            violated_constraints=['length_too_short'],
            length_violation='too_short',
            repair_hints=['pad_to_20']
        )
        repaired = repair_candidate(candidate, breach, schema)
        self.assertIsNotNone(repaired)
        self.assertGreaterEqual(len(repaired.content), 20)


class TestRanker(unittest.TestCase):
    """Test scoring and ranking."""
    
    def test_score_candidate(self):
        """Test candidate scoring."""
        schema = ConstraintSchema(
            required_tokens=['test'],
            min_length=10,
            max_length=100
        )
        candidate = Candidate(
            content='test content here',
            seed=42,
            generation_step=0
        )
        ranker = Ranker(schema)
        score = ranker.score(candidate)
        self.assertGreater(score, 0)
    
    def test_rank_candidates(self):
        """Test candidate ranking."""
        schema = ConstraintSchema(min_length=5, max_length=50)
        candidates = [
            Candidate(content='short', seed=42, generation_step=0),
            Candidate(content='this is longer content', seed=42, generation_step=1),
        ]
        ranker = Ranker(schema)
        ranked = ranker.rank(candidates)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]['rank'], 1)
        self.assertEqual(ranked[1]['rank'], 2)
    
    def test_deterministic_ranking(self):
        """Test that ranking is deterministic."""
        schema = ConstraintSchema(min_length=5, max_length=50)
        candidates = [
            Candidate(content='test1', seed=42, generation_step=i)
            for i in range(5)
        ]
        ranked1 = score_and_rank_candidates(candidates, schema)
        ranked2 = score_and_rank_candidates(candidates, schema)
        
        for r1, r2 in zip(ranked1, ranked2):
            self.assertEqual(r1['score'], r2['score'])
            self.assertEqual(r1['rank'], r2['rank'])


class TestBabelSiphonPipeline(unittest.TestCase):
    """Test complete pipeline execution."""
    
    def test_pipeline_success(self):
        """Test successful pipeline execution."""
        pipeline = BabelSiphonPipeline(base_seed=42, max_candidates=20, top_n=5)
        result = pipeline.run('hello world')
        self.assertIn('status', result)
        self.assertIn(result['status'], ['success', 'no_valid_candidates'])
        
        if result['status'] == 'success':
            self.assertIn('results', result)
            self.assertGreater(len(result['results']), 0)
    
    def test_pipeline_determinism(self):
        """Test that pipeline is deterministic."""
        pipeline = BabelSiphonPipeline(base_seed=42, max_candidates=20, top_n=3)
        result1 = pipeline.run('test query')
        result2 = pipeline.run('test query')
        
        # Results should be identical
        self.assertEqual(result1, result2)
    
    def test_pipeline_statistics(self):
        """Test that statistics are included."""
        pipeline = BabelSiphonPipeline(base_seed=42, max_candidates=10)
        result = pipeline.run('test')
        self.assertIn('statistics', result)
        self.assertIn('candidates_generated', result['statistics'])
    
    def test_convenience_function(self):
        """Test convenience function."""
        result = run_babel_siphon_pipeline('hello', base_seed=42, max_candidates=10, top_n=3)
        self.assertIn('status', result)
    
    def test_no_valid_candidates(self):
        """Test handling of unsatisfiable constraints."""
        # Create very strict constraints that are unlikely to be satisfied
        pipeline = BabelSiphonPipeline(base_seed=42, max_candidates=5)
        result = pipeline.run('extremely specific nonexistent requirements')
        
        # Should handle gracefully without emitting noise
        self.assertIn('status', result)
        if result['status'] == 'no_valid_candidates':
            self.assertIn('message', result)
            self.assertNotIn('results', result)


if __name__ == '__main__':
    unittest.main()
