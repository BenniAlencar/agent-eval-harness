"""Real-Time Telemetry Engine for agent-eval-harness.

Captures evaluation suite latency percentiles (P50, P90, P99), pass/fail gate
ratios, red-team leak detections, and assertion type distributions.
"""

from __future__ import annotations

import statistics
import time
from typing import Any


class EvalTelemetryEngine:
    """Collects real-time evaluation, red-teaming, and receipt telemetry."""

    def __init__(self, max_history: int = 500) -> None:
        self.max_history = max_history
        self.suite_latencies_ms: list[float] = []
        self.assertion_counts: dict[str, int] = {}
        self.start_time = time.time()
        self.total_suites = 0
        self.total_cases = 0
        self.total_passed_cases = 0
        self.total_gate_failures = 0
        self.total_leaks_detected = 0

    def record_suite(
        self,
        latency_ms: float,
        cases_count: int,
        passed_cases: int,
        gate_passed: bool,
        leaks_detected: int = 0,
        assertion_types: list[str] | None = None,
    ) -> None:
        """Record metrics for an executed evaluation suite."""
        self.suite_latencies_ms.append(latency_ms)
        if len(self.suite_latencies_ms) > self.max_history:
            self.suite_latencies_ms.pop(0)

        self.total_suites += 1
        self.total_cases += cases_count
        self.total_passed_cases += passed_cases
        if not gate_passed:
            self.total_gate_failures += 1
        self.total_leaks_detected += leaks_detected

        if assertion_types:
            for atype in assertion_types:
                self.assertion_counts[atype] = self.assertion_counts.get(atype, 0) + 1

    @staticmethod
    def _percentile(values: list[float], p: float) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = int(round((p / 100.0) * (len(sorted_vals) - 1)))
        return round(sorted_vals[idx], 3)

    def get_summary(self) -> dict[str, Any]:
        """Return aggregated telemetry snapshot."""
        uptime = max(0.001, time.time() - self.start_time)
        avg_ms = (
            round(statistics.mean(self.suite_latencies_ms), 3)
            if self.suite_latencies_ms
            else 0.0
        )
        pass_rate = (
            round((self.total_passed_cases / self.total_cases) * 100.0, 2)
            if self.total_cases > 0
            else 0.0
        )
        return {
            "uptime_s": round(uptime, 2),
            "total_suites": self.total_suites,
            "total_cases": self.total_cases,
            "total_passed_cases": self.total_passed_cases,
            "pass_rate_pct": pass_rate,
            "total_gate_failures": self.total_gate_failures,
            "total_leaks_detected": self.total_leaks_detected,
            "suite_latency_ms": {
                "avg": avg_ms,
                "p50": self._percentile(self.suite_latencies_ms, 50),
                "p90": self._percentile(self.suite_latencies_ms, 90),
                "p99": self._percentile(self.suite_latencies_ms, 99),
            },
            "assertion_distribution": dict(self.assertion_counts),
        }
