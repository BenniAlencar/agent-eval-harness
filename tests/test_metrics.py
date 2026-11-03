import pytest
from agent_eval_harness.metrics import EvaluatorMetrics


def test_jaccard_and_levenshtein_similarity():
    s1 = "Autonomous AI Agent Swarm Architecture"
    s2 = "Autonomous AI Agent Swarm Coordination"
    jaccard = EvaluatorMetrics.jaccard_similarity(s1, s2)
    assert jaccard > 0.6

    lev = EvaluatorMetrics.levenshtein_ratio("hello", "hello")
    assert lev == 1.0
    lev_diff = EvaluatorMetrics.levenshtein_ratio("kitten", "sitting")
    assert 0.5 < lev_diff < 0.8


def test_keyword_density():
    text = "The system achieved 99.9% uptime with zero packet drops under stress."
    ratio, missing = EvaluatorMetrics.keyword_density(text, ["uptime", "zero packet drops", "stress"])
    assert ratio == 1.0
    assert len(missing) == 0

    ratio2, missing2 = EvaluatorMetrics.keyword_density(text, ["uptime", "quantum decoherence"])
    assert ratio2 == 0.5
    assert missing2 == ["quantum decoherence"]


def test_validate_json_structure():
    raw_json = '{"status": "ok", "latency_ms": 12.4}'
    valid, parsed, _ = EvaluatorMetrics.validate_json_structure(raw_json, required_keys=["status", "latency_ms"])
    assert valid is True
    assert parsed["status"] == "ok"

    # Test markdown wrapped json
    wrapped = '```json\n{"status": "ok"}\n```'
    valid2, parsed2, _ = EvaluatorMetrics.validate_json_structure(wrapped, required_keys=["status"])
    assert valid2 is True
    assert parsed2["status"] == "ok"


def test_red_team_leak_detection():
    safe_text = "The model summarized the financial statement correctly."
    has_leak, _ = EvaluatorMetrics.check_red_team_leak(safe_text)
    assert has_leak is False

    leaked_key = "Here is your key: sk-abcdef1234567890abcdef123456"
    has_leak2, patterns2 = EvaluatorMetrics.check_red_team_leak(leaked_key)
    assert has_leak2 is True
    assert len(patterns2) > 0

    leaked_ssrf = "curl http://169.254.169.254/latest/meta-data/"
    has_leak3, patterns3 = EvaluatorMetrics.check_red_team_leak(leaked_ssrf)
    assert has_leak3 is True


def test_tool_sequence_matching():
    actual = ["search_web", "extract_content", "save_report", "cleanup"]
    expected = ["search_web", "save_report"]
    passed, score = EvaluatorMetrics.evaluate_tool_sequence(actual, expected)
    assert passed is True
    assert score == 1.0

    unmatched_expected = ["search_web", "delete_database"]
    passed2, score2 = EvaluatorMetrics.evaluate_tool_sequence(actual, unmatched_expected)
    assert passed2 is False
    assert score2 == 0.5
