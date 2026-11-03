import pytest
from agent_eval_harness.receipts import EvaluationReceipt


def test_evaluation_receipt_hashing_and_markdown():
    receipt = EvaluationReceipt(
        suite_name="Production Gate V1",
        total_cases=10,
        passed_cases=10,
        overall_score=1.0,
        gate_verdict="PASS",
        case_results=[
            {"case_id": "c-01", "passed": True, "score": 1.0, "summary": "All assertions met"},
            {"case_id": "c-02", "passed": True, "score": 1.0, "summary": "Zero secrets leaked"},
        ]
    )

    assert len(receipt.merkle_root_hash) == 64
    md = receipt.to_markdown()
    assert "Production Gate V1" in md
    assert "PASSED" in md
    assert receipt.merkle_root_hash in md

    d = receipt.to_dict()
    assert d["gate_verdict"] == "PASS"
    assert d["merkle_root_hash"] == receipt.merkle_root_hash
