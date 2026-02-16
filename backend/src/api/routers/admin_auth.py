"""
Admin Authentication API Router
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

from ...core.database import get_db
from ...models import User
from ..auth import verify_password, create_access_token, create_refresh_token, verify_admin_email

logger = logging.getLogger(__name__)
router = APIRouter()


class AdminLoginRequest(BaseModel):
    """Admin login request model"""
    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    """Admin login response model"""
    success: bool
    user: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    message: Optional[str] = None


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    login_data: AdminLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Admin login endpoint
    """
    try:
        # Check if email is in admin list
        if not verify_admin_email(login_data.email):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Admin privileges required"
            )
        
        # Get user from database
        result = await db.execute(
            select(User).where(
                User.email == login_data.email,
                User.is_active == True
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not verify_password(login_data.password, user.encrypted_password):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        
        # Create tokens
        access_token = create_access_token(str(user.id), user.email)
        refresh_token = create_refresh_token(str(user.id), user.email)
        
        return AdminLoginResponse(
            success=True,
            user={
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name or f"{user.first_name} {user.last_name or ''}".strip(),
                "role": "admin"
            },
            access_token=access_token,
            refresh_token=refresh_token,
            message="Login successful"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

