"""
Admin Authentication API Router
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

from ...core.database import get_db
from ...models import User
from ..auth import verify_password, hash_password, create_access_token, create_refresh_token, verify_admin_email
from ..dependencies import verify_admin_token

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


class ProfileUpdateRequest(BaseModel):
    """Profile update request"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class PasswordUpdateRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str
    confirm_password: str


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


@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdateRequest,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Update admin profile information"""
    try:
        result = await db.execute(
            select(User).where(User.id == admin_user["user_id"])
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if profile_data.first_name is not None:
            user.first_name = profile_data.first_name.strip()
        if profile_data.last_name is not None:
            user.last_name = profile_data.last_name.strip() if profile_data.last_name else None

        user.full_name = f"{user.first_name} {user.last_name or ''}".strip()
        user.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(user)

        return {
            "success": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.put("/password")
async def update_password(
    password_data: PasswordUpdateRequest,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Change admin password"""
    try:
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(status_code=400, detail="New passwords do not match")

        if len(password_data.new_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

        result = await db.execute(
            select(User).where(User.id == admin_user["user_id"])
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(password_data.current_password, user.encrypted_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        user.encrypted_password = hash_password(password_data.new_password)
        user.updated_at = datetime.utcnow()

        await db.commit()

        return {"success": True, "message": "Password updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update password: {e}")
        raise HTTPException(status_code=500, detail="Failed to update password")

