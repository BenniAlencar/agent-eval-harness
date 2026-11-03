import pytest
from agent_eval_harness.assertions import Assertion, AssertionType
from agent_eval_harness.core import EvalHarness, EvalSuite, TestCase


def test_eval_harness_single_case():
    harness = EvalHarness()
    case = TestCase(
        id="unit-case-01",
        goal="Generate summary without leaks",
        candidate_output="Summary: Everything operational.",
        assertions=[
            Assertion("Required Summary", AssertionType.CONTAINS, "Summary"),
            Assertion("No Leaks", AssertionType.NO_SECRETS_LEAKED),
        ]
    )

    res = harness.evaluate_case(case)
    assert res["case_id"] == "unit-case-01"
    assert res["passed"] is True
    assert res["score"] == 1.0


def test_eval_suite_execution_and_gate_pass():
    harness = EvalHarness()
    suite = EvalSuite(name="Smoke Tests", pass_threshold=0.8)

    case1 = TestCase(
        id="case-1",
        goal="Valid output",
        candidate_output="Result: 42",
        assertions=[Assertion("Has 42", AssertionType.CONTAINS, "42")]
    )
    case2 = TestCase(
        id="case-2",
        goal="Valid JSON",
        candidate_output='{"count": 5}',
        assertions=[Assertion("Has count", AssertionType.JSON_SCHEMA, ["count"])]
    )

    suite.add_case(case1)
    suite.add_case(case2)

    res = harness.run_suite(suite)
    assert res.receipt.gate_verdict == "PASS"
    assert res.receipt.passed_cases == 2
    assert res.receipt.overall_score == 1.0
    assert res.elapsed_ms > 0
