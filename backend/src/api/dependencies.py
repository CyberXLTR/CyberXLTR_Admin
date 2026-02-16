"""
API dependencies
"""

from typing import Dict, Any
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..models import User
from .auth import require_admin_scope, ADMIN_EMAILS

import logging

logger = logging.getLogger(__name__)


async def verify_admin_token(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verify admin JWT token and ensure user has admin privileges
    """
    # Use the centralized admin scope validation
    payload = require_admin_scope(request)
    
    user_id = payload.get("sub")
    email = payload.get("email")
    
    # Additional validation: ensure user email is in admin list
    if email not in ADMIN_EMAILS:
        logger.warning(f"Unauthorized admin access attempt by: {email}")
        raise HTTPException(
            status_code=403,
            detail="Access denied: Admin privileges required"
        )
    
    # Verify user still exists and is active in database
    try:
        result = await db.execute(
            select(User).where(
                User.id == user_id,
                User.is_active == True
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=401, detail="Admin user not found or inactive")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database verification failed for admin {email}: {e}")
        raise HTTPException(status_code=500, detail="Database verification failed")
    
    return {"user_id": user_id, "email": email}

