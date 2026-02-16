"""
Sync Event model - tracks cross-service data synchronization
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..core.database import Base


class SyncEvent(Base):
    __tablename__ = "sync_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # What entity was synced
    entity_type = Column(String(50), nullable=False, index=True)  # 'organization', 'user', 'user_organization'
    entity_id = Column(String(255), nullable=False, index=True)  # UUID of the entity
    action = Column(String(20), nullable=False)  # 'create', 'update', 'delete'

    # Sync status
    status = Column(String(50), default="pending", index=True)  # 'pending', 'success', 'failed', 'retrying'
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Payload sent to CyberXLTR
    payload = Column(JSON, default={})

    # Response from CyberXLTR
    response_status_code = Column(Integer)
    response_body = Column(Text)
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_attempted_at = Column(DateTime)
    completed_at = Column(DateTime)

