from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
from contextlib import asynccontextmanager

from src.core.config import settings
from src.core.database import init_db
from src.core.logging import setup_logging, get_logger
from src.middleware.logging import LoggingMiddleware
from src.api.v1.api import api_router
from src.core.database import SessionLocal
from src.models.asset_models import User

# Setup logging first
setup_logging()
logger = get_logger("autonama.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Autonama API...", extra={"extra_fields": {"event": "startup"}})
    try:
        await init_db()
        logger.info("Database initialized successfully", extra={"extra_fields": {"event": "db_init"}})
        # Seed default admin if configured
        try:
            from src.core.config import settings
            if settings.DEFAULT_ADMIN_USERNAME and settings.DEFAULT_ADMIN_PASSWORD:
                db = SessionLocal()
                try:
                    existing = db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME).first()
                    if not existing:
                        admin = User(
                            username=settings.DEFAULT_ADMIN_USERNAME,
                            email=(settings.DEFAULT_ADMIN_EMAIL or f"{settings.DEFAULT_ADMIN_USERNAME}@example.com"),
                            password=settings.DEFAULT_ADMIN_PASSWORD,
                            is_admin=True,
                            has_access=True,
                        )
                        db.add(admin)
                        db.commit()
                        logger.info("Default admin user created", extra={"extra_fields": {"username": settings.DEFAULT_ADMIN_USERNAME}})
                finally:
                    db.close()
        except Exception as se:
            logger.error(f"Failed to seed default admin: {se}")
        
        # Start WebSocket broadcasting service
        # from src.services.websocket_broadcaster import start_websocket_broadcasting
        # import asyncio
        
        # Start broadcasting in background
        # asyncio.create_task(start_websocket_broadcasting())
        # logger.info("WebSocket broadcasting service started", extra={"extra_fields": {"event": "websocket_init"}})
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}", extra={"extra_fields": {"event": "init_error"}}, exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Autonama API...", extra={"extra_fields": {"event": "shutdown"}})
    try:
        # from src.services.websocket_broadcaster import stop_websocket_broadcasting
        # await stop_websocket_broadcasting()
        # logger.info("WebSocket broadcasting service stopped", extra={"extra_fields": {"event": "websocket_shutdown"}})
        pass
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", extra={"extra_fields": {"event": "shutdown_error"}})


app = FastAPI(
    title="Autonama API",
    description="FastAPI backend for Autonama Dashboard",
    version="1.0.0",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add logging middleware first
app.add_middleware(LoggingMiddleware)

# Add CORS middleware with more permissive settings for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

app.include_router(api_router, prefix="/api" + settings.API_V1_STR)


@app.get("/")
async def root():
    logger.info("Root endpoint accessed", extra={"extra_fields": {"endpoint": "/", "action": "root_access"}})
    return {"message": "Autonama API v1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed", extra={"extra_fields": {"endpoint": "/health", "action": "health_check"}})
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    logger.info("Starting Autonama API server", extra={"extra_fields": {"host": "0.0.0.0", "port": 8000}})
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
