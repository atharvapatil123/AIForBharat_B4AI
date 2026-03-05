"""Policy version tracking models."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class VersionChangeType(str, Enum):
    """Types of changes in policy versions."""
    
    COVERAGE_CHANGE = "coverage_change"
    PREMIUM_CHANGE = "premium_change"
    EXCLUSION_ADDED = "exclusion_added"
    EXCLUSION_REMOVED = "exclusion_removed"
    INCLUSION_ADDED = "inclusion_added"
    INCLUSION_REMOVED = "inclusion_removed"
    WAITING_PERIOD_CHANGE = "waiting_period_change"
    TERMS_CHANGE = "terms_change"
    MINOR_UPDATE = "minor_update"


class PolicyVersionChange(BaseModel):
    """Represents a specific change between policy versions."""
    
    change_type: VersionChangeType = Field(..., description="Type of change")
    field_name: str = Field(..., description="Field that changed")
    old_value: Optional[str] = Field(None, description="Previous value")
    new_value: Optional[str] = Field(None, description="New value")
    description: str = Field(..., description="Human-readable description of change")
    impact_level: str = Field(..., description="Impact level: critical, high, medium, low")
    
    def affects_analyses(self) -> bool:
        """
        Determine if this change affects existing analyses.
        
        Critical and high impact changes affect analyses.
        """
        return self.impact_level in ['critical', 'high']


class PolicyVersion(BaseModel):
    """
    Represents a specific version of a policy document.
    
    Tracks version history for policy documents.
    Validates: Requirements 12.3
    """
    
    version_id: str = Field(..., description="Unique version identifier")
    policy_id: str = Field(..., description="Policy identifier this version belongs to")
    version_number: str = Field(..., description="Version number (e.g., '1.0', '2.1')")
    effective_date: datetime = Field(..., description="When this version became effective")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this version was created in the system"
    )
    created_by: Optional[str] = Field(None, description="User who created this version")
    
    # Snapshot of key policy data at this version
    coverage_amount: float = Field(..., description="Coverage amount at this version")
    premium: float = Field(..., description="Premium at this version")
    exclusions_count: int = Field(..., description="Number of exclusions")
    inclusions_count: int = Field(..., description="Number of inclusions")
    
    # Change tracking
    changes_from_previous: List[PolicyVersionChange] = Field(
        default_factory=list,
        description="Changes from previous version"
    )
    
    # Full document reference
    document_snapshot: Optional[str] = Field(
        None,
        description="Full policy document text at this version"
    )
    
    is_current: bool = Field(default=True, description="Whether this is the current version")
    
    def has_critical_changes(self) -> bool:
        """Check if this version has critical changes from previous version."""
        return any(
            change.impact_level == 'critical'
            for change in self.changes_from_previous
        )
    
    def has_high_impact_changes(self) -> bool:
        """Check if this version has high impact changes."""
        return any(
            change.impact_level in ['critical', 'high']
            for change in self.changes_from_previous
        )
    
    def get_changes_by_type(self, change_type: VersionChangeType) -> List[PolicyVersionChange]:
        """Get all changes of a specific type."""
        return [
            change for change in self.changes_from_previous
            if change.change_type == change_type
        ]


class PolicyVersionHistory(BaseModel):
    """
    Complete version history for a policy.
    
    Validates: Requirements 12.3
    """
    
    policy_id: str = Field(..., description="Policy identifier")
    policy_name: str = Field(..., description="Policy name")
    provider_id: str = Field(..., description="Provider identifier")
    
    versions: List[PolicyVersion] = Field(
        default_factory=list,
        description="All versions ordered by effective date (newest first)"
    )
    
    def get_current_version(self) -> Optional[PolicyVersion]:
        """Get the current active version."""
        for version in self.versions:
            if version.is_current:
                return version
        return None
    
    def get_version_by_number(self, version_number: str) -> Optional[PolicyVersion]:
        """Get a specific version by version number."""
        for version in self.versions:
            if version.version_number == version_number:
                return version
        return None
    
    def get_versions_since(self, since_date: datetime) -> List[PolicyVersion]:
        """Get all versions effective since a given date."""
        return [
            version for version in self.versions
            if version.effective_date >= since_date
        ]


class VersionComparison(BaseModel):
    """
    Comparison between two policy versions.
    
    Validates: Requirements 12.4
    """
    
    policy_id: str = Field(..., description="Policy identifier")
    policy_name: str = Field(..., description="Policy name")
    
    old_version: str = Field(..., description="Old version number")
    new_version: str = Field(..., description="New version number")
    
    old_effective_date: datetime = Field(..., description="Old version effective date")
    new_effective_date: datetime = Field(..., description="New version effective date")
    
    changes: List[PolicyVersionChange] = Field(
        default_factory=list,
        description="All changes between versions"
    )
    
    summary: str = Field(..., description="Summary of changes")
    
    affects_existing_analyses: bool = Field(
        ...,
        description="Whether changes affect existing analyses"
    )
    
    def get_critical_changes(self) -> List[PolicyVersionChange]:
        """Get all critical changes."""
        return [
            change for change in self.changes
            if change.impact_level == 'critical'
        ]
    
    def get_high_impact_changes(self) -> List[PolicyVersionChange]:
        """Get all high impact changes."""
        return [
            change for change in self.changes
            if change.impact_level in ['critical', 'high']
        ]
    
    def get_changes_by_type(self, change_type: VersionChangeType) -> List[PolicyVersionChange]:
        """Get all changes of a specific type."""
        return [
            change for change in self.changes
            if change.change_type == change_type
        ]


class AffectedAnalysis(BaseModel):
    """
    Represents an analysis that is affected by a policy update.
    
    Validates: Requirements 12.4
    """
    
    analysis_id: str = Field(..., description="Analysis identifier")
    analysis_type: str = Field(
        ...,
        description="Type of analysis (comparison, claim_prediction, ped_analysis)"
    )
    user_id: Optional[str] = Field(None, description="User who requested the analysis")
    created_at: datetime = Field(..., description="When analysis was created")
    
    policy_id: str = Field(..., description="Policy that was updated")
    old_version: str = Field(..., description="Version used in analysis")
    new_version: str = Field(..., description="Current version")
    
    affected_by_changes: List[PolicyVersionChange] = Field(
        default_factory=list,
        description="Changes that affect this analysis"
    )
    
    flagged_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this analysis was flagged"
    )
    
    notification_sent: bool = Field(
        default=False,
        description="Whether user was notified"
    )
    
    def requires_reanalysis(self) -> bool:
        """Determine if analysis requires reanalysis based on change impact."""
        return any(
            change.impact_level == 'critical'
            for change in self.affected_by_changes
        )
