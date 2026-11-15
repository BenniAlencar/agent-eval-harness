"""System Health & Cryptographic Evaluator Monitor for agent-eval-harness.

Monitors RFC 8785 JCS receipt reproducibility, red-team secret leak scanner
readiness, and assertion evaluator self-test health.
"""

from __future__ import annotations

import time
from typing import Any

from ..core.assertions import Assertion, AssertionType
from ..core.harness import EvalHarness, EvalSuite, TestCase
from ..core.metrics import EvaluatorMetrics


class EvalHealthMonitor:
    """Monitors deterministic evaluator, red-team scanner, and JCS receipt health."""

    def __init__(self, max_eval_latency_ms: float = 50.0) -> None:
        self.max_eval_latency_ms = max_eval_latency_ms

    @staticmethod
    def check_red_team_scanner() -> dict[str, Any]:
        """Verify red-team secret leak scanner detects synthetic secrets."""
        has_leak, leaks = EvaluatorMetrics.check_red_team_leak(
            "token=sk-1234567890abcdef1234567890abcdef"
        )
        clean_leak, _ = EvaluatorMetrics.check_red_team_leak("All checks passed cleanly.")
        return {
            "passed": has_leak and not clean_leak,
            "sample_leaks_detected": len(leaks),
        }

    @staticmethod
    def check_receipt_self_test() -> dict[str, Any]:
        """Run a fast in-memory evaluation + RFC 8785 receipt verification."""
        t0 = time.perf_counter()
        harness = EvalHarness()
        suite = EvalSuite(name="health-selftest", pass_threshold=1.0)
        suite.add_case(
            TestCase(
                id="selftest-001",
                goal="Verify deterministic assertion + JCS receipt",
                candidate_output='{"status": "OK", "count": 1}',
                assertions=[
                    Assertion("JSON", AssertionType.JSON_SCHEMA, ["status", "count"]),
                    Assertion("No Leaks", AssertionType.NO_SECRETS_LEAKED),
                ],
            )
        )
        result = harness.run_suite(suite)
        valid, msg = result.receipt.verify_reproducibility()
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        return {
            "passed": result.receipt.gate_verdict == "PASS" and valid,
            "message": msg,
            "elapsed_ms": elapsed_ms,
        }

    def check_health(self) -> dict[str, Any]:
        """Generate structured health assessment for agent-eval-harness."""
        scanner = self.check_red_team_scanner()
        receipt = self.check_receipt_self_test()

        status = "healthy"
        warnings: list[str] = []

        if not scanner["passed"]:
            status = "critical"
            warnings.append("Red-team secret leak scanner self-test failed.")
        if not receipt["passed"]:
            status = "critical"
            warnings.append("RFC 8785 evaluation receipt self-test failed.")
        elif receipt["elapsed_ms"] > self.max_eval_latency_ms:
            status = "degraded"
            warnings.append(
                f"Evaluation latency {receipt['elapsed_ms']}ms exceeded {self.max_eval_latency_ms}ms."
            )

        return {
            "status": status,
            "warnings": warnings,
            "red_team_scanner": scanner,
            "receipt_self_test": receipt,
            "timestamp": time.time(),
        }
