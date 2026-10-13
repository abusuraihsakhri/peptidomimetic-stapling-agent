"""
FastAPI REST API Server for Peptidomimetic Stapling Agent.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Peptidomimetic Stapling Agent API",
    description="Generic deterministic threshold audits; not validated peptide-property predictions",
    version="3.0.0-ENTERPRISE",
)


@app.exception_handler(SecurityException)
async def sensitive_input_handler(request: Request, exc: SecurityException):
    return JSONResponse(status_code=422, content={"detail": "Sensitive identifier detected; remove it and retry."})


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "peptidomimetic-stapling-agent", "domain": "AI Drug Discovery, Structural Biology & Wet-Lab Robotics", "standard": "Project-defined heuristic thresholds (unvalidated)", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to process request") from exc


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
