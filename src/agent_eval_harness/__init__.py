"""
agent-eval-harness: Deterministic Zero-Cloud Agent Evaluation, Red-Teaming & Benchmark Harness
Part of Benni Master OS v9.4 ecosystem.
"""

from .core import (
    Assertion,
    AssertionResult,
    AssertionType,
    EvalHarness,
    EvalSuite,
    EvaluationReceipt,
    EvaluatorMetrics,
    SuiteResult,
    TestCase,
    compute_sha256,
)
from .serve import EvalHealthMonitor, EvalTelemetryEngine
from .tools import EvalBenchMatrixRunner, run_doctor

__version__ = "1.1.0"
__author__ = "Benni Alencar"
__email__ = "bennialencar@gmail.com"
__all__ = [
    "EvalBenchMatrixRunner",
    "EvalHarness",
    "EvalHealthMonitor",
    "EvalTelemetryEngine",
    "TestCase",
    "EvalSuite",
    "SuiteResult",
    "Assertion",
    "AssertionType",
    "AssertionResult",
    "EvaluatorMetrics",
    "EvaluationReceipt",
    "compute_sha256",
    "run_doctor",
    "__version__",
]
