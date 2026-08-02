from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import Settings, settings
from app.core.errors import register_exception_handlers
from app.core.logger import logger
from app.domain.schemas.responses import HealthResponse, ReadinessResponse
from app.modules.coaching.router import router as coaching_router
from app.modules.event_detection.router import router as event_router
from app.modules.fleet.router import router as fleet_router
from app.modules.insurance.router import router as insurance_router
from app.modules.risk_fusion.router import router as risk_router
from app.modules.streaming.router import router as streaming_router
from app.modules.ai_alerts.router import router as ai_alerts_router
from app.integrations.carsky.client import CarSkyClient
from app.integrations.carsky.service import CarSkyPublisher


EXPECTED_TRIP_IDS = frozenset(f"T{index:02d}d" for index in range(1, 11))
REST_ROUTERS = (
    ai_alerts_router,
    fleet_router,
    event_router,
    risk_router,
    insurance_router,
    coaching_router,
)


def dataset_is_readable(path: Path) -> bool:
    return path.is_dir() and os.access(path, os.R_OK)


def readiness_snapshot(app: FastAPI) -> tuple[bool, ReadinessResponse]:
    app_settings: Settings = app.state.settings
    trip_cache: dict[str, Any] = getattr(app.state, "trip_cache", {})
    cached_ids = set(trip_cache)
    missing_trip_ids = sorted(EXPECTED_TRIP_IDS - cached_ids)
    dataset_ready = dataset_is_readable(app_settings.DATASET_DIR)
    cache_ready = not missing_trip_ids
    external_ai_ready = app_settings.external_ai_configured
    ready = dataset_ready and cache_ready and external_ai_ready

    response = ReadinessResponse(
        status="ready" if ready else "not_ready",
        dataset_ready=dataset_ready,
        cached_trips=len(EXPECTED_TRIP_IDS & cached_ids),
        expected_trips=len(EXPECTED_TRIP_IDS),
        external_ai_ready=external_ai_ready,
        details={
            "dataset_dir": str(app_settings.DATASET_DIR),
            "cache_ready": cache_ready,
            "missing_trip_ids": missing_trip_ids,
            "ai_source_mode": app_settings.AI_SOURCE_MODE,
        },
    )
    return ready, response


def create_app(app_settings: Settings | None = None) -> FastAPI:
    configured_settings = app_settings or settings

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        started_at = time.perf_counter()
        application.state.trip_cache = getattr(application.state, "trip_cache", {})
        application.state.settings = configured_settings
        application.state.started_at = time.time()
        application.state.carsky_publisher = None

        if (
            configured_settings.CARSKY_ENABLED
            and configured_settings.CARSKY_MODE == "external"
            and configured_settings.CARSKY_BASE_URL
            and configured_settings.CARSKY_API_KEY
            and configured_settings.CARSKY_ROOM_ID
            and configured_settings.CARSKY_NODE_KEY
        ):
            cars_client = CarSkyClient(
                base_url=configured_settings.CARSKY_BASE_URL,
                api_key=configured_settings.CARSKY_API_KEY,
                room_id=configured_settings.CARSKY_ROOM_ID,
                node_key=configured_settings.CARSKY_NODE_KEY,
                auth_mode=configured_settings.CARSKY_AUTH_MODE,
                timeout_sec=configured_settings.CARSKY_TIMEOUT_SEC,
                max_retries=configured_settings.CARSKY_MAX_RETRIES,
            )
            cars_publisher = CarSkyPublisher(
                cars_client,
                queue_size=configured_settings.CARSKY_QUEUE_SIZE,
            )
            await cars_publisher.start()
            application.state.carsky_publisher = cars_publisher

        dataset_dir = configured_settings.DATASET_DIR
        if dataset_is_readable(dataset_dir) and not getattr(
            application.state, "static_mounted", False
        ):
            application.mount(
                "/static",
                StaticFiles(directory=str(dataset_dir)),
                name="static",
            )
            application.state.static_mounted = True
            logger.info("Mounted static dataset directory path=%s", dataset_dir)

        logger.info(
            "Backend startup complete env=%s source=%s fps=%s duration_ms=%.2f",
            configured_settings.APP_ENV,
            configured_settings.AI_SOURCE_MODE,
            configured_settings.STREAM_FPS,
            (time.perf_counter() - started_at) * 1000,
        )
        yield
        cars_publisher = getattr(application.state, "carsky_publisher", None)
        if cars_publisher is not None:
            await cars_publisher.stop()
        logger.info("Backend shutdown complete")

    application = FastAPI(
        title=configured_settings.PROJECT_NAME,
        description="DMS Driver & Fleet Risk Intelligence Backend",
        version=configured_settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    application.state.settings = configured_settings
    application.state.trip_cache = {}

    application.add_middleware(
        CORSMiddleware,
        allow_origins=configured_settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    register_exception_handlers(application)

    @application.get("/", tags=["Health Check"])
    async def root() -> dict[str, Any]:
        return {
            "project": configured_settings.PROJECT_NAME,
            "status": "online",
            "fps_stream": configured_settings.STREAM_FPS,
            "docs": "/docs",
        }

    @application.get("/health", response_model=HealthResponse, tags=["Health Check"])
    async def health() -> HealthResponse:
        return HealthResponse(
            service=configured_settings.SERVICE_NAME,
            version=configured_settings.VERSION,
            stream_fps=configured_settings.STREAM_FPS,
        )

    @application.get(
        "/ready",
        response_model=ReadinessResponse,
        responses={503: {"model": ReadinessResponse}},
        tags=["Health Check"],
    )
    async def ready(request: Request) -> ReadinessResponse | JSONResponse:
        is_ready, response = readiness_snapshot(request.app)
        if not is_ready:
            return JSONResponse(status_code=503, content=response.model_dump(mode="json"))
        return response

    for feature_router in REST_ROUTERS:
        application.include_router(
            feature_router,
            prefix=configured_settings.API_V1_PREFIX,
        )
        application.include_router(
            feature_router,
            prefix=configured_settings.LEGACY_API_PREFIX,
            deprecated=True,
        )

    application.include_router(streaming_router)
    return application


app = create_app()
