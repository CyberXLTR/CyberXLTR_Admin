"""
Authentication utilities for admin system
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from jose import jwt, JWTError
import bcrypt

from ..core.config import settings

logger = logging.getLogger(__name__)

# Admin email list - only these emails can be admins
ADMIN_EMAILS = ["admin@cyberxltr.com"]


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Password hashing failed: {e}")
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against hash"""
    if not hashed_password:
        return False
    
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.warning(f"Password verification failed: {e}")
        return False


def create_access_token(user_id: str, email: str, expires_minutes: int = None) -> str:
    """Create a secure JWT access token"""
    if expires_minutes is None:
        expires_minutes = settings.jwt_expiration_hours * 60
    
    now = datetime.utcnow()
    expires = now + timedelta(minutes=expires_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expires,
        "iat": now,
        "nbf": now,
        "iss": "cyberxltr-admin",
        "aud": "cyberxltr-admin-api",
        "type": "access",
        "scope": "admin",
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str, email: str) -> str:
    """Create a secure JWT refresh token"""
    now = datetime.utcnow()
    expires = now + timedelta(days=7)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expires,
        "iat": now,
        "nbf": now,
        "iss": "cyberxltr-admin",
        "aud": "cyberxltr-admin-api",
        "type": "refresh",
        "scope": "admin",
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            audience="cyberxltr-admin-api",
            issuer="cyberxltr-admin",
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


def require_admin_scope(request: Request) -> Dict[str, Any]:
    """
    Verify admin JWT token from request headers
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )
    
    token = auth_header.replace("Bearer ", "")
    payload = verify_jwt_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    scope = payload.get("scope")
    if scope != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    
    return payload


def verify_admin_email(email: str) -> bool:
    """Check if email is in admin list"""
    return email in ADMIN_EMAILS

