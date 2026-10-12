from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db

router = APIRouter(
    prefix="/api/verifications",
    tags=["Verifications"]
)


@router.get("/")
def get_verifications(
    db: Session = Depends(get_db)
):
    verifications = (
        db.query(models.Verification)
        .order_by(models.Verification.created_at.desc())
        .all()
    )

    return verifications


@router.get("/{verification_id}")
def get_verification(
    verification_id: int,
    db: Session = Depends(get_db)
):
    verification = (
        db.query(models.Verification)
        .filter(models.Verification.id == verification_id)
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=404,
            detail="Verification not found"
        )

    return verification


@router.post("/")
def create_verification(
    work_order_id: int,
    verifier_name: str,
    result: str = "Pending",
    remarks: str | None = None,
    photo_filename: str | None = None,
    db: Session = Depends(get_db)
):
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

    verification = models.Verification(
        work_order_id=work_order_id,
        verifier_name=verifier_name,
        verification_date=datetime.utcnow(),
        result=result,
        remarks=remarks,
        photo_filename=photo_filename,
        created_at=datetime.utcnow()
    )

    db.add(verification)

    # If verification is approved,
    # mark the related work order as completed
    # and update the linked complaint.
    if result.lower() == "approved":

        work_order.status = "Completed"

        if work_order.completed_at is None:
            work_order.completed_at = datetime.utcnow()

        # Update the linked complaint status
        if work_order.complaint_id is not None:

            complaint = (
                db.query(models.Complaint)
                .filter(
                    models.Complaint.id == work_order.complaint_id
                )
                .first()
            )

            if complaint:
                complaint.status = "Completed"

    db.commit()
    db.refresh(verification)

    return {
        "success": True,
        "message": "Verification recorded successfully",
        "verification": verification,
        "work_order_updated": result.lower() == "approved"
    }
@router.put("/{verification_id}")
def update_verification(
    verification_id: int,
    result: str | None = None,
    remarks: str | None = None,
    photo_filename: str | None = None,
    db: Session = Depends(get_db)
):
    verification = (
        db.query(models.Verification)
        .filter(models.Verification.id == verification_id)
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=404,
            detail="Verification not found"
        )

    if result is not None:
        verification.result = result

        if result.strip().lower() == "approved":
            work_order = (
                db.query(models.WorkOrder)
                .filter(
                    models.WorkOrder.id == verification.work_order_id
                )
                .first()
            )

            if work_order:
                work_order.status = "Completed"

                if work_order.completed_at is None:
                    work_order.completed_at = datetime.utcnow()

                if work_order.complaint_id is not None:
                    complaint = (
                        db.query(models.Complaint)
                        .filter(
                            models.Complaint.id == work_order.complaint_id
                        )
                        .first()
                    )

                    if complaint:
                        complaint.status = "Completed"

    if remarks is not None:
        verification.remarks = remarks

    if photo_filename is not None:
        verification.photo_filename = photo_filename

    db.commit()
    db.refresh(verification)

    return {
        "success": True,
        "message": "Verification updated successfully",
        "verification": verification
    }