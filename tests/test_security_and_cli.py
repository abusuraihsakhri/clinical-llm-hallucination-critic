import csv
from pathlib import Path

import pytest

from agents.base import AuditTrail, PHIGuard, SecurityException
from agents.llm_factory import LLMFactory
from agents.models import SystemTaskPayload, UrgencyLevel
from agents.supervisor import SystemSupervisor
from cli import main


def test_hmac_verifier_detects_entry_tampering():
    trail = AuditTrail(secret_key="unit-test-secret")
    trail.log("tester", "unit", "event", {"value": 1})
    assert trail.verify_integrity() is True
    trail.logs[0]["event_type"] = "tampered"
    assert trail.verify_integrity() is False


def test_get_trail_returns_copy():
    trail = AuditTrail(secret_key="unit-test-secret")
    trail.log("tester", "unit", "event", {"value": 1})
    exported = trail.get_trail()
    exported[0]["event_type"] = "modified-copy"
    assert trail.verify_integrity() is True


def test_phi_guard_is_explicitly_pattern_based():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("MRN-123456")
    PHIGuard.assert_no_phi("CASE-123")


def test_unimplemented_model_provider_fails_closed():
    with pytest.raises(ValueError):
        LLMFactory.create("openai")


def test_supervisor_rule_evaluation():
    supervisor = SystemSupervisor()
    dossier = supervisor.process_task(
        SystemTaskPayload(
            task_id="T-1",
            target_identifier="TARGET-1",
            primary_metric=30,
            secondary_metric=2,
            status_descriptor="NOMINAL",
        )
    )
    assert dossier.overall_urgency == UrgencyLevel.ELEVATED
    assert dossier.total_alerts == 1


def test_batch_cli_round_trip(tmp_path: Path):
    source = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    source.write_text(
        "task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag,status_descriptor\n"
        "T1,TARGET1,10,2,False,NOMINAL\n",
        encoding="utf-8",
    )
    assert main(["batch", "-i", str(source), "-o", str(output)]) == 0
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["overall_urgency"] == "ROUTINE"
    assert rows[0]["audit_hash"]
