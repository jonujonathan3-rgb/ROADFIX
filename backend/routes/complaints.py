from datetime import datetime
import random

from sqlalchemy.orm import Session
from auth import get_current_admin
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Body
from pathlib import Path
from uuid import uuid4
from fastapi.responses import FileResponse
from database import get_db
import models
router = APIRouter(
    prefix="/api/complaints",
    tags=["Complaints"]
)
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_PHOTO_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def save_uploaded_photo(photo: UploadFile) -> str:
    if photo.content_type not in ALLOWED_PHOTO_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Please upload a JPEG, PNG, or WebP image."
        )

    contents = await photo.read(MAX_PHOTO_SIZE + 1)

    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded photo is empty.")

    if len(contents) > MAX_PHOTO_SIZE:
        raise HTTPException(status_code=413, detail="Photo must be 5 MB or smaller.")

    # Check that the file contents match a supported image format.
    valid_image = (
        photo.content_type == "image/jpeg"
        and contents.startswith(b"\xff\xd8\xff")
    ) or (
        photo.content_type == "image/png"
        and contents.startswith(b"\x89PNG\r\n\x1a\n")
    ) or (
        photo.content_type == "image/webp"
        and contents.startswith(b"RIFF")
        and contents[8:12] == b"WEBP"
    )

    if not valid_image:
        raise HTTPException(
            status_code=400,
            detail="The file contents do not match the selected image type."
        )

    filename = f"{uuid4().hex}{ALLOWED_PHOTO_TYPES[photo.content_type]}"
    destination = UPLOAD_DIR / filename
    destination.write_bytes(contents)

    return filename

def generate_tracking_id():
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = random.randint(1000, 9999)
    return f"RDF-{date_part}-{random_part}"


def calculate_priority(
    problem_type: str,
    severity: str,
    traffic_level: str,
    school_zone: bool
):
    score = 0

    severity_points = {
        "Low": 10,
        "Medium": 25,
        "High": 40,
        "Critical": 50
    }

    traffic_points = {
        "Low": 5,
        "Medium": 10,
        "High": 20
    }

    problem_points = {
        "Pothole": 20,
        "Road Damage": 25,
        "Landslide/Debris": 35,
        "Bridge/Culvert": 40,
        "Drainage": 15,
        "Missing Sign": 20,
        "Widening": 10,
        "Other": 10
    }

    score += severity_points.get(severity, 10)
    score += traffic_points.get(traffic_level, 5)
    score += problem_points.get(problem_type, 10)

    if school_zone:
        score += 20

    if score >= 80:
        priority = "CRITICAL"
    elif score >= 60:
        priority = "HIGH"
    elif score >= 35:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return score, priority


@router.post("/")
async def create_complaint(
    name: str = Form(...),
    phone: str = Form(...),
    problem_type: str = Form(...),
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    severity: str = Form("Medium"),
    traffic_level: str = Form("Medium"),
    school_zone: bool = Form(False),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    tracking_id = generate_tracking_id()

    score, priority = calculate_priority(
        problem_type,
        severity,
        traffic_level,
        school_zone
    )

    photo_filename = None

    if photo and photo.filename:
        photo_filename = await save_uploaded_photo(photo)
    complaint = models.Complaint(
        tracking_id=tracking_id,
        name=name,
        phone=phone,
        problem_type=problem_type,
        description=description,
        latitude=latitude,
        longitude=longitude,
        severity=severity,
        traffic_level=traffic_level,
        school_zone=school_zone,
        priority_score=score,
        priority=priority,
        photo_filename=photo_filename,
        status="Submitted",
        created_at=datetime.utcnow()
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return {
        "success": True,
        "message": "Road complaint submitted successfully",
        "tracking_id": tracking_id,
        "priority_score": score,
        "priority": priority,
        "status": "Submitted"
    }



@router.get("/")
def get_complaints(
    db: Session = Depends(get_db),
    admin_username: str = Depends(get_current_admin)
):
    complaints = (
        db.query(models.Complaint)
        .order_by(models.Complaint.created_at.desc())
        .all()
    )

    return complaints

@router.get("/{tracking_id}")
def get_complaint(
    tracking_id: str,
    db: Session = Depends(get_db)
):
    complaint = (
        db.query(models.Complaint)
        .filter(models.Complaint.tracking_id == tracking_id)
        .first()
    )

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return complaint

@router.patch("/{tracking_id}/status")
def update_complaint_status(
    tracking_id: str,
    status: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    admin_username: str = Depends(get_current_admin)
):
    allowed_statuses = {
        "Submitted",
        "Assigned",
        "In Progress",
        "Completed"
    }

    # Normalize the status received from the dashboard.
    normalized_status = str(status).strip().lower().replace("_", " ")

    status_lookup = {
        item.lower(): item for item in allowed_statuses
    }

    if normalized_status not in status_lookup:
        raise HTTPException(
            status_code=400,
            detail="Status must be Submitted, Assigned, In Progress, or Completed."
        )

    new_status = status_lookup[normalized_status]

    complaint = (
        db.query(models.Complaint)
        .filter(models.Complaint.tracking_id == tracking_id)
        .first()
    )

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found."
        )

    current_time = datetime.utcnow()

    # Update the linked work order when one exists.
    # A work order or approved verification is NOT required
    # to update the complaint status.
    work_order = (
        db.query(models.WorkOrder)
        .filter(models.WorkOrder.complaint_id == complaint.id)
        .first()
    )

    if work_order:
        if new_status == "Assigned":
            work_order.status = "Assigned"

            if work_order.assigned_at is None:
                work_order.assigned_at = current_time

        elif new_status == "In Progress":
            work_order.status = "In Progress"

            if work_order.started_at is None:
                work_order.started_at = current_time

        elif new_status == "Completed":
            work_order.status = "Completed"

            if hasattr(work_order, "completed_at"):
                work_order.completed_at = current_time

        elif new_status == "Submitted":
            # Update the complaint only; do not reset a work order.
            pass

    # Update the citizen-facing complaint status.
    complaint.status = new_status

    try:
        db.commit()
        db.refresh(complaint)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update complaint status."
        )

    return {
        "success": True,
        "message": "Complaint status updated successfully.",
        "tracking_id": complaint.tracking_id,
        "status": complaint.status
    }
@router.post("/{tracking_id}/after-photo")
async def upload_after_photo(
    tracking_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_username: str = Depends(get_current_admin),
):
    complaint = (
        db.query(models.Complaint)
        .filter(models.Complaint.tracking_id == tracking_id)
        .first()
    )

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found.")

    new_filename = await save_uploaded_photo(file)
    old_filename = complaint.after_photo_filename

    complaint.after_photo_filename = new_filename

    try:
        db.commit()
    except Exception:
        db.rollback()
        (UPLOAD_DIR / new_filename).unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Could not save the after-repair photo."
        )

    if old_filename:
        (UPLOAD_DIR / old_filename).unlink(missing_ok=True)

    return {
        "success": True,
        "message": "After-repair photo uploaded successfully.",
        "tracking_id": tracking_id,
    }
@router.get("/{tracking_id}/before-photo")
def get_before_photo(
    tracking_id: str,
    db: Session = Depends(get_db),
):
    complaint = (
        db.query(models.Complaint)
        .filter(models.Complaint.tracking_id == tracking_id)
        .first()
    )

    if not complaint or not complaint.photo_filename:
        raise HTTPException(status_code=404, detail="Before photo not found.")

    photo_path = UPLOAD_DIR / complaint.photo_filename

    if not photo_path.is_file():
        raise HTTPException(status_code=404, detail="Before photo file not found.")

    return FileResponse(photo_path)


@router.get("/{tracking_id}/after-photo")
def get_after_photo(
    tracking_id: str,
    db: Session = Depends(get_db),
):
    complaint = (
        db.query(models.Complaint)
        .filter(models.Complaint.tracking_id == tracking_id)
        .first()
    )

    if not complaint or not complaint.after_photo_filename:
        raise HTTPException(status_code=404, detail="After-repair photo not found.")

    photo_path = UPLOAD_DIR / complaint.after_photo_filename

    if not photo_path.is_file():
        raise HTTPException(status_code=404, detail="After-repair photo file not found.")

    return FileResponse(photo_path)