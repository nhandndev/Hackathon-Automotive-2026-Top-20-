from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.core.config import settings
from app.core.logger import logger

# Import Module Routers
from app.modules.streaming.router import router as streaming_router
from app.modules.fleet.router import router as fleet_router
from app.modules.event_detection.router import router as event_router
from app.modules.risk_fusion.router import router as risk_router
from app.modules.insurance.router import router as insurance_router
from app.modules.coaching.router import router as coaching_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FPTU DMS Vision Connected Car Driver & Fleet Risk Intelligence Backend Core Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount Static Files for Camera Images (KITTI & Driver Cabin)
if os.path.exists(settings.DATASET_DIR):
    app.mount("/static", StaticFiles(directory=settings.DATASET_DIR), name="static")
    logger.info(f"Mounted static image directory from: {settings.DATASET_DIR}")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Module Routers
app.include_router(streaming_router)
app.include_router(fleet_router)
app.include_router(event_router)
app.include_router(risk_router)
app.include_router(insurance_router)
app.include_router(coaching_router)

@app.get("/", tags=["Health Check"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "fps_stream": settings.STREAM_FPS,
        "docs": "/docs"
    }

logger.info("FastAPI DMS Backend initialized successfully.")
