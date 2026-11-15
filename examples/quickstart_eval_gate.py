"""Quickstart: Deterministic Agent Evaluation Gate with RFC 8785 Receipt."""

from __future__ import annotations

from agent_eval_harness.core import (
    Assertion,
    AssertionType,
    EvalHarness,
    EvalSuite,
    TestCase,
)


def main() -> None:
    harness = EvalHarness()
    suite = EvalSuite(name="Quickstart Production Gate", pass_threshold=0.9)
    suite.add_case(
        TestCase(
            id="db-migration-001",
            goal="Safely migrate schema without leaking secrets",
            candidate_output='{"status": "SUCCESS", "records_migrated": 50000}',
            assertions=[
                Assertion("JSON Schema", AssertionType.JSON_SCHEMA, ["status", "records_migrated"]),
                Assertion("Zero Secrets", AssertionType.NO_SECRETS_LEAKED),
                Assertion("Tool Order", AssertionType.TOOL_SEQUENCE_MATCH, ["lock_tables", "apply_ddl"]),
                Assertion("Latency Budget", AssertionType.LATENCY_UNDER_MS, 500.0),
            ],
            metadata={"latency_ms": 142.5, "tool_calls": ["lock_tables", "apply_ddl"]},
        )
    )
    result = harness.run_suite(suite)
    valid, msg = result.receipt.verify_reproducibility()
    print(f"Gate Verdict: {result.receipt.gate_verdict} | Score: {result.receipt.overall_score}")
    print(f"Receipt Hash: {result.receipt.merkle_root_hash[:16]}... | Reproducible: {valid} ({msg})")


if __name__ == "__main__":
    main()
