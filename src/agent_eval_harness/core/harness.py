"""
Core Agent Evaluation Harness and Suite Orchestrator.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .assertions import Assertion, AssertionResult
from .receipts import EvaluationReceipt, compute_sha256


@dataclass
class TestCase:
    __test__ = False
    id: str
    goal: str
    candidate_output: str
    assertions: List[Assertion] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "candidate_output": self.candidate_output,
            "metadata": self.metadata,
        }


@dataclass
class SuiteResult:
    suite_name: str
    receipt: EvaluationReceipt
    elapsed_ms: float


class EvalSuite:
    def __init__(
        self,
        name: str,
        pass_threshold: float = 0.8,
        task_version: str = "v1.0.0",
        policy_version: str = "2026.11-strict",
    ) -> None:
        self.name = name
        self.pass_threshold = pass_threshold
        self.task_version = task_version
        self.policy_version = policy_version
        self.cases: List[TestCase] = []

    def add_case(self, case: TestCase) -> None:
        self.cases.append(case)

    def compute_input_digest(self) -> str:
        """Computes deterministic RFC 8785 SHA-256 digest of input goals and metadata."""
        case_inputs = [{"id": c.id, "goal": c.goal, "metadata": c.metadata} for c in self.cases]
        return compute_sha256(case_inputs)

    def compute_ruleset_digest(self) -> str:
        """Computes deterministic RFC 8785 SHA-256 digest of invariant assertion ruleset."""
        rules = []
        for c in self.cases:
            for a in c.assertions:
                rules.append({
                    "case_id": c.id,
                    "assertion": a.name,
                    "assertion_type": getattr(a.assertion_type, "value", str(a.assertion_type)),
                    "expected_value": a.expected_value,
                    "weight": a.weight,
                })
        return compute_sha256(rules)


class EvalHarness:
    """
    Evaluates autonomous AI agent runs, RAG pipelines, and tool calls
    against deterministic invariant assertions.
    """

    def evaluate_case(self, case: TestCase) -> Dict[str, Any]:
        if not case.assertions:
            return {
                "case_id": case.id,
                "passed": True,
                "score": 1.0,
                "summary": "No assertions configured (Default PASS)",
                "assertion_results": [],
            }

        results: List[AssertionResult] = []
        total_weight = 0.0
        weighted_score = 0.0

        for a in case.assertions:
            res = a.evaluate(case.candidate_output, metadata=case.metadata)
            results.append(res)
            w = max(0.1, a.weight)
            total_weight += w
            weighted_score += res.score * w

        final_score = weighted_score / total_weight if total_weight > 0 else 0.0
        all_passed = all(r.passed for r in results)

        summary_parts = [f"{r.name}: {'✔' if r.passed else '✘'}" for r in results]
        summary = ", ".join(summary_parts)

        return {
            "case_id": case.id,
            "passed": all_passed,
            "score": round(final_score, 4),
            "summary": summary,
            "assertion_results": [r.to_dict() for r in results],
        }

    def run_suite(self, suite: EvalSuite) -> SuiteResult:
        t0 = time.perf_counter()
        case_records = []
        passed_count = 0
        total_score_sum = 0.0

        for c in suite.cases:
            rec = self.evaluate_case(c)
            case_records.append(rec)
            if rec["passed"]:
                passed_count += 1
            total_score_sum += rec["score"]

        total_cases = len(suite.cases)
        overall_score = (total_score_sum / total_cases) if total_cases > 0 else 1.0
        gate_verdict = "PASS" if overall_score >= suite.pass_threshold and passed_count == total_cases else "FAIL"

        input_digest = suite.compute_input_digest()
        ruleset_digest = suite.compute_ruleset_digest()

        receipt = EvaluationReceipt(
            suite_name=suite.name,
            total_cases=total_cases,
            passed_cases=passed_count,
            overall_score=round(overall_score, 4),
            gate_verdict=gate_verdict,
            case_results=case_records,
            task_version=suite.task_version,
            policy_version=suite.policy_version,
            input_digest=input_digest,
            ruleset_digest=ruleset_digest,
        )

        elapsed = (time.perf_counter() - t0) * 1000.0
        return SuiteResult(suite_name=suite.name, receipt=receipt, elapsed_ms=round(elapsed, 2))
