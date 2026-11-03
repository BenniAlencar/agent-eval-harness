import pytest
from agent_eval_harness.assertions import Assertion, AssertionType


def test_assertion_contains_and_not_contains():
    text = "Deployment successful in region us-east-1."
    a1 = Assertion("Contains Deployment", AssertionType.CONTAINS, "deployment")
    res1 = a1.evaluate(text)
    assert res1.passed is True

    a2 = Assertion("Not Contains Error", AssertionType.NOT_CONTAINS, ["error", "fatal", "exception"])
    res2 = a2.evaluate(text)
    assert res2.passed is True

    a3 = Assertion("Failing Contains", AssertionType.CONTAINS, "critical failure")
    res3 = a3.evaluate(text)
    assert res3.passed is False


def test_assertion_json_and_secrets():
    json_payload = '{"auth": "token", "user": "benni"}'
    a1 = Assertion("Valid Auth JSON", AssertionType.JSON_SCHEMA, ["auth", "user"])
    res1 = a1.evaluate(json_payload)
    assert res1.passed is True

    a2 = Assertion("No Secrets", AssertionType.NO_SECRETS_LEAKED)
    res2 = a2.evaluate("Confidential report without tokens.")
    assert res2.passed is True

    res3 = a2.evaluate("Private token: ghp_123456789012345678901234567890123456")
    assert res3.passed is False


def test_assertion_latency_and_tools():
    a_lat = Assertion("Latency Check", AssertionType.LATENCY_UNDER_MS, 100.0)
    res_lat = a_lat.evaluate("", metadata={"latency_ms": 42.5})
    assert res_lat.passed is True

    res_lat_fail = a_lat.evaluate("", metadata={"latency_ms": 150.0})
    assert res_lat_fail.passed is False
