from pydantic import BaseModel
from typing import Optional


class RoadBase(BaseModel):
    road_name: str
    road_code: str
    area: str
    latitude: float
    longitude: float
    road_type: str = "Urban"
    condition: str = "Good"
    risk_level: str = "LOW"
    traffic_level: str = "Medium"


class RoadCreate(RoadBase):
    pass


class RoadUpdate(BaseModel):
    condition: Optional[str] = None
    risk_level: Optional[str] = None
    traffic_level: Optional[str] = None
    status: Optional[str] = None


class RoadResponse(RoadBase):
    id: int
    status: str

    class Config:
        from_attributes = True