from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db


router = APIRouter(
    prefix="/api/work-orders",
    tags=["Work Orders"]
)


@router.get("/")
def get_work_orders(
    db: Session = Depends(get_db)
):
    work_orders = (
        db.query(models.WorkOrder)
        .order_by(models.WorkOrder.created_at.desc())
        .all()
    )

    return work_orders


@router.get("/{work_order_id}")
def get_work_order(
    work_order_id: int,
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

    return work_order


@router.post("/")
def create_work_order(
    road_id: int,
    title: str,
    description: str,
    priority: str = "MEDIUM",
    complaint_id: int | None = None,
    db: Session = Depends(get_db)
):
    road = (
        db.query(models.Road)
        .filter(models.Road.id == road_id)
        .first()
    )

    if not road:
        raise HTTPException(
            status_code=404,
            detail="Road not found"
        )

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

    work_order = models.WorkOrder(
        road_id=road_id,
        complaint_id=complaint_id,
        title=title,
        description=description,
        priority=priority,
        status="Pending",
        created_at=datetime.utcnow()
    )

    db.add(work_order)
    db.commit()
    db.refresh(work_order)

    return {
        "success": True,
        "message": "Work order created successfully",
        "work_order": work_order
    }


@router.put("/{work_order_id}")
def update_work_order(
    work_order_id: int,
    status: str | None = None,
    contractor_name: str | None = None,
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

    if status is not None:
        normalized_status = status.strip().lower()

        work_order.status = status
        current_time = datetime.utcnow()

        if normalized_status == "assigned":
            if work_order.assigned_at is None:
                work_order.assigned_at = current_time

        elif normalized_status == "in progress":
            if work_order.started_at is None:
                work_order.started_at = current_time

        elif normalized_status == "completed":
            if work_order.completed_at is None:
                work_order.completed_at = current_time

        # Synchronize the linked complaint.
        if work_order.complaint_id is not None:
            complaint = (
                db.query(models.Complaint)
                .filter(
                    models.Complaint.id == work_order.complaint_id
                )
                .first()
            )

            if complaint:
                if normalized_status == "assigned":
                    complaint.status = "Assigned"

                elif normalized_status == "in progress":
                    complaint.status = "In Progress"

                elif normalized_status == "completed":
                    complaint.status = "Completed"

    if contractor_name is not None:
        work_order.contractor_name = contractor_name

    db.commit()
    db.refresh(work_order)

    return {
        "success": True,
        "message": "Work order updated successfully",
        "work_order": work_order
    }