import logging
import time
import uuid

from fastapi import FastAPI, Request

from src.api.v1.endpoints import router as api_v1_router
from src.core.config import settings
from src.core.exceptions import AppError, app_exception_handler
from src.core.logging import setup_logging

# Initialize structured logging
setup_logging(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

# ... rest of the setup
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Register Global Exception Handler
app.add_exception_handler(AppError, app_exception_handler)

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log every incoming request and its processing time.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    logger.info(
        "Handled request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "latency_ms": round(process_time, 2),
            "request_id": request_id
        }
    )
    return response

# Include API V1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for monitoring, load balancers, and container orchestration.
    """
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    # Local development runner with hot-reloading
    # Bind to 127.0.0.1 for local development to avoid security warnings.
    # For Docker, 0.0.0.0 is used via the command in the Dockerfile.
    uvicorn.run(
        "src.main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=settings.DEBUG
    )
