from fastapi import APIRouter

from src.api.v1.endpoints import auth, data, results, websocket, alerts, optimization_ingestion
from src.core.config import settings

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(data.router, prefix="/data", tags=["data"])
# api_router.include_router(multi_asset_data.router, prefix="/multi-asset", tags=["multi-asset"])  # REMOVED: Focus on crypto only
# api_router.include_router(autonama_optimization.router, prefix="/autonama", tags=["autonama-optimization"])  # REMOVED: No longer needed
# api_router.include_router(optimization.router, prefix="/optimize", tags=["optimization"])  # REMOVED: No longer needed
api_router.include_router(results.router, prefix="/results", tags=["results"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(websocket.router, prefix="", tags=["websocket"])
api_router.include_router(optimization_ingestion.router, prefix="/optimization", tags=["optimization-ingestion"])

# Include Stripe billing endpoints only if a secret key is configured
try:
    if getattr(settings, "STRIPE_SECRET_KEY", ""):
        from src.api.v1.endpoints import billing
        api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
except Exception:
    # Skip billing if misconfigured or dependency missing
    pass

