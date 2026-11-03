import pytest
from agent_eval_harness.metrics import EvaluatorMetrics


def test_mcp_eval_logic_direct():
    valid, _, _ = EvaluatorMetrics.validate_json_structure('{"status": "ok"}', ["status"])
    assert valid is True

    has_leak, _ = EvaluatorMetrics.check_red_team_leak("safe string")
    assert has_leak is False
