"""Integration test demonstrating policy versioning with Knowledge Base."""

from datetime import date
from pathlib import Path

from healthcare_insurance_platform.models.policy import (
    PolicyDocument,
    WaitingPeriod,
    DocumentRequirement,
    ParsedClause,
)


def test_versioning_workflow():
    """
    Demonstrate the complete versioning workflow.
    
    This test shows how:
    1. A policy is ingested with version 1.0
    2. An updated policy is ingested with version 2.0
    3. Changes are detected and tracked
    4. Version comparison is performed
    5. Affected analyses are flagged
    """
    print("\n=== Policy Versioning Workflow Demo ===\n")
    
    # Step 1: Create initial policy version
    print("Step 1: Creating initial policy version 1.0")
    policy_v1 = PolicyDocument(
        policy_id="health-plus-001",
        provider_id="star-health",
        policy_name="Star Health Plus",
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
            "Hospitalization expenses",
            "Surgical procedures",
            "Diagnostic tests",
            "Ambulance charges",
        ],
        exclusions=[
            "Cosmetic surgery",
            "Dental treatment (except accident)",
            "Infertility treatment",
        ],
        ped_policy="Pre-existing diseases covered after 24 months waiting period",
        claim_process="Submit claim within 30 days of discharge with all documents",
        document_requirements=[
            DocumentRequirement(
                claim_type="hospitalization",
                documents=[
                    "Hospital discharge summary",
                    "Medical bills and receipts",
                    "Diagnostic reports",
                    "Doctor's prescription",
                ],
            ),
        ],
        full_text="[Full policy document text for version 1.0]",
        parsed_clauses=[
            ParsedClause(
                clause_type="coverage",
                text="Maximum coverage: Rs. 5,00,000 per policy year",
                importance="critical",
            ),
        ],
    )
    
    print(f"  ✓ Policy ID: {policy_v1.policy_id}")
    print(f"  ✓ Version: {policy_v1.version}")
    print(f"  ✓ Coverage: Rs. {policy_v1.coverage_amount:,.0f}")
    print(f"  ✓ Premium: Rs. {policy_v1.premium:,.0f}")
    print(f"  ✓ Inclusions: {len(policy_v1.inclusions)}")
    print(f"  ✓ Exclusions: {len(policy_v1.exclusions)}")
    
    # Step 2: Create updated policy version
    print("\nStep 2: Creating updated policy version 2.0 with changes")
    policy_v2 = PolicyDocument(
        policy_id="health-plus-001",
        provider_id="star-health",
        policy_name="Star Health Plus",
        policy_type="individual",
        version="2.0",
        effective_date=date(2024, 7, 1),
        coverage_amount=750000.0,  # Increased by 50%
        premium=18500.0,  # Increased by 23.3%
        waiting_periods=WaitingPeriod(
            general=30,
            pre_existing=730,
            specific_conditions=[],
        ),
        inclusions=[
            "Hospitalization expenses",
            "Surgical procedures",
            "Diagnostic tests",
            "Ambulance charges",
            "Maternity coverage",  # NEW
            "Mental health treatment",  # NEW
        ],
        exclusions=[
            "Cosmetic surgery",
            "Dental treatment (except accident)",
            "Infertility treatment",
            "Alternative medicine (Ayurveda, Homeopathy)",  # NEW
        ],
        ped_policy="Pre-existing diseases covered after 24 months waiting period",
        claim_process="Submit claim within 30 days of discharge with all documents",
        document_requirements=[
            DocumentRequirement(
                claim_type="hospitalization",
                documents=[
                    "Hospital discharge summary",
                    "Medical bills and receipts",
                    "Diagnostic reports",
                    "Doctor's prescription",
                ],
            ),
        ],
        full_text="[Full policy document text for version 2.0]",
        parsed_clauses=[
            ParsedClause(
                clause_type="coverage",
                text="Maximum coverage: Rs. 7,50,000 per policy year",
                importance="critical",
            ),
        ],
    )
    
    print(f"  ✓ Version: {policy_v2.version}")
    print(f"  ✓ Coverage: Rs. {policy_v2.coverage_amount:,.0f} (↑ 50%)")
    print(f"  ✓ Premium: Rs. {policy_v2.premium:,.0f} (↑ 23.3%)")
    print(f"  ✓ Inclusions: {len(policy_v2.inclusions)} (added 2)")
    print(f"  ✓ Exclusions: {len(policy_v2.exclusions)} (added 1)")
    
    # Step 3: Detect changes
    print("\nStep 3: Detecting changes between versions")
    from healthcare_insurance_platform.services.policy_versioning import PolicyVersioningService
    
    versioning_service = PolicyVersioningService(db_session=None)
    changes = versioning_service._detect_changes(policy_v1, policy_v2)
    
    print(f"  ✓ Total changes detected: {len(changes)}")
    
    # Categorize changes by impact
    critical_changes = [c for c in changes if c.impact_level == 'critical']
    high_changes = [c for c in changes if c.impact_level == 'high']
    medium_changes = [c for c in changes if c.impact_level == 'medium']
    
    print(f"  ✓ Critical changes: {len(critical_changes)}")
    print(f"  ✓ High impact changes: {len(high_changes)}")
    print(f"  ✓ Medium impact changes: {len(medium_changes)}")
    
    # Step 4: Display detailed changes
    print("\nStep 4: Detailed change breakdown")
    
    for i, change in enumerate(changes, 1):
        print(f"\n  Change {i}: {change.change_type.value}")
        print(f"    Field: {change.field_name}")
        print(f"    Impact: {change.impact_level.upper()}")
        print(f"    Description: {change.description}")
        if change.old_value and len(change.old_value) < 100:
            print(f"    Old: {change.old_value}")
        if change.new_value and len(change.new_value) < 100:
            print(f"    New: {change.new_value}")
        print(f"    Affects analyses: {change.affects_analyses()}")
    
    # Step 5: Generate comparison summary
    print("\nStep 5: Generating comparison summary")
    summary = versioning_service._generate_comparison_summary(changes)
    print(f"\n{summary}")
    
    # Step 6: Identify affected analyses
    print("\nStep 6: Identifying affected analyses")
    affecting_changes = [c for c in changes if c.affects_analyses()]
    print(f"  ✓ Changes that affect existing analyses: {len(affecting_changes)}")
    
    if affecting_changes:
        print("\n  These changes require re-analysis:")
        for change in affecting_changes:
            print(f"    • {change.description} ({change.impact_level})")
    
    # Step 7: Summary
    print("\n=== Versioning Workflow Summary ===")
    print(f"✓ Successfully tracked policy evolution from v1.0 to v2.0")
    print(f"✓ Detected {len(changes)} changes across multiple dimensions")
    print(f"✓ Identified {len(affecting_changes)} changes requiring user notification")
    print(f"✓ Version comparison and impact analysis complete")
    
    print("\n=== Key Benefits ===")
    print("• Users with old analyses will be notified of policy changes")
    print("• Critical changes (new exclusions) are flagged for immediate attention")
    print("• Positive changes (new coverage) are highlighted")
    print("• Complete audit trail of policy evolution maintained")
    print()
    
    # Assertions to verify correctness
    assert len(changes) > 0, "Should detect changes between versions"
    assert len(critical_changes) > 0, "Should have critical changes (exclusion added)"
    assert len(affecting_changes) > 0, "Should have changes affecting analyses"
    
    # Verify specific changes
    change_types = {c.change_type for c in changes}
    assert "coverage_change" in [ct.value for ct in change_types], "Should detect coverage change"
    assert "premium_change" in [ct.value for ct in change_types], "Should detect premium change"
    assert "inclusion_added" in [ct.value for ct in change_types], "Should detect new inclusions"
    assert "exclusion_added" in [ct.value for ct in change_types], "Should detect new exclusions"
    
    print("✅ All assertions passed - versioning system working correctly!\n")


if __name__ == "__main__":
    test_versioning_workflow()
