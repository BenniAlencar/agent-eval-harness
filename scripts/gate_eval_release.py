"""Release Readiness & Cryptographic Integrity Gate for agent-eval-harness."""

from __future__ import annotations

import sys

from agent_eval_harness.tools.doctor import run_doctor


def main() -> int:
    report = run_doctor()
    print(f"Eval Release Gate: status={report['status']} ok={report['ok']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
