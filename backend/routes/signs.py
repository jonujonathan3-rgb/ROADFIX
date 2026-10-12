from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db

router = APIRouter(
    prefix="/api/signs",
    tags=["Road Signs"]
)


@router.get("/")
def get_signs(
    db: Session = Depends(get_db)
):
    signs = (
        db.query(models.RoadSign)
        .order_by(models.RoadSign.created_at.desc())
        .all()
    )

    return signs


@router.get("/{sign_id}")
def get_sign(
    sign_id: int,
    db: Session = Depends(get_db)
):
    sign = (
        db.query(models.RoadSign)
        .filter(models.RoadSign.id == sign_id)
        .first()
    )

    if not sign:
        raise HTTPException(
            status_code=404,
            detail="Road sign not found"
        )

    return sign


@router.post("/")
def create_sign(
    sign_type: str,
    latitude: float,
    longitude: float,
    description: str | None = None,
    road_id: int | None = None,
    condition: str = "Good",
    replacement_required: bool = False,
    db: Session = Depends(get_db)
):
    if road_id is not None:
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

    sign = models.RoadSign(
        sign_type=sign_type,
        description=description,
        road_id=road_id,
        latitude=latitude,
        longitude=longitude,
        condition=condition,
        status="Active",
        replacement_required=replacement_required,
        created_at=datetime.utcnow()
    )

    db.add(sign)
    db.commit()
    db.refresh(sign)

    return {
        "success": True,
        "message": "Road sign created successfully",
        "sign": sign
    }


@router.put("/{sign_id}")
def update_sign(
    sign_id: int,
    condition: str | None = None,
    status: str | None = None,
    replacement_required: bool | None = None,
    description: str | None = None,
    db: Session = Depends(get_db)
):
    sign = (
        db.query(models.RoadSign)
        .filter(models.RoadSign.id == sign_id)
        .first()
    )

    if not sign:
        raise HTTPException(
            status_code=404,
            detail="Road sign not found"
        )

    if condition is not None:
        sign.condition = condition

    if status is not None:
        sign.status = status

    if replacement_required is not None:
        sign.replacement_required = replacement_required

    if description is not None:
        sign.description = description

    db.commit()
    db.refresh(sign)

    return {
        "success": True,
        "message": "Road sign updated successfully",
        "sign": sign
    }