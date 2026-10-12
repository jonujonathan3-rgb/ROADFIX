
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import models
from database import get_db
from auth import get_current_admin

router = APIRouter(prefix="/api/complaints", tags=["Complaint Photos"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_TYPES = {
    "image/jpeg": (".jpg", lambda b: b.startswith(b"\xff\xd8\xff")),
    "image/png": (".png", lambda b: b.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": (
        ".webp",
        lambda b: len(b) >= 12 and b[:4] == b"RIFF" and b[8:12] == b"WEBP",
    ),
}


def find_complaint(tracking_id: str, db: Session):
    complaint = (
        db.query(models.Complaint)
        .filter(models.Complaint.tracking_id == tracking_id)
        .first()
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


def photo_response(filename: str | None):
    if not filename:
        raise HTTPException(status_code=404, detail="Photo not available")

    safe_name = Path(filename).name
    path = UPLOAD_DIR / safe_name

    if not path.is_file():
        raise HTTPException(status_code=404, detail="Photo file not found")

    return FileResponse(path)


@router.post("/{tracking_id}/after-photo")
async def upload_after_photo(
    tracking_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_username: str = Depends(get_current_admin),
):
    complaint = find_complaint(tracking_id, db)

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Upload a JPEG, PNG, or WebP image.",
        )

    data = await file.read(MAX_IMAGE_SIZE + 1)
    if not data:
        raise HTTPException(status_code=400, detail="The image is empty.")
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Maximum image size is 5 MB.")

    extension, signature_check = ALLOWED_TYPES[file.content_type]
    if not signature_check(data):
        raise HTTPException(status_code=400, detail="Invalid image file.")

    filename = f"{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename
    destination.write_bytes(data)

    old_filename = complaint.after_photo_filename
    complaint.after_photo_filename = filename

    try:
        db.commit()
    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Could not save photo record.")

    if old_filename:
        old_path = UPLOAD_DIR / Path(old_filename).name
        if old_path != destination:
            old_path.unlink(missing_ok=True)

    return {
        "success": True,
        "message": "After-repair photo uploaded successfully.",
        "tracking_id": complaint.tracking_id,
        "photo_url": f"/api/complaints/{tracking_id}/after-photo",
        "uploaded_by": admin_username,
    }


@router.get("/{tracking_id}/photos")
def get_photo_urls(tracking_id: str, db: Session = Depends(get_db)):
    complaint = find_complaint(tracking_id, db)

    return {
        "tracking_id": complaint.tracking_id,
        "before_photo_url": (
            f"/api/complaints/{tracking_id}/before-photo"
            if complaint.photo_filename else None
        ),
        "after_photo_url": (
            f"/api/complaints/{tracking_id}/after-photo"
            if complaint.after_photo_filename else None
        ),
    }


@router.get("/{tracking_id}/before-photo")
def get_before_photo(tracking_id: str, db: Session = Depends(get_db)):
    complaint = find_complaint(tracking_id, db)
    return photo_response(complaint.photo_filename)


@router.get("/{tracking_id}/after-photo")
def get_after_photo(tracking_id: str, db: Session = Depends(get_db)):
    complaint = find_complaint(tracking_id, db)
    return photo_response(complaint.after_photo_filename)