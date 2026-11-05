import pytest
from agent_eval_harness.receipts import EvaluationReceipt, compute_sha256
from agent_eval_harness.core import EvalHarness, EvalSuite, TestCase
from agent_eval_harness.assertions import Assertion, AssertionType


def test_evaluation_receipt_hashing_and_markdown():
    receipt = EvaluationReceipt(
        suite_name="Production Gate V1",
        total_cases=10,
        passed_cases=10,
        overall_score=1.0,
        gate_verdict="PASS",
        task_version="v1.2.0",
        policy_version="2026.11-strict",
        input_digest="a" * 64,
        ruleset_digest="b" * 64,
        case_results=[
            {"case_id": "c-01", "passed": True, "score": 1.0, "summary": "All assertions met"},
            {"case_id": "c-02", "passed": True, "score": 1.0, "summary": "Zero secrets leaked"},
        ]
    )

    assert len(receipt.merkle_root_hash) == 64
    md = receipt.to_markdown()
    assert "Production Gate V1" in md
    assert "PASSED" in md
    assert "v1.2.0" in md
    assert "2026.11-strict" in md
    assert receipt.merkle_root_hash in md

    d = receipt.to_dict()
    assert d["gate_verdict"] == "PASS"
    assert d["task_version"] == "v1.2.0"
    assert d["input_digest"] == "a" * 64
    assert d["merkle_root_hash"] == receipt.merkle_root_hash


def test_receipt_reproducibility_verification():
    raw_inputs = {"prompt": "Analyze sales revenue", "user_id": "usr_99"}
    raw_ruleset = [{"rule": "no_pii", "weight": 1.0}, {"rule": "valid_json", "weight": 0.8}]

    input_hash = compute_sha256(raw_inputs)
    ruleset_hash = compute_sha256(raw_ruleset)

    receipt = EvaluationReceipt(
        suite_name="Financial Agent Gate",
        total_cases=1,
        passed_cases=1,
        overall_score=1.0,
        gate_verdict="PASS",
        task_version="v2.0.0",
        policy_version="pci-dss-v4",
        input_digest=input_hash,
        ruleset_digest=ruleset_hash,
        case_results=[{"case_id": "fin-01", "passed": True, "score": 1.0, "summary": "PASS"}]
    )

    # 1. Nominal verification: verifier reproduces claim
    valid, msg = receipt.verify_reproducibility(
        raw_inputs=raw_inputs,
        raw_ruleset=raw_ruleset,
        expected_task_version="v2.0.0",
        expected_policy_version="pci-dss-v4"
    )
    assert valid is True
    assert "successfully verified" in msg

    # 2. Tampered input detection: auditor passes different inputs
    tampered_inputs = {"prompt": "Analyze sales revenue (TAMPERED)", "user_id": "usr_99"}
    valid_tampered, err = receipt.verify_reproducibility(raw_inputs=tampered_inputs)
    assert valid_tampered is False
    assert "Input digest mismatch" in err

    # 3. Tampered ruleset detection: auditor evaluates against weaker rules
    tampered_ruleset = [{"rule": "no_pii", "weight": 0.1}]
    valid_rules, err_rules = receipt.verify_reproducibility(raw_ruleset=tampered_ruleset)
    assert valid_rules is False
    assert "Ruleset digest mismatch" in err_rules

    # 4. Tampered task version detection
    valid_ver, err_ver = receipt.verify_reproducibility(expected_task_version="v1.0.0")
    assert valid_ver is False
    assert "Task version mismatch" in err_ver


def test_suite_generates_canonical_receipt():
    suite = EvalSuite(name="Autonomous Pipeline", task_version="v3.1.0", policy_version="sovereign-tier1")
    case = TestCase(
        id="t-01",
        goal="Generate Python code",
        candidate_output="def add(a, b): return a + b",
        assertions=[Assertion("HasDef", AssertionType.CONTAINS, expected_value="def")]
    )
    suite.add_case(case)

    harness = EvalHarness()
    result = harness.run_suite(suite)

    receipt = result.receipt
    assert receipt.gate_verdict == "PASS"
    assert receipt.task_version == "v3.1.0"
    assert receipt.policy_version == "sovereign-tier1"
    assert len(receipt.input_digest) == 64
    assert len(receipt.ruleset_digest) == 64

    # Assert verifier can reproduce
    valid, msg = receipt.verify_reproducibility()
    assert valid is True
