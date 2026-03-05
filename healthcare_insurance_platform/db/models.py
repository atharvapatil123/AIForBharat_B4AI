"""SQLAlchemy database models for policy versioning."""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from healthcare_insurance_platform.db.base import Base


class PolicyVersionDB(Base):
    """Database model for policy versions."""
    
    __tablename__ = "policy_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(String(255), unique=True, nullable=False, index=True)
    policy_id = Column(String(255), nullable=False, index=True)
    version_number = Column(String(50), nullable=False)
    effective_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    created_by = Column(String(255), nullable=True)
    
    # Snapshot of key policy data
    coverage_amount = Column(Float, nullable=False)
    premium = Column(Float, nullable=False)
    exclusions_count = Column(Integer, nullable=False)
    inclusions_count = Column(Integer, nullable=False)
    
    # Changes from previous version (stored as JSON)
    changes_from_previous = Column(JSON, nullable=False, default=list)
    
    # Full document snapshot
    document_snapshot = Column(Text, nullable=True)
    
    is_current = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    affected_analyses = relationship(
        "AffectedAnalysisDB",
        back_populates="policy_version",
        cascade="all, delete-orphan"
    )


class AffectedAnalysisDB(Base):
    """Database model for analyses affected by policy updates."""
    
    __tablename__ = "affected_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(255), unique=True, nullable=False, index=True)
    analysis_type = Column(String(100), nullable=False)
    user_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    
    policy_id = Column(String(255), nullable=False, index=True)
    old_version = Column(String(50), nullable=False)
    new_version = Column(String(50), nullable=False)
    
    # Changes that affect this analysis (stored as JSON)
    affected_by_changes = Column(JSON, nullable=False, default=list)
    
    flagged_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    notification_sent = Column(Boolean, nullable=False, default=False)
    
    # Foreign key to policy version
    policy_version_id = Column(Integer, ForeignKey("policy_versions.id"), nullable=True)
    
    # Relationships
    policy_version = relationship("PolicyVersionDB", back_populates="affected_analyses")
