"""
Organizations API Router
Admin endpoints for managing organizations
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...core.database import get_db
from ...models import Organization
from ..dependencies import verify_admin_token
from ...services.sync_service import sync_service

logger = logging.getLogger(__name__)
router = APIRouter()


class OrganizationCreate(BaseModel):
    name: str
    url: str
    subscription_tier: str = "starter"
    max_storage_gb: int = 5
    billing_email: Optional[str] = None
    support_email: Optional[str] = None
    phone: Optional[str] = None
    company_address: Optional[str] = None
    primary_color: str = "#3B82F6"


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    subscription_tier: Optional[str] = None
    max_storage_gb: Optional[int] = None
    billing_email: Optional[str] = None
    support_email: Optional[str] = None
    phone: Optional[str] = None
    company_address: Optional[str] = None
    primary_color: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_organizations(
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    search: Optional[str] = None,
    status: Optional[str] = None
):
    """
    List all organizations with pagination and filtering
    """
    try:
        query = select(Organization)
        
        if search:
            query = query.where(
                or_(
                    Organization.name.ilike(f"%{search}%"),
                    Organization.url.ilike(f"%{search}%")
                )
            )
        
        if status == "active":
            query = query.where(Organization.is_active == True)
        elif status == "inactive":
            query = query.where(Organization.is_active == False)
        
        # Get total count
        count_query = select(func.count()).select_from(Organization)
        if search:
            count_query = count_query.where(
                or_(
                    Organization.name.ilike(f"%{search}%"),
                    Organization.url.ilike(f"%{search}%")
                )
            )
        if status:
            is_active = status == "active"
            count_query = count_query.where(Organization.is_active == is_active)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        organizations = result.scalars().all()
        
        return {
            "organizations": [
                {
                    "id": str(org.id),
                    "name": org.name,
                    "url": org.url,
                    "subscription_tier": org.subscription_tier,
                    "max_storage_gb": org.max_storage_gb,
                    "billing_email": org.billing_email,
                    "support_email": org.support_email,
                    "phone": org.phone,
                    "company_address": org.company_address,
                    "primary_color": org.primary_color,
                    "is_active": org.is_active,
                    "created_at": org.created_at.isoformat() if org.created_at else None,
                    "updated_at": org.updated_at.isoformat() if org.updated_at else None,
                }
                for org in organizations
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Failed to list organizations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list organizations")


@router.get("/{organization_id}")
async def get_organization(
    organization_id: str,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific organization by ID
    """
    try:
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one_or_none()
        
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return {
            "id": str(org.id),
            "name": org.name,
            "url": org.url,
            "subscription_tier": org.subscription_tier,
            "max_storage_gb": org.max_storage_gb,
            "billing_email": org.billing_email,
            "support_email": org.support_email,
            "phone": org.phone,
            "company_address": org.company_address,
            "primary_color": org.primary_color,
            "environment": org.environment,
            "description": org.description,
            "max_users": org.max_users,
            "max_monthly_prospects": org.max_monthly_prospects,
            "max_monthly_emails": org.max_monthly_emails,
            "is_active": org.is_active,
            "features": org.features,
            "settings": org.settings,
            "security_settings": org.security_settings,
            "created_at": org.created_at.isoformat() if org.created_at else None,
            "updated_at": org.updated_at.isoformat() if org.updated_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get organization {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get organization")


@router.post("/")
async def create_organization(
    org_data: OrganizationCreate,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new organization
    """
    try:
        # Check if URL is unique
        existing = await db.execute(
            select(Organization).where(Organization.url == org_data.url)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Organization URL already exists")
        
        # Create organization
        org = Organization(
            name=org_data.name,
            url=org_data.url,
            subscription_tier=org_data.subscription_tier,
            max_storage_gb=org_data.max_storage_gb,
            billing_email=org_data.billing_email,
            support_email=org_data.support_email,
            phone=org_data.phone,
            company_address=org_data.company_address,
            primary_color=org_data.primary_color,
            environment="production",
            description="",
            max_users=10,
            max_monthly_prospects=1000,
            max_monthly_emails=5000,
            is_active=True,
            features={
                "sso_auth": False,
                "ai_scoring": True,
                "api_access": False,
                "audit_logs": True,
                "data_export": True,
                "white_label": False,
                "web_scraping": True,
                "email_outreach": True,
                "multi_language": False,
                "priority_support": False,
                "advanced_analytics": False,
                "custom_integrations": False
            },
            settings={
                "currency": "USD",
                "timezone": "UTC",
                "date_format": "MM/DD/YYYY",
                "auto_follow_up": True,
                "email_signature": "",
                "lead_scoring_enabled": True,
                "default_email_template": "professional",
                "notification_preferences": {
                    "deal_alerts": True,
                    "weekly_reports": True,
                    "email_notifications": True
                }
            },
            security_settings={
                "ip_whitelist": [],
                "audit_logging": True,
                "password_policy": "strong",
                "session_timeout": 480,
                "two_factor_required": False
            }
        )
        
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
        # Sync to CyberXLTR via VPC peering
        org_sync_data = {
            "id": str(org.id),
            "name": org.name,
            "url": org.url,
            "subscription_tier": org.subscription_tier,
            "max_storage_gb": org.max_storage_gb,
            "billing_email": org.billing_email,
            "support_email": org.support_email,
            "phone": org.phone,
            "company_address": org.company_address,
            "primary_color": org.primary_color,
            "environment": org.environment,
            "description": org.description,
            "max_users": org.max_users,
            "max_monthly_prospects": org.max_monthly_prospects,
            "max_monthly_emails": org.max_monthly_emails,
            "is_active": org.is_active,
            "features": org.features or {},
            "settings": org.settings or {},
            "security_settings": org.security_settings or {},
        }
        await sync_service.sync_organization_create(org_sync_data)
        
        return {
            "success": True,
            "organization": {
                "id": str(org.id),
                "name": org.name,
                "url": org.url,
                "subscription_tier": org.subscription_tier,
                "is_active": org.is_active
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create organization: {e}")
        raise HTTPException(status_code=500, detail="Failed to create organization")


@router.put("/{organization_id}")
async def update_organization(
    organization_id: str,
    org_data: OrganizationUpdate,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing organization
    """
    try:
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one_or_none()
        
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Check URL uniqueness if updating
        if org_data.url and org_data.url != org.url:
            existing = await db.execute(
                select(Organization).where(
                    Organization.url == org_data.url,
                    Organization.id != organization_id
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Organization URL already exists")
        
        # Update fields
        update_data = org_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(org, key, value)
        
        org.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(org)
        
        # Sync update to CyberXLTR
        org_sync_data = {
            "id": str(org.id),
            "name": org.name,
            "url": org.url,
            "subscription_tier": org.subscription_tier,
            "max_storage_gb": org.max_storage_gb,
            "billing_email": org.billing_email,
            "support_email": org.support_email,
            "phone": org.phone,
            "company_address": org.company_address,
            "primary_color": org.primary_color,
            "environment": org.environment,
            "description": org.description,
            "max_users": org.max_users,
            "max_monthly_prospects": org.max_monthly_prospects,
            "max_monthly_emails": org.max_monthly_emails,
            "is_active": org.is_active,
            "features": org.features or {},
            "settings": org.settings or {},
            "security_settings": org.security_settings or {},
        }
        await sync_service.sync_organization_update(org_sync_data)
        
        return {
            "success": True,
            "organization": {
                "id": str(org.id),
                "name": org.name,
                "url": org.url,
                "is_active": org.is_active
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update organization {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update organization")


@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: str,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete an organization
    """
    try:
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one_or_none()
        
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        org.is_active = False
        org.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # Sync deactivation to CyberXLTR
        await sync_service.sync_organization_delete(organization_id)
        
        return {"success": True, "message": "Organization deactivated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete organization {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete organization")


@router.post("/{organization_id}/reactivate")
async def reactivate_organization(
    organization_id: str,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Reactivate a deactivated organization
    """
    try:
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one_or_none()
        
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        if org.is_active:
            raise HTTPException(status_code=400, detail="Organization is already active")
        
        org.is_active = True
        org.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # Sync reactivation to CyberXLTR
        await sync_service.sync_organization_reactivate(organization_id)
        
        return {"success": True, "message": "Organization reactivated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to reactivate organization {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reactivate organization")

