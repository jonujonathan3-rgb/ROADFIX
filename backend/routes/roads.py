from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db


router = APIRouter(
    prefix="/api/roads",
    tags=["Roads"]
)


@router.get("/")
def get_roads(
    db: Session = Depends(get_db)
):
    roads = (
        db.query(models.Road)
        .order_by(models.Road.created_at.desc())
        .all()
    )

    return roads


@router.get("/{road_id}")
def get_road(
    road_id: int,
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

    return road


@router.post("/")
def create_road(
    road_name: str,
    road_code: str,
    area: str,
    latitude: float,
    longitude: float,
    road_type: str = "Urban",
    condition: str = "Good",
    risk_level: str = "LOW",
    traffic_level: str = "Medium",
    db: Session = Depends(get_db)
):
    existing_road = (
        db.query(models.Road)
        .filter(models.Road.road_code == road_code)
        .first()
    )

    if existing_road:
        raise HTTPException(
            status_code=400,
            detail="Road code already exists"
        )

    road = models.Road(
        road_name=road_name,
        road_code=road_code,
        area=area,
        latitude=latitude,
        longitude=longitude,
        road_type=road_type,
        condition=condition,
        risk_level=risk_level,
        traffic_level=traffic_level,
        last_inspection=datetime.utcnow(),
        status="Active",
        created_at=datetime.utcnow()
    )

    db.add(road)
    db.commit()
    db.refresh(road)

    return {
        "success": True,
        "message": "Road created successfully",
        "road": road
    }


@router.put("/{road_id}")
def update_road(
    road_id: int,
    condition: str | None = None,
    risk_level: str | None = None,
    traffic_level: str | None = None,
    status: str | None = None,
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

    if condition is not None:
        road.condition = condition

    if risk_level is not None:
        road.risk_level = risk_level

    if traffic_level is not None:
        road.traffic_level = traffic_level

    if status is not None:
        road.status = status

    road.last_inspection = datetime.utcnow()

    db.commit()
    db.refresh(road)

    return {
        "success": True,
        "message": "Road updated successfully",
        "road": road
    }