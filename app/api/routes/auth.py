import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models.user import User, UserRole
from app.auth.utils import hash_password, verify_password, create_access_token
from app.auth.dependencies import get_current_user, require_super_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Authentication"])


# ============================================================
#  REQUEST / RESPONSE MODELS
# ============================================================

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None
    business_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str
    business_id: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ============================================================
#  ROUTES
# ============================================================

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new business owner account."""

    # Validate email format (basic check)
    if "@" not in req.email or "." not in req.email:
        raise HTTPException(status_code=400, detail="Invalid email format.")

    # Validate password length
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    # Check if email already exists
    existing = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    # Check if phone already exists
    if req.phone:
        existing_phone = db.query(User).filter(User.phone == req.phone.strip()).first()
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone number already registered.")

    # Create user (always business_owner via public registration)
    user = User(
        email=req.email.lower().strip(),
        password_hash=hash_password(req.password),
        full_name=req.full_name.strip(),
        phone=req.phone.strip() if req.phone else None,
        role=UserRole.BUSINESS_OWNER.value,
        business_id=req.business_id,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("New user registered: " + user.email + " (role=" + user.role + ")")

    token = create_access_token({"sub": user.id, "role": user.role})

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password. Returns JWT token."""

    user = db.query(User).filter(User.email == req.email.lower().strip()).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account has been deactivated.")

    logger.info("User logged in: " + user.email)

    token = create_access_token({"sub": user.id, "role": user.role})

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    """Get current logged-in user profile."""
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
def update_me(
    req: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user profile (name, phone)."""
    if req.full_name is not None:
        user.full_name = req.full_name.strip()
    if req.phone is not None:
        # Check phone uniqueness
        if req.phone.strip():
            existing = db.query(User).filter(
                User.phone == req.phone.strip(),
                User.id != user.id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Phone number already in use.")
        user.phone = req.phone.strip() if req.phone.strip() else None

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change password for current user."""
    if not verify_password(req.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")

    user.password_hash = hash_password(req.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Password changed successfully."}


# ============================================================
#  ADMIN-ONLY ROUTES
# ============================================================

@router.get("/users", response_model=List[UserResponse])
def list_all_users(
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """List all users (super_admin only)."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [UserResponse.model_validate(u) for u in users]


@router.put("/users/{user_id}/role")
def change_user_role(
    user_id: str,
    role: str,
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Change a user's role (super_admin only)."""
    valid_roles = [r.value for r in UserRole]
    if role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. Must be one of: " + ", ".join(valid_roles)
        )

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    target.role = role
    target.updated_at = datetime.utcnow()
    db.commit()

    logger.info("Admin " + admin.email + " changed role of " + target.email + " to " + role)
    return {"message": "Role updated to " + role}


@router.put("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: str,
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Deactivate a user account (super_admin only)."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself.")

    target.is_active = False
    target.updated_at = datetime.utcnow()
    db.commit()

    logger.info("Admin " + admin.email + " deactivated user " + target.email)
    return {"message": "User " + target.email + " deactivated."}


@router.put("/users/{user_id}/activate")
def activate_user(
    user_id: str,
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Reactivate a user account (super_admin only)."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    target.is_active = True
    target.updated_at = datetime.utcnow()
    db.commit()

    logger.info("Admin " + admin.email + " activated user " + target.email)
    return {"message": "User " + target.email + " activated."}
