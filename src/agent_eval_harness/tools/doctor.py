"""Eval Doctor — Runtime diagnostics, red-team scanner & RFC 8785 receipt probe."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from typing import Any

from ..serve.health_monitor import EvalHealthMonitor


def run_doctor() -> dict[str, Any]:
    """Run full diagnostic suite for agent-eval-harness."""
    health = EvalHealthMonitor().check_health()
    ok = health["status"] == "healthy"
    return {
        "ok": ok,
        "status": health["status"],
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "red_team_scanner": health["red_team_scanner"],
        "receipt_self_test": health["receipt_self_test"],
        "warnings": health["warnings"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-eval-harness doctor",
        description="Run local diagnostics for red-team scanner and RFC 8785 receipts.",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON output.")
    args = parser.parse_args(argv)

    report = run_doctor()
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        badge = "OK" if report["ok"] else "WARN"
        print(f"[agent-eval-harness doctor] Status: {badge} ({report['status']})")
        print(f"  Python   : {report['python_version']} ({report['platform']})")
        print(f"  Red-Team : passed={report['red_team_scanner']['passed']}")
        print(
            f"  Receipts : passed={report['receipt_self_test']['passed']} "
            f"({report['receipt_self_test']['elapsed_ms']} ms)"
        )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
