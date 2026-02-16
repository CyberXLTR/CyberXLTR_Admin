"""
Notification model
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)
    
    target = Column(String(50), default="all_users")
    target_spec = Column(JSON, default={})
    
    priority = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    expires_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

