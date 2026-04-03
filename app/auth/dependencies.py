from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.utils import decode_access_token
from app.models.user import User

# This scheme extracts the token from "Authorization: Bearer <token>"
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Dependency: extracts JWT from header, validates it, returns User.
    Use in any route: user = Depends(get_current_user)
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID.",
        )

    user = db.query(User).filter(
        User.id == user_id,
        User.is_active == True
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated.",
        )

    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Dependency: same as get_current_user but returns None instead of 401.
    Use for routes that work with or without auth.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = db.query(User).filter(
        User.id == user_id,
        User.is_active == True
    ).first()

    return user


def require_super_admin(user: User = Depends(get_current_user)):
    """Dependency: only super_admin can access."""
    if user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required.",
        )
    return user


def require_business_owner(user: User = Depends(get_current_user)):
    """Dependency: super_admin OR business_owner can access."""
    if user.role not in ("super_admin", "business_owner"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business owner access required.",
        )
    return user


def require_any_staff(user: User = Depends(get_current_user)):
    """Dependency: any authenticated active user can access."""
    return user
