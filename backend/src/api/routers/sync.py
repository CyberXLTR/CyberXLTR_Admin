"""
Sync API Router - Monitor and manage cross-service synchronization
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import Dict, Any, Optional
from datetime import datetime

from ...core.database import get_db
from ...models import SyncEvent, Organization, User, UserOrganization
from ..dependencies import verify_admin_token
from ...services.sync_service import sync_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status")
async def get_sync_status(
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
):
    """Get overall sync health status"""
    try:
        status = await sync_service.get_sync_status()
        return {"status": "ok", **status}
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sync status")


@router.get("/events")
async def list_sync_events(
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = None,
    entity_type: Optional[str] = None,
):
    """List sync events with filtering"""
    try:
        query = select(SyncEvent)

        if status_filter:
            query = query.where(SyncEvent.status == status_filter)
        if entity_type:
            query = query.where(SyncEvent.entity_type == entity_type)

        # Count
        count_query = select(func.count()).select_from(SyncEvent)
        if status_filter:
            count_query = count_query.where(SyncEvent.status == status_filter)
        if entity_type:
            count_query = count_query.where(SyncEvent.entity_type == entity_type)

        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Results
        query = query.order_by(SyncEvent.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        events = result.scalars().all()

        return {
            "events": [
                {
                    "id": str(e.id),
                    "entity_type": e.entity_type,
                    "entity_id": e.entity_id,
                    "action": e.action,
                    "status": e.status,
                    "retry_count": e.retry_count,
                    "response_status_code": e.response_status_code,
                    "error_message": e.error_message,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                    "last_attempted_at": e.last_attempted_at.isoformat() if e.last_attempted_at else None,
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                }
                for e in events
            ],
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"Failed to list sync events: {e}")
        raise HTTPException(status_code=500, detail="Failed to list sync events")


@router.post("/retry-failed")
async def retry_failed_syncs(
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db),
):
    """Retry all failed sync events"""
    try:
        result = await db.execute(
            select(SyncEvent).where(SyncEvent.status == "failed")
        )
        failed_events = result.scalars().all()

        retried = 0
        succeeded = 0

        for event in failed_events:
            # Re-dispatch based on entity type and action
            success = await sync_service._send_sync_request(
                endpoint=_get_endpoint_for_entity(event.entity_type),
                payload=event.payload,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                action=event.action,
            )
            retried += 1
            if success:
                succeeded += 1
                # Mark original event as superseded
                event.status = "superseded"
                event.error_message = f"Superseded by manual retry at {datetime.utcnow().isoformat()}"

        await db.commit()

        return {
            "retried": retried,
            "succeeded": succeeded,
            "failed": retried - succeeded,
        }
    except Exception as e:
        logger.error(f"Failed to retry syncs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retry syncs")


@router.post("/full-sync")
async def trigger_full_sync(
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger a full sync of all organizations and users to CyberXLTR.
    Useful for initial setup or disaster recovery.
    """
    try:
        results = {"organizations": 0, "users": 0, "user_organizations": 0, "errors": []}

        # Sync all active organizations
        org_result = await db.execute(
            select(Organization).where(Organization.is_active == True)
        )
        organizations = org_result.scalars().all()

        for org in organizations:
            org_data = {
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
            success = await sync_service.sync_organization_create(org_data)
            if success:
                results["organizations"] += 1
            else:
                results["errors"].append(f"org:{org.id}")

        # Sync all active users
        user_result = await db.execute(
            select(User).where(User.is_active == True)
        )
        users = user_result.scalars().all()

        for user in users:
            user_data = {
                "id": str(user.id),
                "email": user.email,
                "encrypted_password": user.encrypted_password,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "phone": user.phone,
                "job_title": user.job_title,
                "department": user.department,
                "global_role": user.global_role,
                "is_active": user.is_active,
                "email_verified": user.email_verified,
            }
            success = await sync_service.sync_user_create(user_data)
            if success:
                results["users"] += 1
            else:
                results["errors"].append(f"user:{user.id}")

        # Sync all user-organization mappings
        uo_result = await db.execute(
            select(UserOrganization).where(UserOrganization.is_active == True)
        )
        user_orgs = uo_result.scalars().all()

        for uo in user_orgs:
            uo_data = {
                "id": str(uo.id),
                "user_id": str(uo.user_id),
                "organization_id": str(uo.organization_id),
                "role": uo.role,
                "is_active": uo.is_active,
                "is_primary": uo.is_primary,
            }
            success = await sync_service.sync_user_organization(uo_data, action="create")
            if success:
                results["user_organizations"] += 1
            else:
                results["errors"].append(f"user_org:{uo.id}")

        return {
            "success": True,
            "synced": results,
        }
    except Exception as e:
        logger.error(f"Full sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Full sync failed: {str(e)}")


def _get_endpoint_for_entity(entity_type: str) -> str:
    """Map entity type to sync endpoint"""
    mapping = {
        "organization": "/api/v1/internal/sync/organization",
        "user": "/api/v1/internal/sync/user",
        "user_organization": "/api/v1/internal/sync/user-organization",
    }
    return mapping.get(entity_type, f"/api/v1/internal/sync/{entity_type}")

