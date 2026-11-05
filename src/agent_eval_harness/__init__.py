"""
agent-eval-harness: Deterministic Zero-Cloud Agent Evaluation, Red-Teaming & Benchmark Harness
Part of Benni Master OS v9.4 ecosystem.
"""

from .core import EvalHarness, TestCase, EvalSuite, SuiteResult
from .assertions import Assertion, AssertionType, AssertionResult
from .metrics import EvaluatorMetrics
from .receipts import EvaluationReceipt, compute_sha256

__version__ = "1.1.0"
__author__ = "Benni Alencar"
__email__ = "bennialencar@gmail.com"
__all__ = [
    "EvalHarness",
    "TestCase",
    "EvalSuite",
    "SuiteResult",
    "Assertion",
    "AssertionType",
    "AssertionResult",
    "EvaluatorMetrics",
    "EvaluationReceipt",
    "compute_sha256",
    "__version__",
]
