from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db


router = APIRouter(
    prefix="/api/inspections",
    tags=["Inspections"]
)


@router.get("/")
def get_inspections(
    db: Session = Depends(get_db)
):
    inspections = (
        db.query(models.Inspection)
        .order_by(models.Inspection.inspection_date.desc())
        .all()
    )

    return inspections


@router.get("/{inspection_id}")
def get_inspection(
    inspection_id: int,
    db: Session = Depends(get_db)
):
    inspection = (
        db.query(models.Inspection)
        .filter(models.Inspection.id == inspection_id)
        .first()
    )

    if not inspection:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found"
        )

    return inspection


@router.post("/")
def create_inspection(
    road_id: int,
    inspector_name: str,
    condition: str,
    risk_level: str,
    findings: str,
    recommended_action: str | None = None,
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

    inspection = models.Inspection(
        road_id=road_id,
        inspector_name=inspector_name,
        inspection_date=datetime.utcnow(),
        condition=condition,
        risk_level=risk_level,
        findings=findings,
        recommended_action=recommended_action,
        created_at=datetime.utcnow()
    )

    db.add(inspection)

    # Update the road based on inspection
    road.condition = condition
    road.risk_level = risk_level
    road.last_inspection = datetime.utcnow()

    db.commit()
    db.refresh(inspection)

    return {
        "success": True,
        "message": "Inspection recorded successfully",
        "inspection": inspection,
        "road_updated": True
    }