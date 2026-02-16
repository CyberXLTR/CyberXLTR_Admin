"""
Organization model
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ..core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False, unique=True)
    
    subscription_tier = Column(String(50), default="starter")
    max_storage_gb = Column(Integer, default=5)
    
    billing_email = Column(String(255))
    support_email = Column(String(255))
    phone = Column(String(50))
    company_address = Column(String(500))
    primary_color = Column(String(20), default="#3B82F6")
    
    environment = Column(String(50), default="production")
    description = Column(String(1000))
    
    max_users = Column(Integer, default=10)
    max_monthly_prospects = Column(Integer, default=1000)
    max_monthly_emails = Column(Integer, default=5000)
    
    is_active = Column(Boolean, default=True)
    
    features = Column(JSON, default={})
    settings = Column(JSON, default={})
    security_settings = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user_organizations = relationship("UserOrganization", back_populates="organization")

