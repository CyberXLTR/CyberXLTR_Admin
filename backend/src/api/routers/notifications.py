"""
Notifications API Router - Admin endpoints for managing notifications
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ...core.database import get_db
from ...models import Notification
from ..dependencies import verify_admin_token

logger = logging.getLogger(__name__)
router = APIRouter()


class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str = "info"
    priority: int = 1
    expires_at: Optional[str] = None


class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None
    target: Optional[str] = None
    target_spec: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    expires_at: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_notifications(
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    is_active: Optional[bool] = None,
    type_filter: Optional[str] = None
):
    """List all notifications with pagination and filtering"""
    try:
        query = select(Notification)
        
        if is_active is not None:
            query = query.where(Notification.is_active == is_active)
        
        if type_filter:
            query = query.where(Notification.type == type_filter)
        
        # Get total count
        count_query = select(func.count()).select_from(Notification)
        if is_active is not None:
            count_query = count_query.where(Notification.is_active == is_active)
        if type_filter:
            count_query = count_query.where(Notification.type == type_filter)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        notifications = result.scalars().all()
        
        return {
            "notifications": [
                {
                    "id": str(notif.id),
                    "title": notif.title,
                    "message": notif.message,
                    "type": notif.type,
                    "target": notif.target,
                    "target_spec": notif.target_spec,
                    "priority": notif.priority,
                    "is_active": notif.is_active,
                    "created_by": str(notif.created_by) if notif.created_by else None,
                    "expires_at": notif.expires_at.isoformat() if notif.expires_at else None,
                    "created_at": notif.created_at.isoformat() if notif.created_at else None,
                    "updated_at": notif.updated_at.isoformat() if notif.updated_at else None,
                }
                for notif in notifications
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Failed to list notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to list notifications")


@router.post("/")
async def create_notification(
    notification_data: NotificationCreate,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Create a new notification"""
    try:
        # Validate notification data
        if not notification_data.title or not notification_data.message:
            raise HTTPException(status_code=400, detail="Title and message are required")
        
        # Validate type enum
        valid_types = ['info', 'warning', 'success', 'error', 'system_update', 
                      'maintenance', 'feature_announcement', 'security_alert']
        
        if notification_data.type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid notification type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Create notification
        notification = Notification(
            title=notification_data.title,
            message=notification_data.message,
            type=notification_data.type,
            target='all_users',
            target_spec={},
            priority=notification_data.priority,
            created_by=admin_user["user_id"],
            is_active=True,
            expires_at=notification_data.expires_at
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        return {
            "success": True,
            "notification": {
                "id": str(notification.id),
                "title": notification.title,
                "message": notification.message,
                "type": notification.type,
                "is_active": notification.is_active
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to create notification")


@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific notification by ID"""
    try:
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {
            "id": str(notification.id),
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
            "target": notification.target,
            "target_spec": notification.target_spec,
            "priority": notification.priority,
            "is_active": notification.is_active,
            "created_by": str(notification.created_by) if notification.created_by else None,
            "expires_at": notification.expires_at.isoformat() if notification.expires_at else None,
            "created_at": notification.created_at.isoformat() if notification.created_at else None,
            "updated_at": notification.updated_at.isoformat() if notification.updated_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get notification {notification_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification")


@router.put("/{notification_id}")
async def update_notification(
    notification_id: str,
    notification_data: NotificationUpdate,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing notification"""
    try:
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Validate type if updating
        if notification_data.type:
            valid_types = ['info', 'warning', 'success', 'error', 'system_update',
                          'maintenance', 'feature_announcement', 'security_alert']
            if notification_data.type not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid notification type. Must be one of: {', '.join(valid_types)}"
                )
        
        # Update fields
        update_data = notification_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(notification, key, value)
        
        notification.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(notification)
        
        return {
            "success": True,
            "notification": {
                "id": str(notification.id),
                "title": notification.title,
                "is_active": notification.is_active
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update notification {notification_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notification")


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a notification"""
    try:
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notification.is_active = False
        notification.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Notification deactivated"}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete notification {notification_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")


@router.get("/stats/overview")
async def get_notifications_stats(
    admin_user: Dict[str, Any] = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Get notifications statistics for admin dashboard"""
    try:
        # Get total notifications
        total_result = await db.execute(select(func.count()).select_from(Notification))
        total_count = total_result.scalar()
        
        # Get active notifications
        active_result = await db.execute(
            select(func.count()).select_from(Notification).where(Notification.is_active == True)
        )
        active_count = active_result.scalar()
        
        # Get recent notifications (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_result = await db.execute(
            select(func.count()).select_from(Notification).where(Notification.created_at >= seven_days_ago)
        )
        recent_count = recent_result.scalar()
        
        return {
            "total_notifications": total_count,
            "active_notifications": active_count,
            "recent_notifications": recent_count,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Failed to fetch notifications stats: {e}")
        return {
            "total_notifications": 0,
            "active_notifications": 0,
            "recent_notifications": 0,
            "status": "error"
        }

