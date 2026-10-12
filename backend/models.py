from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text
)

from database import Base



class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    # Tracking
    tracking_id = Column(String(30), unique=True, index=True, nullable=False)

    # Citizen details
    name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=False)

    # Problem details
    problem_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)

    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Rule-based assessment
    severity = Column(String(30), default="Medium")
    traffic_level = Column(String(30), default="Medium")
    school_zone = Column(Boolean, default=False)

    # Priority engine
    priority_score = Column(Integer, default=0)
    priority = Column(String(30), default="LOW")

    # Evidence
    photo_filename = Column(String(255), nullable=True)
    after_photo_filename = Column(String(255), nullable=True)

    # Workflow
    status = Column(String(50), default="Submitted")

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)

    # Road being inspected
    road_id = Column(Integer, nullable=False)

    # Inspector details
    inspector_name = Column(String(100), nullable=False)

    # Inspection information
    inspection_date = Column(DateTime, default=datetime.utcnow)

    condition = Column(String(50), nullable=False)

    risk_level = Column(String(30), nullable=False)

    findings = Column(Text, nullable=False)

    recommended_action = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)

    # References
    road_id = Column(Integer, nullable=False)
    complaint_id = Column(Integer, nullable=True)

    # Work order details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Priority
    priority = Column(String(30), default="MEDIUM")

    # Workflow
    status = Column(String(50), default="Pending")

    # Assignment
    contractor_name = Column(String(150), nullable=True)

    # Dates
    assigned_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

class Contractor(Base):
    __tablename__ = "contractors"

    id = Column(Integer, primary_key=True, index=True)

    # Contractor details
    name = Column(String(150), nullable=False)
    company_name = Column(String(150), nullable=False)
    phone = Column(String(15), nullable=False)
    email = Column(String(150), nullable=True)

    # Contractor specialization
    specialization = Column(String(150), nullable=True)

    # Location
    area = Column(String(150), nullable=True)

    # Performance
    rating = Column(Float, default=0.0)
    completed_orders = Column(Integer, default=0)

    # Availability
    status = Column(String(50), default="Available")

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)

    # Work order being verified
    work_order_id = Column(Integer, nullable=False)

    # Verification details
    verifier_name = Column(String(100), nullable=False)
    verification_date = Column(DateTime, default=datetime.utcnow)

    # Verification result
    result = Column(String(30), default="Pending")

    # Evidence and remarks
    remarks = Column(Text, nullable=True)
    photo_filename = Column(String(255), nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Related records
    complaint_id = Column(Integer, nullable=True)
    work_order_id = Column(Integer, nullable=True)

    # Audit information
    action = Column(String(100), nullable=False)
    performed_by = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

class RoadSign(Base):
    __tablename__ = "road_signs"

    id = Column(Integer, primary_key=True, index=True)

    # Sign details
    sign_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Location
    road_id = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Condition
    condition = Column(String(50), default="Good")

    # Maintenance
    status = Column(String(50), default="Active")
    replacement_required = Column(Boolean, default=False)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)