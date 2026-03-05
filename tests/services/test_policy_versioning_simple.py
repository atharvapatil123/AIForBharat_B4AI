"""Simple unit tests for policy versioning logic without database dependencies."""

from datetime import date, datetime, timezone

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
)
from healthcare_insurance_platform.services.policy_versioning import PolicyVersioningService


def create_sample_policy_v1():
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


def create_sample_policy_v2():
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


def test_detect_coverage_change():
    """Test detection of coverage amount changes."""
    service = PolicyVersioningService(db_session=None)
    policy_v1 = create_sample_policy_v1()
    policy_v2 = create_sample_policy_v2()
    
    changes = service._detect_changes(policy_v1, policy_v2)
    
    coverage_changes = [
        c for c in changes
        if c.change_type == VersionChangeType.COVERAGE_CHANGE
    ]
    
    assert len(coverage_changes) == 1
    change = coverage_changes[0]
    assert change.field_name == "coverage_amount"
    assert "500,000" in change.old_value
    assert "750,000" in change.new_value
    assert change.impact_level == "critical"  # 50% increase
    print("✓ Coverage change detection works")


def test_detect_premium_change():
    """Test detection of premium changes."""
    service = PolicyVersioningService(db_session=None)
    policy_v1 = create_sample_policy_v1()
    policy_v2 = create_sample_policy_v2()
    
    changes = service._detect_changes(policy_v1, policy_v2)
    
    premium_changes = [
        c for c in changes
        if c.change_type == VersionChangeType.PREMIUM_CHANGE
    ]
    
    assert len(premium_changes) == 1
    change = premium_changes[0]
    assert change.field_name == "premium"
    assert "15,000" in change.old_value
    assert "18,000" in change.new_value
    assert change.impact_level == "medium"  # 20% increase (exactly at threshold, so medium)
    print("✓ Premium change detection works")


def test_detect_inclusion_added():
    """Test detection of new inclusions."""
    service = PolicyVersioningService(db_session=None)
    policy_v1 = create_sample_policy_v1()
    policy_v2 = create_sample_policy_v2()
    
    changes = service._detect_changes(policy_v1, policy_v2)
    
    inclusion_changes = [
        c for c in changes
        if c.change_type == VersionChangeType.INCLUSION_ADDED
    ]
    
    assert len(inclusion_changes) == 1
    change = inclusion_changes[0]
    assert "Maternity coverage" in change.new_value
    assert change.impact_level == "high"
    print("✓ Inclusion addition detection works")


def test_detect_exclusion_added():
    """Test detection of new exclusions."""
    service = PolicyVersioningService(db_session=None)
    policy_v1 = create_sample_policy_v1()
    policy_v2 = create_sample_policy_v2()
    
    changes = service._detect_changes(policy_v1, policy_v2)
    
    exclusion_changes = [
        c for c in changes
        if c.change_type == VersionChangeType.EXCLUSION_ADDED
    ]
    
    assert len(exclusion_changes) == 1
    change = exclusion_changes[0]
    assert "Alternative medicine" in change.new_value
    assert change.impact_level == "critical"  # Adding exclusions is critical
    print("✓ Exclusion addition detection works")


def test_no_changes_detected():
    """Test that no changes are detected for identical policies."""
    service = PolicyVersioningService(db_session=None)
    policy_v1 = create_sample_policy_v1()
    
    changes = service._detect_changes(policy_v1, policy_v1)
    
    assert len(changes) == 0
    print("✓ No false changes detected for identical policies")


def test_change_affects_analyses():
    """Test that critical and high impact changes affect analyses."""
    critical_change = PolicyVersionChange(
        change_type=VersionChangeType.EXCLUSION_ADDED,
        field_name="exclusions",
        old_value=None,
        new_value="New exclusion",
        description="Added exclusion",
        impact_level="critical",
    )
    
    high_change = PolicyVersionChange(
        change_type=VersionChangeType.PREMIUM_CHANGE,
        field_name="premium",
        old_value="Rs. 10,000",
        new_value="Rs. 15,000",
        description="Premium increased",
        impact_level="high",
    )
    
    low_change = PolicyVersionChange(
        change_type=VersionChangeType.MINOR_UPDATE,
        field_name="text",
        old_value="Old",
        new_value="New",
        description="Minor update",
        impact_level="low",
    )
    
    assert critical_change.affects_analyses() is True
    assert high_change.affects_analyses() is True
    assert low_change.affects_analyses() is False
    print("✓ Change impact assessment works correctly")


def test_generate_comparison_summary():
    """Test generating a comparison summary."""
    service = PolicyVersioningService(db_session=None)
    
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
    
    summary = service._generate_comparison_summary(changes)
    
    assert "Total changes: 2" in summary
    assert "1 critical changes" in summary
    assert "1 high impact changes" in summary
    assert "Coverage increased by 50%" in summary
    print("✓ Comparison summary generation works")


def test_policy_version_model():
    """Test PolicyVersion model functionality."""
    version = PolicyVersion(
        version_id="v1",
        policy_id="policy-123",
        version_number="1.0",
        effective_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        coverage_amount=500000.0,
        premium=15000.0,
        exclusions_count=2,
        inclusions_count=3,
        changes_from_previous=[
            PolicyVersionChange(
                change_type=VersionChangeType.COVERAGE_CHANGE,
                field_name="coverage_amount",
                old_value="Rs. 400,000",
                new_value="Rs. 500,000",
                description="Coverage increased",
                impact_level="critical",
            ),
            PolicyVersionChange(
                change_type=VersionChangeType.MINOR_UPDATE,
                field_name="text",
                old_value="Old",
                new_value="New",
                description="Minor update",
                impact_level="low",
            ),
        ],
    )
    
    assert version.has_critical_changes() is True
    assert version.has_high_impact_changes() is True
    
    coverage_changes = version.get_changes_by_type(VersionChangeType.COVERAGE_CHANGE)
    assert len(coverage_changes) == 1
    print("✓ PolicyVersion model methods work correctly")


if __name__ == "__main__":
    print("\nRunning policy versioning tests...\n")
    
    test_detect_coverage_change()
    test_detect_premium_change()
    test_detect_inclusion_added()
    test_detect_exclusion_added()
    test_no_changes_detected()
    test_change_affects_analyses()
    test_generate_comparison_summary()
    test_policy_version_model()
    
    print("\n✅ All tests passed!\n")
