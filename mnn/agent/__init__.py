"""
MNN Automation Agent

Discovers, validates, and reports on the health of the MNN repository.
All validation steps run in a deterministic, explicit order with fail-fast
semantics and full state capture.

Usage (CLI):
    python -m mnn.agent            # run all checks
    python -m mnn.agent --checks lint,test,cpp
    python -m mnn.agent --help

Usage (API):
    from mnn.agent import Agent
    result = Agent().run()
    print(result.summary())
"""

from mnn.agent.core import Agent, AgentResult, CheckStatus

__all__ = ["Agent", "AgentResult", "CheckStatus"]
