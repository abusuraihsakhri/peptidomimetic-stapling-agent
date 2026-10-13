"""Regressions for audit verification, input handling and position screening."""
import pytest
from pydantic import ValidationError
from agents.base import AuditTrail, PHIGuard, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from cli import parse_critical_flag as root_parse, main as root_main
from peptido_staple.cli import parse_critical_flag as legacy_parse, main as legacy_main
from peptido_staple.staples import enumerate_staple_sites


def test_hmac_verification_detects_tampered_metadata_and_signature():
    audit = AuditTrail("test-key")
    audit.log("worker", "tier", "created", {"status": "ok"})
    assert audit.verify_integrity()
    audit.logs[0]["actor"] = "attacker"
    assert not audit.verify_integrity()
    audit.logs[0]["actor"] = "worker"
    audit.logs[0]["current_hash"] = "0" * 64
    assert not audit.verify_integrity()


def test_audit_trail_returns_snapshot():
    audit = AuditTrail("test-key")
    audit.log("worker", "tier", "created", {"status": "ok"})
    copy = audit.get_trail()
    copy[0]["actor"] = "attacker"
    assert audit.verify_integrity()


@pytest.mark.parametrize("parser", [root_parse, legacy_parse])
def test_csv_booleans(parser):
    assert parser("False") is False
    assert parser("TRUE") is True
    assert parser("0") is False
    assert parser("1") is True
    with pytest.raises(ValueError):
        parser("occasionally")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_metrics_rejected(value):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T1", target_identifier="SEQ", primary_metric=value)


def test_nested_sensitive_metadata_rejected():
    supervisor = SystemSupervisor()
    payload = SystemTaskPayload(task_id="T1", target_identifier="SEQ", primary_metric=1,
                                attributes={"notes": "patient@example.com"})
    with pytest.raises(SecurityException):
        supervisor.process_task(payload)


def test_staple_position_enumeration():
    result = enumerate_staple_sites("ACDEFGHIK")
    assert len(result) == 7  # 5 i+4 plus 2 i+7 candidates
    assert result[0]["start_position"] == 1
    assert result[0]["end_position"] == 5
    assert result[5]["spacing"] == "i,i+7"
    assert all(not r["contains_proline"] for r in result)
    assert enumerate_staple_sites("AAPAAAAA", (7,))[0]["contains_proline"] is True


@pytest.mark.parametrize("sequence", ["", "AAAA1", "ACX", "A" * 501])
def test_invalid_staple_sequences(sequence):
    with pytest.raises(ValueError):
        enumerate_staple_sites(sequence)


def test_cli_design_commands(capsys):
    assert root_main(["design", "--sequence", "ACDEFGHI", "--spacing", "7"]) == 0
    assert '"candidate_count": 1' in capsys.readouterr().out
    assert legacy_main(["design", "--sequence", "ACDEFGHI", "--spacing", "4"]) == 0
    assert '"candidate_count": 4' in capsys.readouterr().out


def test_api_rejects_sensitive_input_and_nonfinite_metrics():
    from fastapi.testclient import TestClient
    from agents.api import app
    client = TestClient(app)
    request = {"task_id": "T1", "target_identifier": "SEQ", "primary_metric": 1,
               "attributes": {"note": "patient@example.com"}}
    response = client.post("/api/audit", json=request)
    assert response.status_code == 422
    request["attributes"] = {}
    request["primary_metric"] = "NaN"
    response = client.post("/api/audit", json=request)
    assert response.status_code == 422


def test_unimplemented_llm_providers_are_not_misrepresented():
    from agents.llm_factory import LLMFactory
    with pytest.raises(ValueError):
        LLMFactory.create("openai")
    assert "Mock response" in LLMFactory.create("mock").invoke("status")
