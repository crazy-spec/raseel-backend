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

# Simple in-memory store for reset tokens
# In production use Redis or database table
reset_tokens = {}


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
#  EMAIL HELPER
# ============================================================

def send_reset_email(to_email: str, reset_token: str, full_name: str):
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_email = os.getenv("SMTP_EMAIL", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")

        if not smtp_email or not smtp_password:
            logger.error("SMTP credentials not set")
            return False

        reset_url = "https://raseel-frontend-0.vercel.app/reset-password?token=" + reset_token

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Raseel — Reset Your Password"
        msg["From"] = "Raseel Platform <" + smtp_email + ">"
        msg["To"] = to_email

        text_content = """
Hello """ + full_name + """,

You requested to reset your Raseel password.

Click the link below to reset your password:
""" + reset_url + """

This link expires in 1 hour.

If you did not request this, ignore this email.

Raseel Platform
رسيل — منصة الأتمتة الذكية
"""

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

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, msg.as_string())

        logger.info("Reset email sent to: " + to_email)
        return True

    except Exception as e:
        logger.error("Email send failed: " + str(e))
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
    """Send password reset email."""

    user = db.query(User).filter(User.email == req.email.lower().strip()).first()

    if not user:
        return {"message": "If this email exists, a reset link has been sent."}

    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    reset_tokens[reset_token] = {
        "user_id": user.id,
        "email": user.email,
        "expires_at": expires_at,
    }

    send_reset_email(user.email, reset_token, user.full_name)

    logger.info("Password reset requested for: " + user.email)

    return {"message": "If this email exists, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token from email."""

    token_data = reset_tokens.get(req.token)

    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    if datetime.utcnow() > token_data["expires_at"]:
        del reset_tokens[req.token]
        raise HTTPException(status_code=400, detail="Reset token has expired.")

    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    user = db.query(User).filter(User.id == token_data["user_id"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.password_hash = hash_password(req.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    del reset_tokens[req.token]

    logger.info("Password reset successful for: " + user.email)

    return {"message": "Password reset successful. You can now login."}


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
