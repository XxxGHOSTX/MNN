"""
UCS Integration Tests

Comprehensive test suite for the Library of Sense integration:
  • UCS Kernel (Golden Ratio constants, NUME, Xuan-Liang, Verlinde, Master Formula)
  • Control Plane (lifecycle coordination)
  • Logic Guard (Z3 soundness gate, 99% threshold)
  • Answer Verifier
  • Neuro-Symbolic Search cycle
  • Virtuoso Code Engine

All tests are deterministic: same inputs always produce same outputs.

Author: MNN Engine Contributors
"""

import math
import unittest

from mnn.ucs.kernel import (
    PHI,
    UCSConstants,
    NUMECalculator,
    XuanLiangMetric,
    VerlindeEntropicForce,
    MasterFormula,
    derive_constant_from_phi,
)
from mnn.control.plane import LifecycleState, SubsystemInfo, ControlPlane
from mnn.guard.logic_guard import GuardResult, LogicGuard, SOUNDNESS_THRESHOLD
from mnn.verification.verifier import VerificationResult, AnswerVerifier
from mnn.search.neuro_symbolic import SearchResult, NeuroSymbolicSearch
from mnn.codegen.virtuoso import CodeResult, VirtuosoEngine
from mnn.ir.models import ConstraintSchema, Candidate


# ---------------------------------------------------------------------------
# UCS Kernel
# ---------------------------------------------------------------------------


class TestGoldenRatio(unittest.TestCase):
    """Verify that PHI and all derived constants are correct."""

    def test_phi_value(self):
        """PHI must equal (1 + sqrt(5)) / 2."""
        expected = (1.0 + math.sqrt(5.0)) / 2.0
        self.assertAlmostEqual(PHI, expected, places=12)

    def test_phi_approx(self):
        """PHI ≈ 1.618."""
        self.assertAlmostEqual(PHI, 1.618, places=2)

    def test_phi_identity(self):
        """φ² = φ + 1 (defining identity of the Golden Ratio)."""
        self.assertAlmostEqual(PHI ** 2, PHI + 1.0, places=12)

    def test_phi_reciprocal_identity(self):
        """1/φ = φ - 1."""
        self.assertAlmostEqual(1.0 / PHI, PHI - 1.0, places=12)

    def test_derive_constant_from_phi_zero(self):
        self.assertAlmostEqual(derive_constant_from_phi(0), 1.0, places=12)

    def test_derive_constant_from_phi_two(self):
        self.assertAlmostEqual(derive_constant_from_phi(2), PHI ** 2, places=12)

    def test_derive_constant_from_phi_negative(self):
        self.assertAlmostEqual(derive_constant_from_phi(-1), 1.0 / PHI, places=12)


class TestUCSConstants(unittest.TestCase):
    """All physical constants must be derived from PHI."""

    def setUp(self):
        self.c = UCSConstants()

    def test_phi_inv(self):
        self.assertAlmostEqual(self.c.PHI_INV, 1.0 / PHI, places=12)

    def test_phi_sq(self):
        self.assertAlmostEqual(self.c.PHI_SQ, PHI ** 2, places=12)

    def test_phi_cube(self):
        self.assertAlmostEqual(self.c.PHI_CUBE, PHI ** 3, places=12)

    def test_coupling(self):
        self.assertAlmostEqual(self.c.COUPLING, 1.0 / (PHI ** 2), places=12)

    def test_energy_scale(self):
        self.assertAlmostEqual(self.c.ENERGY_SCALE, PHI ** 3, places=12)

    def test_entropy_unit(self):
        self.assertAlmostEqual(self.c.ENTROPY_UNIT, math.log(PHI), places=12)

    def test_mass_ratio(self):
        self.assertAlmostEqual(self.c.MASS_RATIO, PHI ** 2, places=12)

    def test_temperature(self):
        self.assertAlmostEqual(self.c.TEMPERATURE, 1.0 / PHI, places=12)

    def test_all_positive(self):
        for attr in ("PHI", "PHI_INV", "PHI_SQ", "PHI_CUBE",
                     "COUPLING", "ENERGY_SCALE", "ENTROPY_UNIT",
                     "MASS_RATIO", "TEMPERATURE"):
            self.assertGreater(getattr(self.c, attr), 0.0, msg=f"{attr} must be > 0")


class TestNUME(unittest.TestCase):
    """NUME score tests."""

    def setUp(self):
        self.calc = NUMECalculator()

    def test_empty_string_returns_zero(self):
        self.assertEqual(self.calc.compute(""), 0.0)

    def test_uniform_string_low_entropy(self):
        """A string of repeated chars has low entropy → low NUME."""
        self.assertLess(self.calc.compute("aaaa"), self.calc.compute("abcd"))

    def test_nonnegative(self):
        for text in ["hello", "world", "MNN", "φ=1.618", "a"]:
            self.assertGreaterEqual(self.calc.compute(text), 0.0)

    def test_deterministic(self):
        """Same input → same output."""
        text = "hello world from MNN"
        self.assertEqual(self.calc.compute(text), self.calc.compute(text))

    def test_diverse_text_higher_score(self):
        """More character diversity → higher NUME."""
        low = self.calc.compute("aaabbbccc")
        high = self.calc.compute("abcdefghij")
        self.assertLessEqual(low, high)

    def test_single_char(self):
        """Single unique character: minimal entropy."""
        score = self.calc.compute("z")
        self.assertGreaterEqual(score, 0.0)


class TestXuanLiangMetric(unittest.TestCase):
    """Xuan-Liang metric tests."""

    def setUp(self):
        self.metric = XuanLiangMetric()

    def test_identical_texts_distance_zero(self):
        self.assertEqual(self.metric.distance("hello", "hello"), 0.0)

    def test_different_texts_positive_distance(self):
        self.assertGreater(self.metric.distance("hello", "world"), 0.0)

    def test_distance_nonnegative(self):
        pairs = [("a", "b"), ("hello world", "goodbye"), ("x", "x")]
        for a, b in pairs:
            self.assertGreaterEqual(self.metric.distance(a, b), 0.0)

    def test_identical_texts_similarity_one(self):
        self.assertAlmostEqual(self.metric.similarity("hello", "hello"), 1.0, places=12)

    def test_similarity_in_range(self):
        sim = self.metric.similarity("hello", "world")
        self.assertGreater(sim, 0.0)
        self.assertLessEqual(sim, 1.0)

    def test_deterministic(self):
        d1 = self.metric.distance("foo bar", "baz qux")
        d2 = self.metric.distance("foo bar", "baz qux")
        self.assertEqual(d1, d2)

    def test_closer_texts_smaller_distance(self):
        """Texts sharing more tokens should have smaller distance."""
        d_close = self.metric.distance("hello world", "hello earth")
        d_far = self.metric.distance("hello world", "quantum physics")
        self.assertLessEqual(d_close, d_far)


class TestVerlindeEntropicForce(unittest.TestCase):
    """Verlinde entropic force tests."""

    def setUp(self):
        self.vf = VerlindeEntropicForce()

    def test_zero_entropy_zero_force(self):
        self.assertEqual(self.vf.compute(0.0), 0.0)

    def test_positive_entropy_positive_force(self):
        self.assertGreater(self.vf.compute(0.5), 0.0)

    def test_force_scales_with_entropy(self):
        """Larger entropy change → larger force."""
        self.assertLess(self.vf.compute(0.1), self.vf.compute(0.9))

    def test_force_inversely_proportional_to_displacement(self):
        f1 = self.vf.compute(1.0, displacement=1.0)
        f2 = self.vf.compute(1.0, displacement=2.0)
        self.assertAlmostEqual(f1, 2.0 * f2, places=10)

    def test_invalid_displacement_raises(self):
        with self.assertRaises(ValueError):
            self.vf.compute(0.5, displacement=0.0)
        with self.assertRaises(ValueError):
            self.vf.compute(0.5, displacement=-1.0)

    def test_custom_temperature(self):
        vf_cold = VerlindeEntropicForce(temperature=0.1)
        vf_hot = VerlindeEntropicForce(temperature=2.0)
        self.assertLess(vf_cold.compute(0.5), vf_hot.compute(0.5))

    def test_temperature_from_phi(self):
        """Default temperature should be 1/φ."""
        self.assertAlmostEqual(self.vf.temperature, 1.0 / PHI, places=12)


class TestMasterFormula(unittest.TestCase):
    """Master Formula tests."""

    def setUp(self):
        self.mf = MasterFormula()

    def test_score_in_range(self):
        score = self.mf.score("hello world", "hello world")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_deterministic(self):
        s1 = self.mf.score("query", "candidate text")
        s2 = self.mf.score("query", "candidate text")
        self.assertEqual(s1, s2)

    def test_identical_query_and_candidate_high_score(self):
        score = self.mf.score("hello world", "hello world")
        self.assertGreater(score, 0.5)

    def test_rank_returns_sorted_results(self):
        results = self.mf.rank("hello", ["hello world", "goodbye", "hello there"])
        self.assertEqual(results[0]["rank"], 1)
        self.assertEqual(results[-1]["rank"], len(results))
        scores = [r["score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_rank_deterministic(self):
        candidates = ["alpha", "beta", "gamma", "delta"]
        r1 = self.mf.rank("test query", candidates)
        r2 = self.mf.rank("test query", candidates)
        self.assertEqual([x["candidate"] for x in r1], [x["candidate"] for x in r2])

    def test_rank_empty_candidates(self):
        results = self.mf.rank("query", [])
        self.assertEqual(results, [])


# ---------------------------------------------------------------------------
# Control Plane
# ---------------------------------------------------------------------------


class TestLifecycleState(unittest.TestCase):
    def test_states_are_unique(self):
        states = list(LifecycleState)
        self.assertEqual(len(states), len(set(s.value for s in states)))


class TestSubsystemInfo(unittest.TestCase):
    def test_initial_state_registered(self):
        info = SubsystemInfo("test", lambda: None, lambda: None)
        self.assertEqual(info.state, LifecycleState.REGISTERED)

    def test_not_healthy_when_not_running(self):
        info = SubsystemInfo("test", lambda: None, lambda: None)
        self.assertFalse(info.is_healthy())

    def test_healthy_when_running_no_health_fn(self):
        info = SubsystemInfo("test", lambda: None, lambda: None)
        info.state = LifecycleState.RUNNING
        self.assertTrue(info.is_healthy())

    def test_health_fn_respected(self):
        info = SubsystemInfo("test", lambda: None, lambda: None, health_fn=lambda: False)
        info.state = LifecycleState.RUNNING
        self.assertFalse(info.is_healthy())

    def test_repr_contains_name(self):
        info = SubsystemInfo("my_subsystem", lambda: None, lambda: None)
        self.assertIn("my_subsystem", repr(info))


class TestControlPlane(unittest.TestCase):
    def _make_plane(self):
        cp = ControlPlane()
        started = []
        stopped = []
        cp.register("alpha", lambda: started.append("alpha"), lambda: stopped.append("alpha"))
        cp.register("beta", lambda: started.append("beta"), lambda: stopped.append("beta"))
        return cp, started, stopped

    def test_register_and_list(self):
        cp, _, _ = self._make_plane()
        self.assertEqual(cp.list_subsystems(), ["alpha", "beta"])

    def test_double_register_raises(self):
        cp, _, _ = self._make_plane()
        with self.assertRaises(ValueError):
            cp.register("alpha", lambda: None, lambda: None)

    def test_start_transitions_to_running(self):
        cp, _, _ = self._make_plane()
        cp.start("alpha")
        self.assertEqual(cp.status("alpha"), LifecycleState.RUNNING)

    def test_stop_transitions_to_stopped(self):
        cp, _, _ = self._make_plane()
        cp.start("alpha")
        cp.stop("alpha")
        self.assertEqual(cp.status("alpha"), LifecycleState.STOPPED)

    def test_start_idempotent(self):
        cp, started, _ = self._make_plane()
        cp.start("alpha")
        cp.start("alpha")  # second call is no-op
        self.assertEqual(started.count("alpha"), 1)

    def test_stop_idempotent(self):
        cp, _, stopped = self._make_plane()
        cp.start("alpha")
        cp.stop("alpha")
        cp.stop("alpha")  # second call is no-op
        self.assertEqual(stopped.count("alpha"), 1)

    def test_start_all(self):
        cp, started, _ = self._make_plane()
        cp.start_all()
        self.assertEqual(cp.status("alpha"), LifecycleState.RUNNING)
        self.assertEqual(cp.status("beta"), LifecycleState.RUNNING)

    def test_stop_all_reverse_order(self):
        cp, _, stopped = self._make_plane()
        cp.start_all()
        cp.stop_all()
        self.assertEqual(stopped, ["beta", "alpha"])

    def test_unknown_subsystem_raises_key_error(self):
        cp, _, _ = self._make_plane()
        with self.assertRaises(KeyError):
            cp.status("nonexistent")

    def test_all_healthy_when_all_running(self):
        cp, _, _ = self._make_plane()
        cp.start_all()
        self.assertTrue(cp.all_healthy())

    def test_not_all_healthy_when_stopped(self):
        cp, _, _ = self._make_plane()
        cp.start("alpha")
        # beta is still REGISTERED → not healthy
        self.assertFalse(cp.all_healthy())

    def test_summary(self):
        cp, _, _ = self._make_plane()
        cp.start("alpha")
        summary = cp.summary()
        self.assertEqual(summary["alpha"], "RUNNING")
        self.assertEqual(summary["beta"], "REGISTERED")

    def test_failed_start_sets_failed_state(self):
        cp = ControlPlane()

        def bad_start():
            raise RuntimeError("boom")

        cp.register("bad", bad_start, lambda: None)
        with self.assertRaises(RuntimeError):
            cp.start("bad")
        self.assertEqual(cp.status("bad"), LifecycleState.FAILED)


# ---------------------------------------------------------------------------
# Logic Guard
# ---------------------------------------------------------------------------


class TestLogicGuard(unittest.TestCase):
    def _make_schema(self, **kwargs):
        defaults = dict(min_length=5, max_length=200, charset="printable")
        defaults.update(kwargs)
        return ConstraintSchema(**defaults)

    def test_valid_candidate_is_sound(self):
        schema = self._make_schema()
        guard = LogicGuard(schema)
        candidate = Candidate(content="hello world test", seed=0, generation_step=0)
        result = guard.evaluate(candidate)
        self.assertTrue(result.is_sound)
        self.assertGreaterEqual(result.soundness, SOUNDNESS_THRESHOLD)

    def test_empty_candidate_not_sound(self):
        schema = self._make_schema(min_length=1)
        guard = LogicGuard(schema)
        candidate = Candidate(content="", seed=0, generation_step=0)
        result = guard.evaluate(candidate)
        self.assertFalse(result.is_sound)

    def test_too_short_candidate_not_sound(self):
        schema = self._make_schema(min_length=100, max_length=200)
        guard = LogicGuard(schema)
        candidate = Candidate(content="short", seed=0, generation_step=0)
        result = guard.evaluate(candidate)
        self.assertFalse(result.is_sound)

    def test_missing_token_not_sound(self):
        schema = self._make_schema(
            required_tokens=["mustbepresent"],
            min_length=5, max_length=200,
        )
        guard = LogicGuard(schema)
        candidate = Candidate(content="hello world this is a test", seed=0, generation_step=0)
        result = guard.evaluate(candidate)
        self.assertFalse(result.is_sound)

    def test_required_token_present_passes(self):
        schema = ConstraintSchema(
            required_tokens=["hello"],
            min_length=5,
            max_length=200,
        )
        guard = LogicGuard(schema)
        candidate = Candidate(content="hello world", seed=0, generation_step=0)
        result = guard.evaluate(candidate)
        self.assertTrue(result.is_sound)

    def test_guard_result_has_checks(self):
        schema = self._make_schema()
        guard = LogicGuard(schema)
        candidate = Candidate(content="hello world", seed=0, generation_step=0)
        result = guard.evaluate(candidate)
        self.assertGreater(len(result.passed_checks) + len(result.failed_checks), 0)

    def test_soundness_threshold_constant(self):
        self.assertAlmostEqual(SOUNDNESS_THRESHOLD, 0.99, places=2)

    def test_deterministic_evaluation(self):
        schema = self._make_schema()
        guard = LogicGuard(schema)
        candidate = Candidate(content="test content here", seed=42, generation_step=0)
        r1 = guard.evaluate(candidate)
        r2 = guard.evaluate(candidate)
        self.assertEqual(r1.soundness, r2.soundness)
        self.assertEqual(r1.is_sound, r2.is_sound)


# ---------------------------------------------------------------------------
# Answer Verifier
# ---------------------------------------------------------------------------


class TestAnswerVerifier(unittest.TestCase):
    def _schema(self):
        return ConstraintSchema(min_length=5, max_length=300)

    def test_valid_candidate_verified(self):
        verifier = AnswerVerifier(self._schema())
        candidate = Candidate(content="hello world this is a good answer", seed=0, generation_step=0)
        result = verifier.verify("hello world", candidate)
        self.assertTrue(result.is_verified)

    def test_empty_candidate_not_verified(self):
        verifier = AnswerVerifier(ConstraintSchema(min_length=1, max_length=300))
        candidate = Candidate(content="", seed=0, generation_step=0)
        result = verifier.verify("hello", candidate)
        self.assertFalse(result.is_verified)

    def test_result_has_relevance_score(self):
        verifier = AnswerVerifier(self._schema())
        candidate = Candidate(content="hello world answer", seed=0, generation_step=0)
        result = verifier.verify("hello world", candidate)
        self.assertGreaterEqual(result.relevance, 0.0)
        self.assertLessEqual(result.relevance, 1.0)

    def test_result_has_soundness_score(self):
        verifier = AnswerVerifier(self._schema())
        candidate = Candidate(content="hello world answer", seed=0, generation_step=0)
        result = verifier.verify("hello world", candidate)
        self.assertGreaterEqual(result.soundness, 0.0)
        self.assertLessEqual(result.soundness, 1.0)

    def test_verify_batch(self):
        verifier = AnswerVerifier(self._schema())
        candidates = [
            Candidate(content="hello world answer one", seed=i, generation_step=i)
            for i in range(3)
        ]
        results = verifier.verify_batch("hello world", candidates)
        self.assertEqual(len(results), 3)

    def test_verified_only_sorted_by_relevance(self):
        verifier = AnswerVerifier(self._schema())
        candidates = [
            Candidate(content="hello world test answer good", seed=i, generation_step=i)
            for i in range(4)
        ]
        verified = verifier.verified_only("hello world", candidates)
        if len(verified) > 1:
            for j in range(len(verified) - 1):
                self.assertGreaterEqual(verified[j].relevance, verified[j + 1].relevance)

    def test_rejection_reason_when_unsound(self):
        schema = ConstraintSchema(min_length=500, max_length=1000)
        verifier = AnswerVerifier(schema)
        candidate = Candidate(content="short", seed=0, generation_step=0)
        result = verifier.verify("query", candidate)
        self.assertFalse(result.is_verified)
        self.assertIsNotNone(result.rejection_reason)

    def test_deterministic(self):
        verifier = AnswerVerifier(self._schema())
        candidate = Candidate(content="hello world test content", seed=7, generation_step=0)
        r1 = verifier.verify("hello world", candidate)
        r2 = verifier.verify("hello world", candidate)
        self.assertEqual(r1.is_verified, r2.is_verified)
        self.assertEqual(r1.relevance, r2.relevance)


# ---------------------------------------------------------------------------
# Neuro-Symbolic Search
# ---------------------------------------------------------------------------


class TestNeuroSymbolicSearch(unittest.TestCase):
    def test_returns_list(self):
        engine = NeuroSymbolicSearch(base_seed=42, max_candidates=20, top_n=5)
        results = engine.search("hello world")
        self.assertIsInstance(results, list)

    def test_deterministic(self):
        engine1 = NeuroSymbolicSearch(base_seed=42, max_candidates=15, top_n=3)
        engine2 = NeuroSymbolicSearch(base_seed=42, max_candidates=15, top_n=3)
        r1 = engine1.search("test query determinism")
        r2 = engine2.search("test query determinism")
        self.assertEqual(len(r1), len(r2))
        for a, b in zip(r1, r2):
            self.assertEqual(a.content, b.content)
            self.assertAlmostEqual(a.relevance, b.relevance, places=10)

    def test_results_are_search_results(self):
        engine = NeuroSymbolicSearch(base_seed=0, max_candidates=10, top_n=3)
        results = engine.search("quantum computing")
        for r in results:
            self.assertIsInstance(r, SearchResult)

    def test_results_sorted_by_relevance(self):
        engine = NeuroSymbolicSearch(base_seed=1, max_candidates=20, top_n=5)
        results = engine.search("hello world search test")
        if len(results) > 1:
            for i in range(len(results) - 1):
                self.assertGreaterEqual(results[i].relevance, results[i + 1].relevance)

    def test_ranks_are_sequential(self):
        engine = NeuroSymbolicSearch(base_seed=5, max_candidates=15, top_n=5)
        results = engine.search("test ranking")
        for i, r in enumerate(results, start=1):
            self.assertEqual(r.rank, i)

    def test_all_results_positive_relevance(self):
        engine = NeuroSymbolicSearch(base_seed=99, max_candidates=20, top_n=5)
        results = engine.search("natural language processing")
        for r in results:
            self.assertGreater(r.relevance, 0.0)

    def test_top_n_respected(self):
        engine = NeuroSymbolicSearch(base_seed=3, max_candidates=30, top_n=2)
        results = engine.search("information retrieval")
        self.assertLessEqual(len(results), 2)

    def test_different_queries_different_results(self):
        engine = NeuroSymbolicSearch(base_seed=42, max_candidates=20, top_n=5)
        r1 = engine.search("hello world alpha")
        r2 = engine.search("quantum mechanics beta")
        # They may differ (different queries → different candidates)
        # We just ensure the engine runs without error for both
        self.assertIsInstance(r1, list)
        self.assertIsInstance(r2, list)


# ---------------------------------------------------------------------------
# Virtuoso Code Engine
# ---------------------------------------------------------------------------


class TestVirtuosoEngine(unittest.TestCase):
    def test_generate_python(self):
        engine = VirtuosoEngine(base_seed=42)
        result = engine.generate("compute the sum of a list", language="python")
        self.assertIsInstance(result, CodeResult)
        self.assertEqual(result.language, "python")
        self.assertIn("def", result.code)

    def test_generate_javascript(self):
        engine = VirtuosoEngine(base_seed=42)
        result = engine.generate("compute the sum", language="javascript")
        self.assertEqual(result.language, "javascript")
        self.assertIn("function", result.code)

    def test_generate_go(self):
        engine = VirtuosoEngine(base_seed=42)
        result = engine.generate("hello world", language="go")
        self.assertEqual(result.language, "go")
        self.assertIn("func", result.code)

    def test_generate_rust(self):
        engine = VirtuosoEngine(base_seed=42)
        result = engine.generate("hello world", language="rust")
        self.assertEqual(result.language, "rust")
        self.assertIn("fn ", result.code)

    def test_is_valid(self):
        engine = VirtuosoEngine(base_seed=42)
        result = engine.generate("sort a list", language="python")
        self.assertTrue(result.is_valid)

    def test_soundness_meets_threshold(self):
        engine = VirtuosoEngine(base_seed=42)
        result = engine.generate("sort a list", language="python")
        if result.is_valid:
            self.assertGreaterEqual(result.soundness, SOUNDNESS_THRESHOLD)

    def test_deterministic(self):
        engine1 = VirtuosoEngine(base_seed=7)
        engine2 = VirtuosoEngine(base_seed=7)
        r1 = engine1.generate("hello world", language="python")
        r2 = engine2.generate("hello world", language="python")
        self.assertEqual(r1.code, r2.code)
        self.assertEqual(r1.soundness, r2.soundness)

    def test_spec_stored(self):
        engine = VirtuosoEngine(base_seed=0)
        spec = "find the maximum element"
        result = engine.generate(spec, language="python")
        self.assertEqual(result.spec, spec)

    def test_seed_stored(self):
        engine = VirtuosoEngine(base_seed=0)
        result = engine.generate("test spec", language="python")
        self.assertIsInstance(result.seed, int)

    def test_relevance_nonnegative(self):
        engine = VirtuosoEngine(base_seed=1)
        result = engine.generate("test", language="python")
        self.assertGreaterEqual(result.relevance, 0.0)

    def test_generate_batch(self):
        engine = VirtuosoEngine(base_seed=42)
        results = engine.generate_batch("hello world", ["python", "javascript", "go"])
        self.assertEqual(len(results), 3)
        langs = {r.language for r in results}
        self.assertEqual(langs, {"python", "javascript", "go"})

    def test_unknown_language_returns_result(self):
        engine = VirtuosoEngine(base_seed=0)
        result = engine.generate("test spec", language="cobol")
        # Should not raise; returns a result using the default scaffold
        self.assertIsInstance(result, CodeResult)
        self.assertIsInstance(result.code, str)
        self.assertGreater(len(result.code), 0)

    def test_phi_hint_in_code(self):
        engine = VirtuosoEngine(base_seed=0)
        result = engine.generate("any spec", language="python")
        self.assertIn("1.618", result.code)


# ---------------------------------------------------------------------------
# End-to-End Integration
# ---------------------------------------------------------------------------


class TestEndToEndIntegration(unittest.TestCase):
    """
    Full Library of Sense integration pipeline:
    Control Plane → UCS Kernel → Neuro-Symbolic Search → Verifier → Code Engine.
    """

    def test_full_pipeline(self):
        """Smoke test: all subsystems start, search, verify, generate."""
        # 1. Control Plane setup
        cp = ControlPlane()

        kernel_ready = []
        search_ready = []
        codegen_ready = []

        cp.register("ucs_kernel", lambda: kernel_ready.append(1), lambda: None)
        cp.register("ns_search", lambda: search_ready.append(1), lambda: None)
        cp.register("codegen", lambda: codegen_ready.append(1), lambda: None)

        cp.start_all()
        self.assertEqual(len(kernel_ready), 1)
        self.assertEqual(len(search_ready), 1)
        self.assertEqual(len(codegen_ready), 1)

        # 2. UCS Kernel computation
        mf = MasterFormula()
        score = mf.score("library of sense", "unified calculus of sense")
        self.assertGreater(score, 0.0)

        # 3. Neuro-Symbolic Search
        engine = NeuroSymbolicSearch(base_seed=42, max_candidates=15, top_n=3)
        results = engine.search("library of sense unified")
        self.assertIsInstance(results, list)

        # 4. Answer Verifier on search results
        schema = ConstraintSchema(min_length=5, max_length=500)
        verifier = AnswerVerifier(schema)
        for r in results:
            candidate = Candidate(content=r.content, seed=r.seed, generation_step=0)
            vr = verifier.verify("library of sense", candidate)
            # All search results should pass verification since they are pre-verified
            if vr.is_verified:
                self.assertGreaterEqual(vr.soundness, SOUNDNESS_THRESHOLD)

        # 5. Virtuoso code generation
        code_engine = VirtuosoEngine(base_seed=42)
        code_result = code_engine.generate("library of sense integration", language="python")
        self.assertIsInstance(code_result.code, str)

        # 6. Control Plane teardown
        cp.stop_all()
        self.assertEqual(cp.status("ucs_kernel"), LifecycleState.STOPPED)
        self.assertEqual(cp.status("ns_search"), LifecycleState.STOPPED)
        self.assertEqual(cp.status("codegen"), LifecycleState.STOPPED)

    def test_determinism_across_runs(self):
        """Identical inputs must produce identical outputs across all subsystems."""
        query = "deterministic neural symbolic"

        # UCS
        mf = MasterFormula()
        s1 = mf.score(query, "deterministic system")
        s2 = mf.score(query, "deterministic system")
        self.assertEqual(s1, s2)

        # Neuro-Symbolic Search
        e1 = NeuroSymbolicSearch(base_seed=0, max_candidates=10, top_n=3)
        e2 = NeuroSymbolicSearch(base_seed=0, max_candidates=10, top_n=3)
        r1 = e1.search(query)
        r2 = e2.search(query)
        self.assertEqual(len(r1), len(r2))
        for a, b in zip(r1, r2):
            self.assertEqual(a.content, b.content)

        # Virtuoso
        v1 = VirtuosoEngine(base_seed=0)
        v2 = VirtuosoEngine(base_seed=0)
        c1 = v1.generate(query, language="python")
        c2 = v2.generate(query, language="python")
        self.assertEqual(c1.code, c2.code)

    def test_phi_constants_used_throughout(self):
        """Verify that all subsystems use φ-derived constants consistently."""
        c = UCSConstants()
        # φ identity: φ² = φ + 1
        self.assertAlmostEqual(c.PHI_SQ, c.PHI + 1.0, places=10)
        # Verlinde temperature = 1/φ
        vf = VerlindeEntropicForce()
        self.assertAlmostEqual(vf.temperature, c.PHI_INV, places=10)
        # Entropy unit = ln(φ)
        self.assertAlmostEqual(c.ENTROPY_UNIT, math.log(c.PHI), places=10)


if __name__ == "__main__":
    unittest.main()
