import logging
import os
import secrets
from datetime import datetime, timedelta
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


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ============================================================
#  EMAIL HELPER — RESEND
# ============================================================

def send_reset_email(to_email: str, reset_token: str, full_name: str):
    try:
        import resend

        api_key = os.getenv("RESEND_API_KEY", "")
        logger.info("Resend API key present: " + str(bool(api_key)))
        logger.info("Resend API key starts with: " + api_key[:6] if api_key else "EMPTY")

        if not api_key:
            logger.error("RESEND_API_KEY is not set in environment")
            return False

        resend.api_key = api_key

        frontend_url = os.getenv("FRONTEND_URL", "https://raseel-frontend-0.vercel.app")
        reset_url = frontend_url + "/reset-password?token=" + reset_token

        html_content = """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 30px;">
    <h1 style="color: white; margin: 0; font-size: 28px;">Raseel رسيل</h1>
    <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0;">AI WhatsApp Automation</p>
  </div>

  <h2 style="color: #1f2937;">Hello """ + full_name + """,</h2>

  <p style="color: #4b5563; font-size: 16px;">
    You requested to reset your Raseel password. Click the button below:
  </p>

  <div style="text-align: center; margin: 30px 0;">
    <a href=" """ + reset_url + """ "
       style="background: #4f46e5; color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-size: 16px; font-weight: bold; display: inline-block;">
      Reset My Password
    </a>
  </div>

  <p style="color: #6b7280; font-size: 14px;">
    This link expires in <strong>1 hour</strong>.
  </p>

  <p style="color: #6b7280; font-size: 14px;">
    If you did not request this, ignore this email.
  </p>

  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

  <p style="color: #9ca3af; font-size: 12px; text-align: center;">
    Raseel Platform — Built in Dammam, Saudi Arabia 🇸🇦<br>
    رسيل — منصة الأتمتة الذكية للأعمال السعودية
  </p>
</body>
</html>
"""

        text_content = (
            "Hello " + full_name + ",\n\n"
            "You requested to reset your Raseel password.\n\n"
            "Click the link below to reset your password:\n"
            + reset_url + "\n\n"
            "This link expires in 1 hour.\n\n"
            "If you did not request this, ignore this email.\n\n"
            "Raseel Platform\n"
            "رسيل — منصة الأتمتة الذكية"
        )

        params = {
            "from": "Raseel Platform <onboarding@resend.dev>",
            "to": [to_email],
            "subject": "Raseel — Reset Your Password",
            "html": html_content,
            "text": text_content,
        }

        result = resend.Emails.send(params)
        logger.info("Resend result: " + str(result))
        logger.info("Reset email sent via Resend to: " + to_email)
        return True

    except Exception as e:
        logger.error("Resend email failed: " + str(e))
        return False


# ============================================================
#  ROUTES
# ============================================================

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new business owner account."""

    if "@" not in req.email or "." not in req.email:
        raise HTTPException(status_code=400, detail="Invalid email format.")

    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    existing = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    if req.phone:
        existing_phone = db.query(User).filter(User.phone == req.phone.strip()).first()
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone number already registered.")

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

    logger.info("New user registered: " + user.email)

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
    """Update current user profile."""
    if req.full_name is not None:
        user.full_name = req.full_name.strip()
    if req.phone is not None:
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


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset email via Resend."""

    user = db.query(User).filter(User.email == req.email.lower().strip()).first()

    if not user:
        return {"message": "If this email exists, a reset link has been sent."}

    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    user.reset_token = reset_token
    user.reset_token_expires = expires_at
    db.commit()

    email_sent = send_reset_email(user.email, reset_token, user.full_name)
    logger.info("Email send result: " + str(email_sent))

    return {"message": "If this email exists, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token stored in database."""

    user = db.query(User).filter(User.reset_token == req.token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    if not user.reset_token_expires or datetime.utcnow() > user.reset_token_expires:
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        raise HTTPException(status_code=400, detail="Reset token has expired.")

    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    user.password_hash = hash_password(req.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    user.updated_at = datetime.utcnow()
    db.commit()

    logger.info("Password reset successful for: " + user.email)

    return {"message": "Password reset successful. You can now login."}


# ============================================================
#  DEBUG ROUTE — REMOVE AFTER TESTING
# ============================================================

@router.get("/test-resend")
def test_resend():
    """Test Resend API key and send a test email."""
    try:
        import resend

        api_key = os.getenv("RESEND_API_KEY", "")
        frontend_url = os.getenv("FRONTEND_URL", "NOT SET")

        if not api_key:
            return {
                "status": "error",
                "reason": "RESEND_API_KEY is empty or not set in environment"
            }

        resend.api_key = api_key

        params = {
            "from": "Raseel Platform <onboarding@resend.dev>",
            "to": ["raseelsupportsa@gmail.com"],
            "subject": "Raseel — Resend Test Email",
            "html": "<h1>Raseel Test</h1><p>Resend is working correctly.</p>",
            "text": "Raseel Test — Resend is working correctly.",
        }

        result = resend.Emails.send(params)

        return {
            "status": "success",
            "resend_result": str(result),
            "api_key_prefix": api_key[:8],
            "frontend_url": frontend_url,
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


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
