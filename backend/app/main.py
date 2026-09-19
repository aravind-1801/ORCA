import os
import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.utils.logging import logger, request_id_ctx
from backend.app.db.session import init_db
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.marine import router as marine_router
from backend.app.api.routes.orca import router as orca_router
from backend.app.api.routes.voice import router as voice_router
from backend.app.api.routes.profile import router as profile_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"Database table initialization notice: {e}")
    try:
        from backend.app.rag.startup import init_rag
        init_rag()
    except Exception as rag_err:
        logger.warning(f"RAG startup notice: {rag_err}")
    logger.info(f"ORCA Backend started successfully in {settings.APP_ENV} mode (Demo={settings.DEMO_MODE}).")
    yield
    # Shutdown
    logger.info("ORCA Backend shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Marine EcOsystem Reasoning with Collaborative Agents (ORCA) API & Multi-Agent Orchestrator",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID and Access Logging Middleware
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_ctx.set(req_id)
    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = int((time.time() - start_time) * 1000)
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time-Ms"] = str(process_time)
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({process_time}ms)"
        )
        return response
    except Exception as exc:
        process_time = int((time.time() - start_time) * 1000)
        logger.error(f"Unhandled Exception for {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected marine data service error occurred.",
                    "request_id": req_id,
                }
            },
            headers={"X-Request-ID": req_id},
        )
    finally:
        request_id_ctx.reset(token)


from backend.app.api.routes.location import router as location_router
from backend.app.api.routes.standard_api import router as standard_router

# Direct root health endpoint (/health)
app.include_router(health_router)

# Register API routers under both /api and /api/v1 for complete compatibility
for prefix in ["/api", "/api/v1"]:
    app.include_router(health_router, prefix=prefix)
    app.include_router(profile_router, prefix=prefix)
    app.include_router(location_router, prefix=prefix)
    app.include_router(marine_router, prefix=prefix)
    app.include_router(orca_router, prefix=prefix)
    app.include_router(voice_router, prefix=prefix)
    app.include_router(standard_router, prefix=prefix)


# Frontend runtime configuration endpoint
@app.get("/api/config", tags=["Config"], summary="Frontend runtime configuration")
@app.get("/api/v1/config", tags=["Config"], summary="Frontend runtime configuration")
async def get_frontend_config():
    """Returns non-sensitive configuration for the frontend, including the Google Maps API key."""
    return {
        "google_maps_key": settings.get_effective_maps_key(),
        "demo_mode": settings.DEMO_MODE,
        "default_lat": settings.DEFAULT_LATITUDE,
        "default_lon": settings.DEFAULT_LONGITUDE,
        "default_location": settings.DEFAULT_LOCATION_NAME,
        "default_harbor": settings.DEFAULT_HARBOR,
    }

# Resolve frontend directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
if not os.path.isdir(frontend_dir):
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../frontend"))

from fastapi.responses import FileResponse

@app.get("/", include_in_schema=False)
async def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"status": "ok", "app": settings.APP_NAME})

if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info(f"Mounted frontend static files from: {frontend_dir}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
