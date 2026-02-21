"""Tests for the MNN automation agent (mnn.agent)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


class TestCheckStatus(unittest.TestCase):
    def test_values(self) -> None:
        from mnn.agent.core import CheckStatus
        self.assertEqual(CheckStatus.PASS.value, "pass")
        self.assertEqual(CheckStatus.FAIL.value, "fail")
        self.assertEqual(CheckStatus.SKIP.value, "skip")


class TestAgentResult(unittest.TestCase):
    def setUp(self) -> None:
        from mnn.agent.core import AgentResult, CheckResult, CheckStatus
        self.AgentResult = AgentResult
        self.CheckResult = CheckResult
        self.CheckStatus = CheckStatus

    def test_passed_all_pass(self) -> None:
        result = self.AgentResult(
            checks=[
                self.CheckResult("a", self.CheckStatus.PASS),
                self.CheckResult("b", self.CheckStatus.SKIP),
            ]
        )
        self.assertTrue(result.passed())

    def test_passed_with_fail(self) -> None:
        result = self.AgentResult(
            checks=[
                self.CheckResult("a", self.CheckStatus.PASS),
                self.CheckResult("b", self.CheckStatus.FAIL, "some error"),
            ]
        )
        self.assertFalse(result.passed())

    def test_summary_contains_check_names(self) -> None:
        result = self.AgentResult(
            checks=[self.CheckResult("discovery", self.CheckStatus.PASS, "Found 5 files.")],
            started_at="2026-01-01T00:00:00+00:00",
            repo_root="/repo",
        )
        summary = result.summary()
        self.assertIn("discovery", summary)
        self.assertIn("PASS", summary)
        self.assertIn("Overall: PASS", summary)

    def test_to_dict_structure(self) -> None:
        result = self.AgentResult(
            checks=[self.CheckResult("deps", self.CheckStatus.PASS, "ok")],
            started_at="2026-01-01T00:00:00+00:00",
            finished_at="2026-01-01T00:00:01+00:00",
            repo_root="/repo",
        )
        d = result.to_dict()
        self.assertIn("checks", d)
        self.assertIn("passed", d)
        self.assertEqual(d["checks"][0]["name"], "deps")
        self.assertEqual(d["checks"][0]["status"], "pass")


class TestAgentChecks(unittest.TestCase):
    """Run individual agent checks against the real repository."""

    @classmethod
    def setUpClass(cls) -> None:
        from mnn.agent.core import Agent
        # Point agent at real repo root (two levels up from this file)
        repo_root = Path(__file__).resolve().parents[1]
        # Use a temp dir for the log file to avoid polluting the repo
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.agent = Agent(
            repo_root=repo_root,
            log_file=Path(cls._tmpdir.name) / "agent_run.log",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmpdir.cleanup()

    def test_check_discovery_passes(self) -> None:
        from mnn.agent.core import CheckStatus
        result = self.agent._check_discovery()
        self.assertEqual(result.status, CheckStatus.PASS, result.detail)

    def test_check_deps_passes(self) -> None:
        from mnn.agent.core import CheckStatus
        result = self.agent._check_deps()
        self.assertEqual(result.status, CheckStatus.PASS, result.detail)

    def test_check_envvars_passes(self) -> None:
        from mnn.agent.core import CheckStatus
        result = self.agent._check_envvars()
        # envvars check should pass regardless of unset optional vars
        self.assertEqual(result.status, CheckStatus.PASS, result.detail)

    def test_check_lint_passes(self) -> None:
        from mnn.agent.core import CheckStatus
        result = self.agent._check_lint()
        self.assertEqual(result.status, CheckStatus.PASS, result.detail)

    def test_check_imports_passes(self) -> None:
        from mnn.agent.core import CheckStatus
        result = self.agent._check_imports()
        self.assertEqual(result.status, CheckStatus.PASS, result.detail)

    def test_full_run_no_test_check(self) -> None:
        """Run all checks except 'test' (which re-runs the entire suite) to keep this fast."""
        from mnn.agent.core import Agent, CheckStatus
        repo_root = Path(__file__).resolve().parents[1]
        fast_checks = [c for c in Agent.CHECK_ORDER if c != "test"]
        agent = Agent(
            repo_root=repo_root,
            checks=fast_checks,
            log_file=Path(self._tmpdir.name) / "agent_run_fast.log",
        )
        result = agent.run()
        self.assertTrue(result.passed(), result.summary())

    def test_log_file_written(self) -> None:
        """Verify the run persists a valid JSON log file."""
        from mnn.agent.core import Agent
        repo_root = Path(__file__).resolve().parents[1]
        log_path = Path(self._tmpdir.name) / "test_log.json"
        agent = Agent(
            repo_root=repo_root,
            checks=["discovery"],
            log_file=log_path,
        )
        agent.run()
        self.assertTrue(log_path.exists())
        data = json.loads(log_path.read_text())
        self.assertIn("checks", data)
        self.assertIn("passed", data)

    def test_fail_fast_stops_early(self) -> None:
        """Verify fail_fast stops after the first failure."""
        from mnn.agent.core import Agent, CheckResult, CheckStatus

        class _FailFirstAgent(Agent):
            def _check_discovery(self) -> CheckResult:
                return CheckResult(name="discovery", status=CheckStatus.FAIL, detail="forced failure")

        repo_root = Path(__file__).resolve().parents[1]
        agent = _FailFirstAgent(
            repo_root=repo_root,
            fail_fast=True,
            log_file=Path(self._tmpdir.name) / "ff_log.json",
        )
        result = agent.run()
        # Should have discovery=FAIL, rest=SKIP
        statuses = {c.name: c.status for c in result.checks}
        self.assertEqual(statuses["discovery"], CheckStatus.FAIL)
        # All checks after discovery should be SKIP
        after = False
        for c in result.checks:
            if c.name == "discovery":
                after = True
                continue
            if after:
                self.assertEqual(c.status, CheckStatus.SKIP, f"{c.name} should be skipped")


class TestCLI(unittest.TestCase):
    def test_help_exits_zero(self) -> None:
        from mnn.agent.__main__ import main
        with self.assertRaises(SystemExit) as ctx:
            main(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_unknown_check_exits_nonzero(self) -> None:
        from mnn.agent.__main__ import main
        with self.assertRaises(SystemExit) as ctx:
            main(["--checks", "nonexistent_check"])
        self.assertNotEqual(ctx.exception.code, 0)

    def test_run_discovery_only(self) -> None:
        from mnn.agent.__main__ import main
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = main(["--checks", "discovery"])
        output = buf.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("discovery", output)
        self.assertIn("PASS", output)


if __name__ == "__main__":
    unittest.main()
