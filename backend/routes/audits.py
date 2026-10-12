from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db

router = APIRouter(
    prefix="/api/audits",
    tags=["Audits"]
)


@router.get("/")
def get_audits(
    db: Session = Depends(get_db)
):
    audits = (
        db.query(models.AuditLog)
        .order_by(models.AuditLog.created_at.desc())
        .all()
    )

    return audits


@router.get("/{audit_id}")
def get_audit(
    audit_id: int,
    db: Session = Depends(get_db)
):
    audit = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.id == audit_id)
        .first()
    )

    if not audit:
        raise HTTPException(
            status_code=404,
            detail="Audit record not found"
        )

    return audit


@router.post("/")
def create_audit(
    action: str,
    performed_by: str,
    description: str | None = None,
    complaint_id: int | None = None,
    work_order_id: int | None = None,
    db: Session = Depends(get_db)
):
    if complaint_id is not None:
        complaint = (
            db.query(models.Complaint)
            .filter(models.Complaint.id == complaint_id)
            .first()
        )

        if not complaint:
            raise HTTPException(
                status_code=404,
                detail="Complaint not found"
            )

    if work_order_id is not None:
        work_order = (
            db.query(models.WorkOrder)
            .filter(models.WorkOrder.id == work_order_id)
            .first()
        )

        if not work_order:
            raise HTTPException(
                status_code=404,
                detail="Work order not found"
            )

    audit = models.AuditLog(
        complaint_id=complaint_id,
        work_order_id=work_order_id,
        action=action,
        performed_by=performed_by,
        description=description,
        created_at=datetime.utcnow()
    )

    db.add(audit)
    db.commit()
    db.refresh(audit)

    return {
        "success": True,
        "message": "Audit record created successfully",
        "audit": audit
    }