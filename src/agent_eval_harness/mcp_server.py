"""
Model Context Protocol (MCP) Server for agent-eval-harness.
Enables Claude Code, Cursor, and Benni OS agents to self-evaluate and verify goal completion.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List

from .assertions import Assertion, AssertionType
from .core import EvalHarness, TestCase
from .metrics import EvaluatorMetrics


def run_stdio() -> None:
    """Standard JSON-RPC 2.0 stdio server loop for Model Context Protocol."""
    harness = EvalHarness()

    while True:
        line = sys.stdin.readline()
        if not line:
            break

        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "agent-eval-harness",
                        "version": "1.0.0",
                    },
                },
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "notifications/initialized":
            pass

        elif method == "tools/list":
            tools = [
                {
                    "name": "evaluate_agent_run",
                    "description": "Evaluates an AI agent run against expected keywords, safety invariants, tool execution sequence, and latency budgets.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "output_text": {
                                "type": "string",
                                "description": "The candidate text produced by the agent.",
                            },
                            "required_keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Keywords that must be present.",
                            },
                            "forbidden_keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Keywords that must NOT be present.",
                            },
                            "actual_tool_calls": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of tool names actually called by the agent.",
                            },
                            "expected_tool_calls": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of tool names expected to be called in order.",
                            },
                        },
                        "required": ["output_text"],
                    },
                },
                {
                    "name": "check_red_team_leaks",
                    "description": "Scans candidate agent output for secret leakage, API keys, system prompts, and SSRF internal addresses.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Agent output to inspect.",
                            },
                        },
                        "required": ["text"],
                    },
                },
                {
                    "name": "validate_json_response",
                    "description": "Validates whether text is valid JSON and contains required top-level keys.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "json_text": {
                                "type": "string",
                                "description": "Candidate JSON text (can be markdown code block).",
                            },
                            "required_keys": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Keys that must be present.",
                            },
                        },
                        "required": ["json_text"],
                    },
                },
            ]
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": tools},
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})

            try:
                if name == "evaluate_agent_run":
                    output_text = args.get("output_text", "")
                    req_kws = args.get("required_keywords", [])
                    forb_kws = args.get("forbidden_keywords", [])
                    act_tools = args.get("actual_tool_calls", [])
                    exp_tools = args.get("expected_tool_calls", [])

                    assertions = [Assertion("Red Team Leak Check", AssertionType.NO_SECRETS_LEAKED)]
                    if req_kws:
                        assertions.append(Assertion("Required Keywords", AssertionType.CONTAINS, req_kws))
                    if forb_kws:
                        assertions.append(Assertion("Forbidden Keywords", AssertionType.NOT_CONTAINS, forb_kws))
                    if exp_tools:
                        assertions.append(Assertion("Tool Sequence", AssertionType.TOOL_SEQUENCE_MATCH, exp_tools))

                    case = TestCase(
                        id="mcp-eval-case",
                        goal="MCP Tool Evaluation",
                        candidate_output=output_text,
                        assertions=assertions,
                        metadata={"tool_calls": act_tools},
                    )
                    eval_result = harness.evaluate_case(case)
                    text_out = json.dumps(eval_result, indent=2)

                elif name == "check_red_team_leaks":
                    text = args.get("text", "")
                    has_leak, leaks = EvaluatorMetrics.check_red_team_leak(text)
                    res = {
                        "is_safe": not has_leak,
                        "leaks_detected": leaks,
                        "status": "PASS" if not has_leak else "FAILED_SECURITY_LEAK",
                    }
                    text_out = json.dumps(res, indent=2)

                elif name == "validate_json_response":
                    text = args.get("json_text", "")
                    keys = args.get("required_keys", [])
                    valid, parsed, detail = EvaluatorMetrics.validate_json_structure(text, required_keys=keys)
                    res = {
                        "valid": valid,
                        "detail": detail,
                        "parsed_keys": list(parsed.keys()) if parsed else [],
                    }
                    text_out = json.dumps(res, indent=2)

                else:
                    text_out = f"Unknown tool: {name}"

                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": text_out}],
                    },
                }
            except Exception as e:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(e)},
                }

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "ping":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio()
