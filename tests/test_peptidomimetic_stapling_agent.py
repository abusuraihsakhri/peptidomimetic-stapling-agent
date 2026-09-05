"""
Automated Pytest Test Suite for Peptidomimetic Stapling Agent.
Domain: AI Drug Discovery, Structural Biology & Wet-Lab Robotics
Standard: wwPDB / IUPAC / OpenSMILES / ISAC Standards
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_phi_guard_blocks_various_patterns():
    """Test that PHI guard catches multiple sensitive data patterns."""
    phi_samples = [
        "Patient MRN-12345678",
        "SSN 123-45-6789",
        "Contact: 555-123-4567",
        "Email: patient@example.com",
        "DOB: 01/15/1985",
        "Patient: John Smith",
    ]
    for sample in phi_samples:
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi(sample)


def test_phi_redaction():
    """Test that PHI is properly redacted."""
    text = "Patient MRN-12345678 called from 555-123-4567"
    redacted = PHIGuard.redact_phi(text)
    assert "MRN-12345678" not in redacted
    assert "555-123-4567" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted


def test_safe_resolve_path_exists():
    """Test safe_resolve_path with existing file."""
    from agents.base import safe_resolve_path
    import os
    result = safe_resolve_path("cli.py", must_exist=True)
    assert os.path.isfile(result)


def test_safe_resolve_path_not_found():
    """Test safe_resolve_path raises for missing files."""
    from agents.base import safe_resolve_path
    with pytest.raises(FileNotFoundError):
        safe_resolve_path("/nonexistent/path/file.csv", must_exist=True)


def test_safe_resolve_path_traversal():
    """Test safe_resolve_path resolves traversal attempts safely."""
    from agents.base import safe_resolve_path
    import os
    # Should resolve to absolute path without raising for non-existent
    result = safe_resolve_path("../cli.py", must_exist=False)
    assert os.path.isabs(result)
