import os
import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "raseel-fallback-secret-not-for-production")
ALGORITHM = "HS256"
EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))


def hash_password(password):
    """Hash a password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password, hashed_password):
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(data, expires_delta=None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=EXPIRE_HOURS)
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.utcnow()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token):
    """Decode and validate a JWT token. Returns payload dict or None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
