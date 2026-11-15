"""Multi-Scale Evaluation Throughput Benchmark Script."""

from __future__ import annotations

import json

from agent_eval_harness.tools.bench_matrix import EvalBenchMatrixRunner


def main() -> None:
    runner = EvalBenchMatrixRunner(case_counts=[10, 50, 100, 500], reps=2)
    report = runner.run_matrix()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
