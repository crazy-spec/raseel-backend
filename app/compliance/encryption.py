import hashlib
import os

# Simple encryption for development
# In production, use proper Fernet encryption with real key
_KEY = os.getenv("ENCRYPTION_KEY", "development-key")


def encrypt_pii(value: str) -> str:
    if not value:
        return ""
    # Simple reversible encoding for development
    # Replace with Fernet in production
    try:
        from cryptography.fernet import Fernet
        if len(_KEY) == 44 and _KEY.endswith("="):
            f = Fernet(_KEY.encode())
            return f.encrypt(value.encode()).decode()
    except (ImportError, Exception):
        pass
    # Fallback: base64
    import base64
    return base64.b64encode(value.encode()).decode()


def decrypt_pii(encrypted_value: str) -> str:
    if not encrypted_value:
        return ""
    try:
        from cryptography.fernet import Fernet
        if len(_KEY) == 44 and _KEY.endswith("="):
            f = Fernet(_KEY.encode())
            return f.decrypt(encrypted_value.encode()).decode()
    except (ImportError, Exception):
        pass
    import base64
    try:
        return base64.b64decode(encrypted_value.encode()).decode()
    except Exception:
        return encrypted_value


def hash_for_lookup(value: str) -> str:
    if not value:
        return ""
    salted = f"raseel-salt:{value}"
    return hashlib.sha256(salted.encode()).hexdigest()
