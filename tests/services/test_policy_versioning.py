"""Unit tests for policy versioning service."""

import pytest
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from healthcare_insurance_platform.models.policy import (
    PolicyDocument,
    WaitingPeriod,
    DocumentRequirement,
    ParsedClause,
)
from healthcare_insurance_platform.models.policy_version import (
    PolicyVersion,
    PolicyVersionChange,
    VersionChangeType,
    VersionComparison,
    PolicyVersionHistory,
)
from healthcare_insurance_platform.services.policy_versioning import PolicyVersioningService


@pytest.fixture
def sample_policy_v1():
    """Create a sample policy document version 1."""
    return PolicyDocument(
        policy_id="policy-123",
        provider_id="provider-1",
        policy_name="Health Plus",
        policy_type="individual",
        version="1.0",
        effective_date=date(2024, 1, 1),
        coverage_amount=500000.0,
        premium=15000.0,
        waiting_periods=WaitingPeriod(
            general=30,
            pre_existing=730,
            specific_conditions=[],
        ),
        inclusions=[
            "Hospitalization",
            "Surgery",
            "Diagnostic tests",
        ],
        exclusions=[
            "Cosmetic surgery",
            "Dental treatment",
        ],
        ped_policy="Pre-existing diseases covered after 2 years",
        claim_process="Submit within 30 days",
        document_requirements=[
            DocumentRequirement(
                claim_type="hospitalization",
                documents=["Discharge summary", "Bills"],
            ),
        ],
        full_text="Full policy text version 1.0",
        parsed_clauses=[
            ParsedClause(
                clause_type="coverage",
                text="Coverage: Rs. 5 lakh",
                importance="critical",
            ),
        ],
    )


@pytest.fixture
def sample_policy_v2():
    """Create a sample policy document version 2 with changes."""
    return PolicyDocument(
        policy_id="policy-123",
        provider_id="provider-1",
        policy_name="Health Plus",
        policy_type="individual",
        version="2.0",
        effective_date=date(2024, 6, 1),
        coverage_amount=750000.0,  # Increased by 50%
        premium=18000.0,  # Increased by 20%
        waiting_periods=WaitingPeriod(
            general=30,
            pre_existing=730,
            specific_conditions=[],
        ),
        inclusions=[
            "Hospitalization",
            "Surgery",
            "Diagnostic tests",
            "Maternity coverage",  # New inclusion
        ],
        exclusions=[
            "Cosmetic surgery",
            "Dental treatment",
            "Alternative medicine",  # New exclusion
        ],
        ped_policy="Pre-existing diseases covered after 2 years",
        claim_process="Submit within 30 days",
        document_requirements=[
            DocumentRequirement(
                claim_type="hospitalization",
                documents=["Discharge summary", "Bills"],
            ),
        ],
        full_text="Full policy text version 2.0",
        parsed_clauses=[
            ParsedClause(
                clause_type="coverage",
                text="Coverage: Rs. 7.5 lakh",
                importance="critical",
            ),
        ],
    )


@pytest.fixture
def versioning_service():
    """Create a policy versioning service instance."""
    mock_db_session = AsyncMock()
    return PolicyVersioningService(db_session=mock_db_session)


class TestPolicyVersionCreation:
    """Tests for creating policy versions."""
    
    @pytest.mark.asyncio
    async def test_create_first_version(self, versioning_service, sample_policy_v1):
        """Test creating the first version of a policy."""
        # Mock database operations
        versioning_service._store_version_in_db = AsyncMock()
        versioning_service._mark_previous_versions_as_old = AsyncMock()
        
        version = await versioning_service.create_version(
            policy_document=sample_policy_v1,
            previous_version=None,
            created_by="admin",
        )
        
        assert version.policy_id == "policy-123"
        assert version.version_number == "1.0"
        assert version.coverage_amount == 500000.0
        assert version.premium == 15000.0
        assert version.exclusions_count == 2
        assert version.inclusions_count == 3
        assert version.is_current is True
        assert len(version.changes_from_previous) == 0  # No previous version
        assert version.created_by == "admin"
    
    @pytest.mark.asyncio
    async def test_create_version_with_changes(
        self,
        versioning_service,
        sample_policy_v1,
        sample_policy_v2,
    ):
        """Test creating a new version with changes detected."""
        # Mock database operations
        versioning_service._store_version_in_db = AsyncMock()
        versioning_service._mark_previous_versions_as_old = AsyncMock()
        
        version = await versioning_service.create_version(
            policy_document=sample_policy_v2,
            previous_version=sample_policy_v1,
            created_by="admin",
        )
        
        assert version.policy_id == "policy-123"
        assert version.version_number == "2.0"
        assert len(version.changes_from_previous) > 0
        
        # Check that changes were detected
        change_types = {c.change_type for c in version.changes_from_previous}
        assert VersionChangeType.COVERAGE_CHANGE in change_types
        assert VersionChangeType.PREMIUM_CHANGE in change_types
        assert VersionChangeType.INCLUSION_ADDED in change_types
        assert VersionChangeType.EXCLUSION_ADDED in change_types


class TestChangeDetection:
    """Tests for detecting changes between versions."""
    
    def test_detect_coverage_change(
        self,
        versioning_service,
        sample_policy_v1,
        sample_policy_v2,
    ):
        """Test detection of coverage amount changes."""
        changes = versioning_service._detect_changes(
            sample_policy_v1,
            sample_policy_v2,
        )
        
        coverage_changes = [
            c for c in changes
            if c.change_type == VersionChangeType.COVERAGE_CHANGE
        ]
        
        assert len(coverage_changes) == 1
        change = coverage_changes[0]
        assert change.field_name == "coverage_amount"
        assert "Rs. 500,000" in change.old_value
        assert "Rs. 750,000" in change.new_value
        assert change.impact_level == "critical"  # 50% increase
    
    def test_detect_premium_change(
        self,
        versioning_service,
        sample_policy_v1,
        sample_policy_v2,
    ):
        """Test detection of premium changes."""
        changes = versioning_service._detect_changes(
            sample_policy_v1,
            sample_policy_v2,
        )
        
        premium_changes = [
            c for c in changes
            if c.change_type == VersionChangeType.PREMIUM_CHANGE
        ]
        
        assert len(premium_changes) == 1
        change = premium_changes[0]
        assert change.field_name == "premium"
        assert "Rs. 15,000" in change.old_value
        assert "Rs. 18,000" in change.new_value
        assert change.impact_level == "high"  # 20% increase
    
    def test_detect_inclusion_added(
        self,
        versioning_service,
        sample_policy_v1,
        sample_policy_v2,
    ):
        """Test detection of new inclusions."""
        changes = versioning_service._detect_changes(
            sample_policy_v1,
            sample_policy_v2,
        )
        
        inclusion_changes = [
            c for c in changes
            if c.change_type == VersionChangeType.INCLUSION_ADDED
        ]
        
        assert len(inclusion_changes) == 1
        change = inclusion_changes[0]
        assert "Maternity coverage" in change.new_value
        assert change.impact_level == "high"
    
    def test_detect_exclusion_added(
        self,
        versioning_service,
        sample_policy_v1,
        sample_policy_v2,
    ):
        """Test detection of new exclusions."""
        changes = versioning_service._detect_changes(
            sample_policy_v1,
            sample_policy_v2,
        )
        
        exclusion_changes = [
            c for c in changes
            if c.change_type == VersionChangeType.EXCLUSION_ADDED
        ]
        
        assert len(exclusion_changes) == 1
        change = exclusion_changes[0]
        assert "Alternative medicine" in change.new_value
        assert change.impact_level == "critical"  # Adding exclusions is critical
    
    def test_no_changes_detected(self, versioning_service, sample_policy_v1):
        """Test that no changes are detected for identical policies."""
        changes = versioning_service._detect_changes(
            sample_policy_v1,
            sample_policy_v1,
        )
        
        assert len(changes) == 0


class TestVersionComparison:
    """Tests for comparing policy versions."""
    
    @pytest.mark.asyncio
    async def test_compare_versions(self, versioning_service):
        """Test comparing two policy versions."""
        # Mock database retrieval
        mock_old_version = PolicyVersion(
            version_id="v1",
            policy_id="policy-123",
            version_number="1.0",
            effective_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            coverage_amount=500000.0,
            premium=15000.0,
            exclusions_count=2,
            inclusions_count=3,
            changes_from_previous=[],
        )
        
        mock_new_version = PolicyVersion(
            version_id="v2",
            policy_id="policy-123",
            version_number="2.0",
            effective_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
            coverage_amount=750000.0,
            premium=18000.0,
            exclusions_count=3,
            inclusions_count=4,
            changes_from_previous=[
                PolicyVersionChange(
                    change_type=VersionChangeType.COVERAGE_CHANGE,
                    field_name="coverage_amount",
                    old_value="Rs. 500,000",
                    new_value="Rs. 750,000",
                    description="Coverage increased by 50%",
                    impact_level="critical",
                ),
            ],
        )
        
        versioning_service._get_version_from_db = AsyncMock(
            side_effect=[mock_old_version, mock_new_version]
        )
        
        comparison = await versioning_service.compare_versions(
            policy_id="policy-123",
            old_version_number="1.0",
            new_version_number="2.0",
        )
        
        assert comparison.policy_id == "policy-123"
        assert comparison.old_version == "1.0"
        assert comparison.new_version == "2.0"
        assert len(comparison.changes) == 1
        assert comparison.affects_existing_analyses is True
    
    def test_generate_comparison_summary(self, versioning_service):
        """Test generating a comparison summary."""
        changes = [
            PolicyVersionChange(
                change_type=VersionChangeType.COVERAGE_CHANGE,
                field_name="coverage_amount",
                old_value="Rs. 500,000",
                new_value="Rs. 750,000",
                description="Coverage increased by 50%",
                impact_level="critical",
            ),
            PolicyVersionChange(
                change_type=VersionChangeType.PREMIUM_CHANGE,
                field_name="premium",
                old_value="Rs. 15,000",
                new_value="Rs. 18,000",
                description="Premium increased by 20%",
                impact_level="high",
            ),
        ]
        
        summary = versioning_service._generate_comparison_summary(changes)
        
        assert "Total changes: 2" in summary
        assert "1 critical changes" in summary
        assert "1 high impact changes" in summary
        assert "Coverage increased by 50%" in summary


class TestAffectedAnalyses:
    """Tests for flagging affected analyses."""
    
    @pytest.mark.asyncio
    async def test_flag_affected_analyses(self, versioning_service):
        """Test flagging analyses affected by policy updates."""
        mock_version = PolicyVersion(
            version_id="v2",
            policy_id="policy-123",
            version_number="2.0",
            effective_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
            coverage_amount=750000.0,
            premium=18000.0,
            exclusions_count=3,
            inclusions_count=4,
            changes_from_previous=[
                PolicyVersionChange(
                    change_type=VersionChangeType.EXCLUSION_ADDED,
                    field_name="exclusions",
                    old_value=None,
                    new_value="Alternative medicine",
                    description="New exclusion added",
                    impact_level="critical",
                ),
            ],
        )
        
        versioning_service._store_affected_analysis_in_db = AsyncMock()
        
        affected = await versioning_service.flag_affected_analyses(
            policy_id="policy-123",
            new_version=mock_version,
            analysis_ids=["analysis-1", "analysis-2"],
        )
        
        assert len(affected) == 2
        assert all(a.policy_id == "policy-123" for a in affected)
        assert all(a.new_version == "2.0" for a in affected)
        assert all(len(a.affected_by_changes) == 1 for a in affected)
    
    @pytest.mark.asyncio
    async def test_no_affected_analyses_for_minor_changes(self, versioning_service):
        """Test that minor changes don't flag analyses."""
        mock_version = PolicyVersion(
            version_id="v2",
            policy_id="policy-123",
            version_number="2.0",
            effective_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
            coverage_amount=500000.0,
            premium=15000.0,
            exclusions_count=2,
            inclusions_count=3,
            changes_from_previous=[
                PolicyVersionChange(
                    change_type=VersionChangeType.MINOR_UPDATE,
                    field_name="full_text",
                    old_value="Old text",
                    new_value="New text",
                    description="Minor text update",
                    impact_level="low",
                ),
            ],
        )
        
        affected = await versioning_service.flag_affected_analyses(
            policy_id="policy-123",
            new_version=mock_version,
            analysis_ids=["analysis-1"],
        )
        
        assert len(affected) == 0


class TestVersionHistory:
    """Tests for version history management."""
    
    @pytest.mark.asyncio
    async def test_get_version_history(self, versioning_service):
        """Test retrieving version history."""
        # Mock database query
        mock_versions = [
            MagicMock(
                version_id="v2",
                policy_id="policy-123",
                version_number="2.0",
                effective_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
                created_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
                created_by="admin",
                coverage_amount=750000.0,
                premium=18000.0,
                exclusions_count=3,
                inclusions_count=4,
                changes_from_previous=[],
                document_snapshot="Text v2",
                is_current=True,
            ),
            MagicMock(
                version_id="v1",
                policy_id="policy-123",
                version_number="1.0",
                effective_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                created_by="admin",
                coverage_amount=500000.0,
                premium=15000.0,
                exclusions_count=2,
                inclusions_count=3,
                changes_from_previous=[],
                document_snapshot="Text v1",
                is_current=False,
            ),
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_versions
        versioning_service.db_session.execute = AsyncMock(return_value=mock_result)
        
        history = await versioning_service.get_version_history("policy-123")
        
        assert history.policy_id == "policy-123"
        assert len(history.versions) == 2
        assert history.versions[0].version_number == "2.0"
        assert history.versions[1].version_number == "1.0"
        
        # Test getting current version
        current = history.get_current_version()
        assert current is not None
        assert current.version_number == "2.0"


class TestPolicyVersionChange:
    """Tests for PolicyVersionChange model."""
    
    def test_affects_analyses_critical(self):
        """Test that critical changes affect analyses."""
        change = PolicyVersionChange(
            change_type=VersionChangeType.EXCLUSION_ADDED,
            field_name="exclusions",
            old_value=None,
            new_value="New exclusion",
            description="Added exclusion",
            impact_level="critical",
        )
        
        assert change.affects_analyses() is True
    
    def test_affects_analyses_high(self):
        """Test that high impact changes affect analyses."""
        change = PolicyVersionChange(
            change_type=VersionChangeType.PREMIUM_CHANGE,
            field_name="premium",
            old_value="Rs. 10,000",
            new_value="Rs. 15,000",
            description="Premium increased",
            impact_level="high",
        )
        
        assert change.affects_analyses() is True
    
    def test_does_not_affect_analyses_low(self):
        """Test that low impact changes don't affect analyses."""
        change = PolicyVersionChange(
            change_type=VersionChangeType.MINOR_UPDATE,
            field_name="text",
            old_value="Old",
            new_value="New",
            description="Minor update",
            impact_level="low",
        )
        
        assert change.affects_analyses() is False
