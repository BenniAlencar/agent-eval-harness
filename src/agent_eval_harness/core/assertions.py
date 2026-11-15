"""
Assertion Engine for Agentic Invariants and Goal Completion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .metrics import EvaluatorMetrics


class AssertionType(str, Enum):
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX_MATCH = "regex_match"
    JSON_SCHEMA = "json_schema"
    SIMILARITY_THRESHOLD = "similarity_threshold"
    NO_SECRETS_LEAKED = "no_secrets_leaked"
    LATENCY_UNDER_MS = "latency_under_ms"
    TOOL_SEQUENCE_MATCH = "tool_sequence_match"


@dataclass
class AssertionResult:
    name: str
    assertion_type: AssertionType
    passed: bool
    score: float
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "assertion_type": self.assertion_type.value,
            "passed": self.passed,
            "score": round(self.score, 4),
            "message": self.message,
        }


@dataclass
class Assertion:
    name: str
    assertion_type: AssertionType
    expected_value: Any = None
    weight: float = 1.0

    def evaluate(self, candidate_text: str, metadata: Optional[Dict[str, Any]] = None) -> AssertionResult:
        meta = metadata or {}
        val = self.expected_value

        if self.assertion_type == AssertionType.CONTAINS:
            if isinstance(val, list):
                ratio, missing = EvaluatorMetrics.keyword_density(candidate_text, val)
                passed = (ratio >= 1.0)
                msg = "All expected keywords present." if passed else f"Missing keywords: {missing}"
                return AssertionResult(self.name, self.assertion_type, passed, ratio, msg)
            else:
                passed = str(val).lower() in candidate_text.lower()
                return AssertionResult(self.name, self.assertion_type, passed, 1.0 if passed else 0.0,
                                       f"Expected to contain '{val}'.")

        elif self.assertion_type == AssertionType.NOT_CONTAINS:
            items = val if isinstance(val, list) else [val]
            found = [str(x) for x in items if str(x).lower() in candidate_text.lower()]
            passed = len(found) == 0
            msg = "No forbidden items detected." if passed else f"Found forbidden items: {found}"
            return AssertionResult(self.name, self.assertion_type, passed, 1.0 if passed else 0.0, msg)

        elif self.assertion_type == AssertionType.REGEX_MATCH:
            passed = bool(re.search(str(val), candidate_text, flags=re.MULTILINE))
            return AssertionResult(self.name, self.assertion_type, passed, 1.0 if passed else 0.0,
                                   f"Regex pattern match: '{val}'.")

        elif self.assertion_type == AssertionType.JSON_SCHEMA:
            req_keys = val if isinstance(val, list) else []
            valid, _, detail = EvaluatorMetrics.validate_json_structure(candidate_text, required_keys=req_keys)
            return AssertionResult(self.name, self.assertion_type, valid, 1.0 if valid else 0.0, detail)

        elif self.assertion_type == AssertionType.SIMILARITY_THRESHOLD:
            target = meta.get("ground_truth", "")
            thresh = float(val or 0.6)
            sim = EvaluatorMetrics.jaccard_similarity(candidate_text, target)
            passed = sim >= thresh
            msg = f"Similarity: {sim:.2f} (Threshold: {thresh:.2f})"
            return AssertionResult(self.name, self.assertion_type, passed, sim, msg)

        elif self.assertion_type == AssertionType.NO_SECRETS_LEAKED:
            has_leak, patterns = EvaluatorMetrics.check_red_team_leak(candidate_text)
            passed = not has_leak
            msg = "Zero secrets or SSRF leaks detected." if passed else f"Red-team violation: leaked {patterns}"
            return AssertionResult(self.name, self.assertion_type, passed, 1.0 if passed else 0.0, msg)

        elif self.assertion_type == AssertionType.LATENCY_UNDER_MS:
            latency = float(meta.get("latency_ms", 0.0))
            max_lat = float(val or 500.0)
            passed = latency <= max_lat
            msg = f"Execution Latency: {latency:.2f}ms (Limit: {max_lat:.1f}ms)"
            return AssertionResult(self.name, self.assertion_type, passed, 1.0 if passed else 0.0, msg)

        elif self.assertion_type == AssertionType.TOOL_SEQUENCE_MATCH:
            actual_tools = meta.get("tool_calls", [])
            expected_tools = val if isinstance(val, list) else []
            passed, score = EvaluatorMetrics.evaluate_tool_sequence(actual_tools, expected_tools)
            msg = f"Tool Sequence Adherence: {int(score * 100)}%"
            return AssertionResult(self.name, self.assertion_type, passed, score, msg)

        return AssertionResult(self.name, self.assertion_type, False, 0.0, "Unknown assertion type.")
