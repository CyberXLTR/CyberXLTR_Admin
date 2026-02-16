"""
Users API Router - Admin endpoints for managing users
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...core.database import get_db
from ...models import User, UserOrganization, Organization
from ..dependencies import verify_admin_token
from ..auth import hash_password, ADMIN_EMAILS
from ...services.sync_service import sync_service

logger = logging.getLogger(__name__)
router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    password: str
    confirm_password: str
    organization_id: str
    role: str = "sales_rep"


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_users(
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    search: Optional[str] = None,
    organization_id: Optional[str] = None
):
    """List all non-admin users with pagination and filtering"""
    try:
        query = select(User).outerjoin(UserOrganization).outerjoin(Organization)
        
        if search:
            query = query.where(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.first_name.ilike(f"%{search}%"),
                    User.last_name.ilike(f"%{search}%")
                )
            )
        
        if organization_id:
            query = query.where(UserOrganization.organization_id == organization_id)
        
        # Get total count
        count_query = select(func.count()).select_from(User)
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        users = result.scalars().all()
        
        # Filter out admins
        user_list = []
        for user in users:
            if user.email in ADMIN_EMAILS:
                continue
            
            user_list.append({
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name or f"{user.first_name} {user.last_name or ''}".strip(),
                "email_verified": user.email_verified,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            })
        
        return {
            "users": user_list,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.post("/")
async def create_user(
    user_data: UserCreate,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user with organization assignment"""
    try:
        # Validate passwords
        if len(user_data.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        if user_data.password != user_data.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        # Check if email is unique
        existing = await db.execute(select(User).where(User.email == user_data.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Check if organization exists
        org = await db.execute(
            select(Organization).where(
                Organization.id == user_data.organization_id,
                Organization.is_active == True
            )
        )
        if not org.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Organization not found or inactive")
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            first_name=user_data.first_name.strip(),
            last_name=user_data.last_name.strip() if user_data.last_name else None,
            phone=user_data.phone,
            job_title=user_data.job_title,
            department=user_data.department,
            encrypted_password=hashed_password,
            global_role="sales_rep",
            is_active=True,
            email_verified=True
        )
        
        db.add(user)
        await db.flush()
        
        # Create user-organization relationship
        user_org = UserOrganization(
            user_id=user.id,
            organization_id=user_data.organization_id,
            role=user_data.role,
            is_active=True
        )
        
        db.add(user_org)
        await db.commit()
        await db.refresh(user)
        
        # Sync user + org assignment to CyberXLTR via VPC peering
        user_sync_data = {
            "id": str(user.id),
            "email": user.email,
            "encrypted_password": user.encrypted_password,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name or f"{user.first_name} {user.last_name or ''}".strip(),
            "phone": user.phone,
            "job_title": user.job_title,
            "department": user.department,
            "global_role": user.global_role,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
        }
        org_assignment = {
            "id": str(user_org.id),
            "user_id": str(user.id),
            "organization_id": str(user_data.organization_id),
            "role": user_data.role,
            "is_active": True,
            "is_primary": False,
        }
        await sync_service.sync_user_create(user_sync_data, org_data=org_assignment)
        
        return {
            "success": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific user by ID"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name or f"{user.first_name} {user.last_name or ''}".strip(),
            "phone": user.phone,
            "job_title": user.job_title,
            "department": user.department,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user")


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing user"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check email uniqueness if updating
        if user_data.email and user_data.email != user.email:
            existing = await db.execute(
                select(User).where(User.email == user_data.email, User.id != user_id)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        # Sync update to CyberXLTR
        user_sync_data = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name or f"{user.first_name} {user.last_name or ''}".strip(),
            "phone": user.phone,
            "job_title": user.job_title,
            "department": user.department,
            "is_active": user.is_active,
        }
        await sync_service.sync_user_update(user_sync_data)
        
        return {
            "success": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "is_active": user.is_active
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a user"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # Sync deactivation to CyberXLTR
        await sync_service.sync_user_deactivate(user_id)
        
        return {"success": True, "message": "User deactivated"}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")


@router.post("/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Reactivate a deactivated user"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.is_active:
            raise HTTPException(status_code=400, detail="User is already active")
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # Sync reactivation to CyberXLTR
        await sync_service.sync_user_reactivate(user_id)
        
        return {"success": True, "message": "User reactivated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to reactivate user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reactivate user")

