from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
import models
from routes.complaints import router as complaints_router
from routes.roads import router as roads_router
from routes.inspections import router as inspections_router
from routes.work_orders import router as work_orders_router
from routes.contractors import router as contractors_router
from routes.verification import router as verification_router
from routes.audits import router as audits_router
from routes.signs import router as signs_router
from routes.auth_routes import router as auth_router
from routes.photos import router as photos_router
# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="ROADFIX API",
    description="Digital Road Safety and Maintenance Management Platform",
    version="1.0.0"
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register complaint routes
app.include_router(complaints_router)
app.include_router(roads_router)
app.include_router(inspections_router)
app.include_router(work_orders_router)
app.include_router(contractors_router)
app.include_router(verification_router)
app.include_router(audits_router)
app.include_router(signs_router)
app.include_router(auth_router)
app.include_router(photos_router)

@app.get("/")
def root():
    return {
        "project": "ROADFIX",
        "message": "ROADFIX backend is running",
        "status": "online"
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "database": "connected"
    }