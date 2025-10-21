"""Security utilities: JWT, password hashing, OTP generation."""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import secrets
import hashlib

import jwt
import bcrypt

from app.config import settings
from app.exceptions import AuthenticationError


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.
    
    Handles bcrypt's 72-byte limit by pre-hashing long passwords with SHA-256.
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    
    # If password exceeds 72 bytes, pre-hash it with SHA-256
    if len(password_bytes) > 72:
        password_bytes = hashlib.sha256(password_bytes).hexdigest().encode('utf-8')
    
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    # Convert password to bytes
    password_bytes = plain_password.encode('utf-8')
    
    # Apply same pre-processing as hash_password
    if len(password_bytes) > 72:
        password_bytes = hashlib.sha256(password_bytes).hexdigest().encode('utf-8')
    
    # Verify password
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except Exception as e:
        raise AuthenticationError(f"Token validation failed: {str(e)}")


def hash_token(token: str) -> str:
    """Hash a token for storage (e.g., refresh tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP code."""
    return "".join([str(secrets.randbelow(10)) for _ in range(length)])


def hash_otp(otp: str) -> str:
    """Hash an OTP code."""
    return hashlib.sha256(otp.encode()).hexdigest()


def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    """Verify an OTP against a hash."""
    return hash_otp(plain_otp) == hashed_otp


def generate_idempotency_key() -> str:
    """Generate a unique idempotency key for payments."""
    return secrets.token_urlsafe(32)