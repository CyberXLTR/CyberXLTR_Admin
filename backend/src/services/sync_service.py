"""
Cross-Service Sync Service

Synchronizes organizations, users, and user-organization mappings
from CyberXLTR Admin to CyberXLTR main service via VPC peering / private networking.

Architecture:
  ┌──────────────────┐   VPC Peering    ┌──────────────────┐
  │  CyberXLTR Admin │ ──────────────→  │    CyberXLTR     │
  │  (VPC-A, RDS-A)  │   POST /sync/*   │  (VPC-B, RDS-B)  │
  └──────────────────┘                  └──────────────────┘

Authentication: Shared API key in X-Inter-Service-Key header
"""

import logging
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import select, update

from ..core.config import settings
from ..core.database import db_client
from ..models.sync_event import SyncEvent

logger = logging.getLogger(__name__)


class SyncService:
    """
    Handles synchronization of shared entities (organizations, users, user_organizations)
    from Admin to CyberXLTR via HTTP API over VPC peering.
    """

    def __init__(self):
        self.base_url = settings.cyberxltr_service_url.rstrip("/")
        self.api_key = settings.inter_service_api_key
        self.timeout = settings.sync_timeout
        self.max_retries = settings.sync_max_retries
        self.enabled = settings.sync_enabled

    def _get_headers(self) -> Dict[str, str]:
        """Headers for inter-service auth"""
        return {
            "Content-Type": "application/json",
            "X-Inter-Service-Key": self.api_key,
            "X-Source-Service": "cyberxltr-admin",
        }

    async def _record_sync_event(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        payload: Dict[str, Any],
        status: str = "pending",
        response_status_code: int = None,
        response_body: str = None,
        error_message: str = None,
    ) -> Optional[SyncEvent]:
        """Record a sync event in the database for auditing and retry"""
        try:
            async with db_client.get_session() as session:
                event = SyncEvent(
                    entity_type=entity_type,
                    entity_id=str(entity_id),
                    action=action,
                    payload=payload,
                    status=status,
                    response_status_code=response_status_code,
                    response_body=response_body,
                    error_message=error_message,
                    last_attempted_at=datetime.utcnow() if status != "pending" else None,
                    completed_at=datetime.utcnow() if status == "success" else None,
                )
                session.add(event)
                await session.commit()
                await session.refresh(event)
                return event
        except Exception as e:
            logger.error(f"Failed to record sync event: {e}")
            return None

    async def _update_sync_event(
        self,
        event_id: str,
        status: str,
        response_status_code: int = None,
        response_body: str = None,
        error_message: str = None,
        retry_count: int = None,
    ):
        """Update an existing sync event"""
        try:
            async with db_client.get_session() as session:
                updates = {
                    "status": status,
                    "last_attempted_at": datetime.utcnow(),
                }
                if response_status_code is not None:
                    updates["response_status_code"] = response_status_code
                if response_body is not None:
                    updates["response_body"] = response_body[:5000]  # Truncate
                if error_message is not None:
                    updates["error_message"] = error_message[:2000]
                if retry_count is not None:
                    updates["retry_count"] = retry_count
                if status == "success":
                    updates["completed_at"] = datetime.utcnow()

                await session.execute(
                    update(SyncEvent)
                    .where(SyncEvent.id == event_id)
                    .values(**updates)
                )
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to update sync event {event_id}: {e}")

    async def _send_sync_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        entity_type: str,
        entity_id: str,
        action: str,
    ) -> bool:
        """
        Send a sync request to CyberXLTR main service.
        Returns True if successful, False otherwise.
        """
        if not self.enabled:
            logger.info(f"Sync disabled - skipping {action} {entity_type} {entity_id}")
            await self._record_sync_event(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                payload=payload,
                status="skipped",
            )
            return True

        url = f"{self.base_url}{endpoint}"
        event = await self._record_sync_event(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            payload=payload,
            status="pending",
        )

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=self._get_headers(),
                    )

                if response.status_code in (200, 201):
                    logger.info(
                        f"Sync success: {action} {entity_type} {entity_id} "
                        f"-> {response.status_code}"
                    )
                    if event:
                        await self._update_sync_event(
                            event_id=str(event.id),
                            status="success",
                            response_status_code=response.status_code,
                            response_body=response.text,
                            retry_count=attempt,
                        )
                    return True
                else:
                    logger.warning(
                        f"Sync failed (attempt {attempt + 1}/{self.max_retries}): "
                        f"{action} {entity_type} {entity_id} -> {response.status_code}: "
                        f"{response.text[:200]}"
                    )
                    if event:
                        await self._update_sync_event(
                            event_id=str(event.id),
                            status="retrying" if attempt < self.max_retries - 1 else "failed",
                            response_status_code=response.status_code,
                            response_body=response.text,
                            retry_count=attempt + 1,
                        )

            except httpx.ConnectError as e:
                logger.warning(
                    f"Sync connection error (attempt {attempt + 1}/{self.max_retries}): "
                    f"{action} {entity_type} {entity_id} -> {e}"
                )
                if event:
                    await self._update_sync_event(
                        event_id=str(event.id),
                        status="retrying" if attempt < self.max_retries - 1 else "failed",
                        error_message=f"Connection error: {str(e)}",
                        retry_count=attempt + 1,
                    )
            except Exception as e:
                logger.error(
                    f"Sync error (attempt {attempt + 1}/{self.max_retries}): "
                    f"{action} {entity_type} {entity_id} -> {e}"
                )
                if event:
                    await self._update_sync_event(
                        event_id=str(event.id),
                        status="retrying" if attempt < self.max_retries - 1 else "failed",
                        error_message=str(e),
                        retry_count=attempt + 1,
                    )

        logger.error(
            f"Sync permanently failed after {self.max_retries} attempts: "
            f"{action} {entity_type} {entity_id}"
        )
        return False

    # ==================== Organization Sync ====================

    async def sync_organization_create(self, org_data: Dict[str, Any]) -> bool:
        """Sync new organization to CyberXLTR"""
        return await self._send_sync_request(
            endpoint="/api/v1/internal/sync/organization",
            payload={"action": "create", "data": org_data},
            entity_type="organization",
            entity_id=org_data.get("id", "unknown"),
            action="create",
        )

    async def sync_organization_update(self, org_data: Dict[str, Any]) -> bool:
        """Sync organization update to CyberXLTR"""
        return await self._send_sync_request(
            endpoint="/api/v1/internal/sync/organization",
            payload={"action": "update", "data": org_data},
            entity_type="organization",
            entity_id=org_data.get("id", "unknown"),
            action="update",
        )

    async def sync_organization_delete(self, org_id: str) -> bool:
        """Sync organization deactivation to CyberXLTR"""
        return await self._send_sync_request(
            endpoint="/api/v1/internal/sync/organization",
            payload={"action": "deactivate", "data": {"id": org_id}},
            entity_type="organization",
            entity_id=org_id,
            action="deactivate",
        )

    async def sync_organization_reactivate(self, org_id: str) -> bool:
        """Sync organization reactivation to CyberXLTR"""
        return await self._send_sync_request(
            endpoint="/api/v1/internal/sync/organization",
            payload={"action": "reactivate", "data": {"id": org_id}},
            entity_type="organization",
            entity_id=org_id,
            action="reactivate",
        )

    # ==================== User Sync ====================

    async def sync_user_create(self, user_data: Dict[str, Any], org_data: Dict[str, Any] = None) -> bool:
        """Sync new user to CyberXLTR (includes org assignment)"""
        payload = {"action": "create", "data": user_data}
        if org_data:
            payload["organization"] = org_data
        return await self._send_sync_request(
            endpoint="/api/v1/internal/sync/user",
            payload=payload,
            entity_type="user",
            entity_id=user_data.get("id", "unknown"),
            action="create",
        )

    async def sync_user_update(self, user_data: Dict[str, Any]) -> bool:
        """Sync user update to CyberXLTR"""
        return await self._send_sync_request(
            endpoint="/api/v1/internal/sync/user",
            payload={"action": "update", "data": user_data},
            entity_type="user",
            entity_id=user_data.get("id", "unknown"),
            action="update",
        )

    async def sync_user_deactivate(self, user_id: str) -> bool:
        """Sync user deactivation to CyberXLTR"""
        return await self._send_sync_request(
            endpoint="/api/v1/internal/sync/user",
            payload={"action": "deactivate", "data": {"id": user_id}},
            entity_type="user",
            entity_id=user_id,
            action="deactivate",
        )

    async def sync_user_reactivate(self, user_id: str) -> bool:
        """Sync user reactivation to CyberXLTR"""
        return await self._send_sync_request(
            endpoint="/api/v1/internal/sync/user",
            payload={"action": "reactivate", "data": {"id": user_id}},
            entity_type="user",
            entity_id=user_id,
            action="reactivate",
        )

    # ==================== User-Organization Sync ====================

    async def sync_user_organization(self, user_org_data: Dict[str, Any], action: str = "create") -> bool:
        """Sync user-organization assignment to CyberXLTR"""
        return await self._send_sync_request(
            endpoint="/api/v1/internal/sync/user-organization",
            payload={"action": action, "data": user_org_data},
            entity_type="user_organization",
            entity_id=user_org_data.get("id", "unknown"),
            action=action,
        )

    # ==================== Bulk Sync (for initial setup) ====================

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get sync health status"""
        try:
            async with db_client.get_session() as session:
                from sqlalchemy import func

                total = await session.execute(
                    select(func.count()).select_from(SyncEvent)
                )
                pending = await session.execute(
                    select(func.count()).select_from(SyncEvent).where(SyncEvent.status == "pending")
                )
                failed = await session.execute(
                    select(func.count()).select_from(SyncEvent).where(SyncEvent.status == "failed")
                )
                success = await session.execute(
                    select(func.count()).select_from(SyncEvent).where(SyncEvent.status == "success")
                )

                return {
                    "enabled": self.enabled,
                    "target_url": self.base_url,
                    "total_events": total.scalar(),
                    "pending": pending.scalar(),
                    "failed": failed.scalar(),
                    "success": success.scalar(),
                }
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {"enabled": self.enabled, "error": str(e)}


# Global instance
sync_service = SyncService()

