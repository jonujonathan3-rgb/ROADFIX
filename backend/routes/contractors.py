from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db

router = APIRouter(
    prefix="/api/contractors",
    tags=["Contractors"]
)


@router.get("/")
def get_contractors(
    db: Session = Depends(get_db)
):
    contractors = (
        db.query(models.Contractor)
        .order_by(models.Contractor.created_at.desc())
        .all()
    )

    return contractors


@router.get("/{contractor_id}")
def get_contractor(
    contractor_id: int,
    db: Session = Depends(get_db)
):
    contractor = (
        db.query(models.Contractor)
        .filter(models.Contractor.id == contractor_id)
        .first()
    )

    if not contractor:
        raise HTTPException(
            status_code=404,
            detail="Contractor not found"
        )

    return contractor


@router.post("/")
def create_contractor(
    name: str,
    company_name: str,
    phone: str,
    email: str | None = None,
    specialization: str | None = None,
    area: str | None = None,
    rating: float = 0.0,
    db: Session = Depends(get_db)
):
    contractor = models.Contractor(
        name=name,
        company_name=company_name,
        phone=phone,
        email=email,
        specialization=specialization,
        area=area,
        rating=rating,
        completed_orders=0,
        status="Available",
        created_at=datetime.utcnow()
    )

    db.add(contractor)
    db.commit()
    db.refresh(contractor)

    return {
        "success": True,
        "message": "Contractor created successfully",
        "contractor": contractor
    }


@router.put("/{contractor_id}")
def update_contractor(
    contractor_id: int,
    phone: str | None = None,
    email: str | None = None,
    specialization: str | None = None,
    area: str | None = None,
    rating: float | None = None,
    status: str | None = None,
    db: Session = Depends(get_db)
):
    contractor = (
        db.query(models.Contractor)
        .filter(models.Contractor.id == contractor_id)
        .first()
    )

    if not contractor:
        raise HTTPException(
            status_code=404,
            detail="Contractor not found"
        )

    if phone is not None:
        contractor.phone = phone

    if email is not None:
        contractor.email = email

    if specialization is not None:
        contractor.specialization = specialization

    if area is not None:
        contractor.area = area

    if rating is not None:
        contractor.rating = rating

    if status is not None:
        contractor.status = status

    db.commit()
    db.refresh(contractor)

    return {
        "success": True,
        "message": "Contractor updated successfully",
        "contractor": contractor
    }