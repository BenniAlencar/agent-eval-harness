# agent-eval-harness Architecture

`agent-eval-harness` is organized into three clean architectural layers matching the Benni OS v9.4 Python OSS standard:

## 1. `core/` — Deterministic Evaluation & RFC 8785 Receipt Layer
- `core/harness.py`: `EvalHarness`, `EvalSuite`, `TestCase`, and `SuiteResult` orchestrating zero-cloud assertion evaluation and pass-threshold gating.
- `core/assertions.py`: `Assertion`, `AssertionType`, and `AssertionResult` covering JSON schema, keyword containment, tool-call sequence matching, latency budgets, and red-team secret checks.
- `core/metrics.py`: `EvaluatorMetrics` providing Jaccard/Levenshtein similarity, keyword density, JSON structural validation, and secret/SSRF leak detection.
- `core/receipts.py`: `EvaluationReceipt` implementing RFC 8785 JSON Canonicalization Scheme (JCS) SHA-256 Merkle root receipts and `verify_reproducibility()`.

## 2. `serve/` — MCP Transport, Telemetry & Health Monitoring
- `serve/mcp_server.py`: Native JSON-RPC 2.0 stdio MCP server exposing `evaluate_agent_run`, `check_red_team_leaks`, and `validate_json_response`.
- `serve/telemetry.py`: `EvalTelemetryEngine` tracking suite evaluation P50/P90/P99 latency, pass-rate %, red-team leak counts, and assertion distributions.
- `serve/health_monitor.py`: `EvalHealthMonitor` verifying red-team scanner accuracy and RFC 8785 receipt reproducibility self-tests.

## 3. `tools/` — Diagnostics & Benchmark Matrix
- `tools/doctor.py`: `run_doctor()` and `agent-eval-harness doctor` CLI probe.
- `tools/bench_matrix.py`: `EvalBenchMatrixRunner` and `agent-eval-harness matrix` CLI sweep across `[10, 50, 100, 500]` test cases.
