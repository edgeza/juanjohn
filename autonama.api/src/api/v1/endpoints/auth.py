"""
Authentication and User Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import jwt
import logging

from src.core.database import get_db
from src.models.asset_models import User, Alert

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    has_access: bool
    is_admin: bool

class AlertCreate(BaseModel):
    symbol: str
    condition: str  # "above", "below", "crosses_above", "crosses_below"
    price: float
    timeframe: str = "1h"
    enabled: bool = True

class AlertResponse(BaseModel):
    id: int
    symbol: str
    condition: str
    price: float
    timeframe: str
    enabled: bool
    triggered: bool
    triggered_at: Optional[datetime]
    created_at: datetime

class AlertUpdate(BaseModel):
    enabled: Optional[bool] = None
    price: Optional[float] = None
    condition: Optional[str] = None

# JWT Configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_admin(
    username: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if not getattr(user, "is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required",
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin verification failed"
        )

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == user.username) | (User.email == user.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
        
        # Create new user (in production, hash the password)
        db_user = User(
            username=user.username,
            email=user.email,
            password=user.password  # Should be hashed in production
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return UserResponse(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            created_at=db_user.created_at,
            has_access=db_user.has_access,
            is_admin=getattr(db_user, "is_admin", False),
        )
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login")
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    try:
        # Find user
        user = db.query(User).filter(User.username == user_credentials.username).first()
        
        if not user or user.password != user_credentials.password:  # Should verify hashed password
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                created_at=user.created_at,
                has_access=user.has_access,
                is_admin=getattr(user, "is_admin", False),
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(username: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Get current user information"""
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if not user.has_access:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Active subscription required"
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            has_access=user.has_access,
            is_admin=getattr(user, "is_admin", False),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@router.post("/users/grant-access")
async def grant_access(
    data: dict,
    db: Session = Depends(get_db),
):
    """Grant manual access to a user. Secured via ADMIN_ACCESS_TOKEN env var checked in data['admin_token']
    This is a minimal admin endpoint for manual granting without full RBAC.
    """
    try:
        from src.core.config import settings
        admin_token = data.get("admin_token")
        username = data.get("username")
        if not admin_token or admin_token != getattr(settings, "ADMIN_ACCESS_TOKEN", None):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        if not username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username is required")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.has_access = True
        db.commit()
        return {"message": "Access granted", "username": username}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Grant access error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to grant access")

@router.post("/users/revoke-access")
async def revoke_access(
    data: dict,
    db: Session = Depends(get_db),
):
    """Revoke manual access from a user.
    Requires ADMIN_ACCESS_TOKEN via data['admin_token'].
    """
    try:
        from src.core.config import settings
        admin_token = data.get("admin_token")
        username = data.get("username")
        if not admin_token or admin_token != getattr(settings, "ADMIN_ACCESS_TOKEN", None):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        if not username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username is required")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.has_access = False
        db.commit()
        return {"message": "Access revoked", "username": username}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke access error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to revoke access")

@router.post("/users/make-admin")
async def make_admin(
    data: dict,
    db: Session = Depends(get_db),
):
    """Promote a user to admin. Secured via ADMIN_ACCESS_TOKEN."""
    try:
        from src.core.config import settings
        admin_token = data.get("admin_token")
        username = data.get("username")
        if not admin_token or admin_token != getattr(settings, "ADMIN_ACCESS_TOKEN", None):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        if not username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username is required")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.is_admin = True
        user.has_access = True
        db.commit()
        return {"message": "User promoted to admin", "username": username}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Make admin error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to make admin")

class UserAdminListItem(BaseModel):
    id: int
    username: str
    email: str
    has_access: bool
    is_admin: bool
    created_at: datetime

@router.get("/admin/users", response_model=List[UserAdminListItem])
async def admin_list_users(
    _: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).all()
    return [
        UserAdminListItem(
            id=u.id,
            username=u.username,
            email=u.email,
            has_access=getattr(u, "has_access", False),
            is_admin=getattr(u, "is_admin", False),
            created_at=u.created_at,
        )
        for u in users
    ]

@router.post("/admin/users/{username}/grant")
async def admin_grant_user_access(
    username: str,
    _: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.has_access = True
    db.commit()
    return {"message": "Access granted", "username": username}

@router.post("/admin/users/{username}/revoke")
async def admin_revoke_user_access(
    username: str,
    _: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.has_access = False
    db.commit()
    return {"message": "Access revoked", "username": username}

# Alert endpoints
@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create a new price alert"""
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if not user.has_access:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Active subscription required"
            )
        
        # Validate condition
        valid_conditions = ["above", "below", "crosses_above", "crosses_below"]
        if alert.condition not in valid_conditions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid condition. Must be one of: {valid_conditions}"
            )
        
        # Create alert
        db_alert = Alert(
            user_id=user.id,
            symbol=alert.symbol,
            condition=alert.condition,
            price=alert.price,
            timeframe=alert.timeframe,
            enabled=alert.enabled
        )
        
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        
        return AlertResponse(
            id=db_alert.id,
            symbol=db_alert.symbol,
            condition=db_alert.condition,
            price=db_alert.price,
            timeframe=db_alert.timeframe,
            enabled=db_alert.enabled,
            triggered=db_alert.triggered,
            triggered_at=db_alert.triggered_at,
            created_at=db_alert.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create alert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert"
        )

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all alerts for the current user"""
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if not user.has_access:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Active subscription required"
            )
        
        alerts = db.query(Alert).filter(Alert.user_id == user.id).all()
        
        return [
            AlertResponse(
                id=alert.id,
                symbol=alert.symbol,
                condition=alert.condition,
                price=alert.price,
                timeframe=alert.timeframe,
                enabled=alert.enabled,
                triggered=alert.triggered,
                triggered_at=alert.triggered_at,
                created_at=alert.created_at
            )
            for alert in alerts
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get alerts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alerts"
        )

@router.put("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update an existing alert"""
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if not user.has_access:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Active subscription required"
            )
        
        # Get alert and verify ownership
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.user_id == user.id
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Update fields
        if alert_update.enabled is not None:
            alert.enabled = alert_update.enabled
        if alert_update.price is not None:
            alert.price = alert_update.price
        if alert_update.condition is not None:
            alert.condition = alert_update.condition
        
        db.commit()
        db.refresh(alert)
        
        return AlertResponse(
            id=alert.id,
            symbol=alert.symbol,
            condition=alert.condition,
            price=alert.price,
            timeframe=alert.timeframe,
            enabled=alert.enabled,
            triggered=alert.triggered,
            triggered_at=alert.triggered_at,
            created_at=alert.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update alert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update alert"
        )

@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete an alert"""
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get alert and verify ownership
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.user_id == user.id
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        db.delete(alert)
        db.commit()
        
        return {"message": "Alert deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete alert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert"
        )

@router.get("/alerts/check")
async def check_alerts(
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Check for triggered alerts (for background processing)"""
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get active alerts
        active_alerts = db.query(Alert).filter(
            Alert.user_id == user.id,
            Alert.enabled == True,
            Alert.triggered == False
        ).all()
        
        triggered_alerts = []
        
        # In a real implementation, you would check current prices against alerts
        # For now, return empty list
        return {
            "triggered_alerts": triggered_alerts,
            "total_alerts": len(active_alerts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Check alerts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check alerts"
        )
