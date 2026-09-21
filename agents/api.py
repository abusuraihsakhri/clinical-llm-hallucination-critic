"""FastAPI interface for the deterministic prototype."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .base import AuditLogger, SecurityException
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Clinical LLM Hallucination Critic API",
    description="Deterministic rule-based prototype API for testing critic workflow plumbing.",
    version="2.1.0",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {
        "status": "HEALTHY",
        "service": "clinical-llm-hallucination-critic",
        "mode": "rule-based prototype",
        "version": "2.1.0",
    }


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "READY",
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        return supervisor.process_task(payload).to_dict()
    except SecurityException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except SecurityException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
