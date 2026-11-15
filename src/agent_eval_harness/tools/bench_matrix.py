"""Matrix Benchmark Suite for agent-eval-harness.

Executes automated sweeps across suite sizes (e.g. 10, 50, 100, 500 test cases)
to measure deterministic assertion throughput, RFC 8785 receipt generation time,
and per-case latency.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from typing import Any

from ..core.assertions import Assertion, AssertionType
from ..core.harness import EvalHarness, EvalSuite, TestCase


class EvalBenchMatrixRunner:
    """Executes a multi-scale evaluation throughput benchmark matrix."""

    def __init__(self, case_counts: list[int] | None = None, reps: int = 2) -> None:
        self.case_counts = case_counts or [10, 50, 100, 500]
        self.reps = reps

    @staticmethod
    def _build_suite(num_cases: int) -> EvalSuite:
        suite = EvalSuite(name=f"bench-matrix-{num_cases}", pass_threshold=0.95)
        sample = '{"status": "COMPLETED", "records_processed": 1420, "latency_ms": 12.4}'
        for i in range(num_cases):
            suite.add_case(
                TestCase(
                    id=f"case-{i:04d}",
                    goal="Verify deterministic JSON, secret safety, tool order, and latency",
                    candidate_output=sample,
                    assertions=[
                        Assertion("Valid JSON", AssertionType.JSON_SCHEMA, ["status", "records_processed"]),
                        Assertion("No Secrets", AssertionType.NO_SECRETS_LEAKED),
                        Assertion("Tools", AssertionType.TOOL_SEQUENCE_MATCH, ["fetch", "process"]),
                        Assertion("Latency", AssertionType.LATENCY_UNDER_MS, 50.0),
                    ],
                    metadata={"latency_ms": 12.4, "tool_calls": ["fetch", "process"]},
                )
            )
        return suite

    def run_matrix(self) -> dict[str, Any]:
        """Run the benchmark sweep across configured case counts."""
        rows: list[dict[str, Any]] = []
        harness = EvalHarness()

        for count in self.case_counts:
            suite = self._build_suite(count)
            latencies_ms: list[float] = []

            for _ in range(self.reps):
                t0 = time.perf_counter()
                res = harness.run_suite(suite)
                latencies_ms.append((time.perf_counter() - t0) * 1000.0)
                assert res.receipt.gate_verdict == "PASS"

            avg_ms = statistics.mean(latencies_ms)
            cases_per_sec = (count / (avg_ms / 1000.0)) if avg_ms > 0 else 0.0
            us_per_case = (avg_ms * 1000.0) / count
            rows.append(
                {
                    "cases": count,
                    "assertions": count * 4,
                    "eval_ms": round(avg_ms, 3),
                    "us_per_case": round(us_per_case, 2),
                    "cases_per_sec": round(cases_per_sec, 1),
                    "token_burn_usd": 0.0,
                }
            )
        return {"reps": self.reps, "matrix": rows}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-eval-harness matrix",
        description="Run multi-scale deterministic evaluation throughput benchmark matrix.",
    )
    parser.add_argument("--cases", nargs="+", type=int, default=[10, 50, 100, 500])
    parser.add_argument("--reps", type=int, default=2)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    runner = EvalBenchMatrixRunner(case_counts=args.cases, reps=args.reps)
    result = runner.run_matrix()
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"[agent-eval-harness matrix] reps={result['reps']}")
        for row in result["matrix"]:
            print(
                f"  cases={row['cases']:>4} ({row['assertions']:>4} assertions) | "
                f"eval={row['eval_ms']:>6.2f}ms | {row['us_per_case']:>6.2f} us/case | "
                f"{row['cases_per_sec']:>9.1f} cases/s"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
