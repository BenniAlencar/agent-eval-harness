"""Tests for core/serve/tools subpackages in agent-eval-harness."""

from __future__ import annotations

import json

from agent_eval_harness.cli import main as cli_main
from agent_eval_harness.serve import EvalHealthMonitor, EvalTelemetryEngine
from agent_eval_harness.tools import EvalBenchMatrixRunner, run_doctor


def test_telemetry_engine_records_suites() -> None:
    tel = EvalTelemetryEngine(max_history=10)
    tel.record_suite(
        latency_ms=2.4,
        cases_count=10,
        passed_cases=9,
        gate_passed=True,
        leaks_detected=1,
        assertion_types=["JSON_SCHEMA", "NO_SECRETS_LEAKED"],
    )
    summary = tel.get_summary()

    assert summary["total_suites"] == 1
    assert summary["total_cases"] == 10
    assert summary["total_passed_cases"] == 9
    assert summary["pass_rate_pct"] == 90.0
    assert summary["total_leaks_detected"] == 1
    assert summary["suite_latency_ms"]["p50"] == 2.4


def test_health_monitor_and_doctor() -> None:
    health = EvalHealthMonitor().check_health()
    assert health["status"] == "healthy"
    assert health["red_team_scanner"]["passed"] is True
    assert health["receipt_self_test"]["passed"] is True

    report = run_doctor()
    assert report["ok"] is True


def test_bench_matrix_runner() -> None:
    runner = EvalBenchMatrixRunner(case_counts=[5, 10], reps=1)
    res = runner.run_matrix()
    assert res["reps"] == 1
    assert len(res["matrix"]) == 2
    assert res["matrix"][0]["cases"] == 5
    assert res["matrix"][1]["cases"] == 10
    assert res["matrix"][0]["token_burn_usd"] == 0.0


def test_cli_doctor_and_matrix_json(capsys) -> None:
    rc_doc = cli_main(["doctor", "--json"])
    assert rc_doc == 0
    doc_payload = json.loads(capsys.readouterr().out)
    assert doc_payload["ok"] is True

    rc_mat = cli_main(["matrix", "--cases", "5", "10", "--reps", "1", "--json"])
    assert rc_mat == 0
    mat_payload = json.loads(capsys.readouterr().out)
    assert len(mat_payload["matrix"]) == 2
