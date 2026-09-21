"""Deterministic threshold workers used by the prototype."""
import uuid
from typing import List

from .models import AgentAlert, SystemTaskPayload, UrgencyLevel


class InvariantQCWorker:
    """Flag a primary metric above the configured demonstration threshold."""

    @classmethod
    def evaluate(cls, payload: SystemTaskPayload) -> List[AgentAlert]:
        alerts = []
        if payload.primary_metric > 25.0:
            alerts.append(
                AgentAlert(
                    alert_id=f"QC-{uuid.uuid4().hex[:6]}",
                    origin_worker="InvariantQCWorker",
                    urgency=UrgencyLevel.ELEVATED,
                    summary="Primary metric threshold exceeded",
                    technical_details=(
                        f"Primary metric ({payload.primary_metric:.2f}) is above the configured "
                        "prototype threshold (25.00)."
                    ),
                    actionable_remediation="Review the input and threshold configuration before interpreting the result.",
                )
            )
        return alerts


class SafetyEscalationWorker:
    """Flag a manual critical input or elevated secondary demo metric."""

    @classmethod
    def evaluate(cls, payload: SystemTaskPayload) -> List[AgentAlert]:
        alerts = []
        if payload.is_critical_flag or payload.secondary_metric > 12.0:
            alerts.append(
                AgentAlert(
                    alert_id=f"SAFE-{uuid.uuid4().hex[:6]}",
                    origin_worker="SafetyEscalationWorker",
                    urgency=UrgencyLevel.CRITICAL_STAT if payload.is_critical_flag else UrgencyLevel.ELEVATED,
                    summary="Secondary rule triggered",
                    technical_details=(
                        f"CriticalFlag={payload.is_critical_flag}; secondary metric={payload.secondary_metric:.2f}; "
                        "configured threshold=12.00."
                    ),
                    actionable_remediation="Review the source data and rule configuration; this result is not clinical advice.",
                )
            )
        return alerts


class ProtocolConformanceWorker:
    """Flag configured keywords in the free-text status descriptor."""

    FLAGS = ("DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT")

    @classmethod
    def evaluate(cls, payload: SystemTaskPayload) -> List[AgentAlert]:
        alerts = []
        descriptor = str(payload.status_descriptor)
        if any(word in descriptor.upper() for word in cls.FLAGS):
            alerts.append(
                AgentAlert(
                    alert_id=f"CONF-{uuid.uuid4().hex[:6]}",
                    origin_worker="ProtocolConformanceWorker",
                    urgency=UrgencyLevel.ELEVATED,
                    summary="Status descriptor matched a review keyword",
                    technical_details=f"Descriptor '{descriptor}' matched the configured prototype keyword list.",
                    actionable_remediation="Review the descriptor and supporting source text manually.",
                )
            )
        return alerts
