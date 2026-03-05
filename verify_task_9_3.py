"""
Verification script for Task 9.3: Complaint Guidance Generator

This script tests the generate_complaint_guidance method of the OmbudsmanAdvisor service.
"""

from healthcare_insurance_platform.services.ombudsman_advisor import OmbudsmanAdvisor


def test_complaint_guidance_basic():
    """Test basic complaint guidance generation."""
    print("=" * 80)
    print("TEST 1: Basic Complaint Guidance Generation")
    print("=" * 80)
    
    advisor = OmbudsmanAdvisor()
    
    # Test data
    claim_id = "CLM-2024-001"
    claim_details = {
        "claim_type": "hospitalization",
        "claim_amount": 150000,
        "treatment": "Cardiac surgery",
        "hospital": "Apollo Hospital",
        "admission_date": "2024-01-15",
        "discharge_date": "2024-01-20"
    }
    rejection_reason = "Pre-existing disease not disclosed"
    policy_id = "POL-HDFC-001"
    
    # Generate complaint guidance
    guide = advisor.generate_complaint_guidance(
        claim_id=claim_id,
        claim_details=claim_details,
        rejection_reason=rejection_reason,
        policy_id=policy_id,
        language="en"
    )
    
    # Verify the guide
    print(f"\n✓ Guide ID: {guide.guide_id}")
    print(f"✓ Claim ID: {guide.claim_id}")
    print(f"✓ Language: {guide.language}")
    
    # Check filing process
    print(f"\n✓ Filing Process Steps: {len(guide.filing_process)}")
    assert len(guide.filing_process) > 0, "Filing process should not be empty"
    print("  Sample steps:")
    for i, step in enumerate(guide.filing_process[:3], 1):
        print(f"    {i}. {step}")
    
    # Check required documents
    print(f"\n✓ Required Documents: {len(guide.required_documents)}")
    assert len(guide.required_documents) > 0, "Required documents should not be empty"
    print("  Sample documents:")
    for i, doc in enumerate(guide.required_documents[:3], 1):
        print(f"    {i}. {doc}")
    
    # Check argument points
    print(f"\n✓ Argument Points: {len(guide.argument_points)}")
    assert len(guide.argument_points) > 0, "Argument points should not be empty"
    print("  Sample arguments:")
    for i, arg in enumerate(guide.argument_points[:3], 1):
        print(f"    {i}. {arg}")
    
    # Check timeline
    print(f"\n✓ Expected Timeline: {guide.expected_timeline[:100]}...")
    assert len(guide.expected_timeline) > 0, "Timeline should not be empty"
    
    # Check deadlines
    print(f"\n✓ Important Deadlines: {len(guide.important_deadlines)}")
    assert len(guide.important_deadlines) > 0, "Deadlines should not be empty"
    for i, deadline in enumerate(guide.important_deadlines, 1):
        print(f"    {i}. {deadline}")
    
    # Check tips and warnings
    print(f"\n✓ Tips and Warnings: {len(guide.tips_and_warnings)}")
    assert len(guide.tips_and_warnings) > 0, "Tips should not be empty"
    print("  Sample tips:")
    for i, tip in enumerate(guide.tips_and_warnings[:3], 1):
        print(f"    {i}. {tip}")
    
    # Check explanation
    print(f"\n✓ Explanation: {guide.explanation[:150]}...")
    assert len(guide.explanation) > 0, "Explanation should not be empty"
    
    # Check citations
    print(f"\n✓ Citations: {len(guide.citations)}")
    assert len(guide.citations) > 0, "Citations should not be empty"
    for i, citation in enumerate(guide.citations, 1):
        print(f"    {i}. {citation}")
    
    print("\n✅ TEST 1 PASSED: Basic complaint guidance generation works correctly")
    return guide


def test_complaint_guidance_ped_rejection():
    """Test complaint guidance for PED-related rejection."""
    print("\n" + "=" * 80)
    print("TEST 2: Complaint Guidance for PED Rejection")
    print("=" * 80)
    
    advisor = OmbudsmanAdvisor()
    
    claim_details = {
        "claim_type": "hospitalization",
        "claim_amount": 200000,
        "treatment": "Diabetes complications",
        "condition": "Type 2 Diabetes"
    }
    rejection_reason = "Pre-existing disease - diabetes not disclosed during policy purchase"
    
    guide = advisor.generate_complaint_guidance(
        claim_id="CLM-2024-002",
        claim_details=claim_details,
        rejection_reason=rejection_reason,
        policy_id="POL-ICICI-002"
    )
    
    # Verify PED-specific argument points
    ped_arguments = [arg for arg in guide.argument_points if "pre-existing" in arg.lower() or "disclosed" in arg.lower()]
    print(f"\n✓ PED-specific argument points found: {len(ped_arguments)}")
    assert len(ped_arguments) > 0, "Should have PED-specific arguments"
    
    for arg in ped_arguments:
        print(f"  - {arg}")
    
    print("\n✅ TEST 2 PASSED: PED-specific guidance generated correctly")


def test_complaint_guidance_waiting_period():
    """Test complaint guidance for waiting period rejection."""
    print("\n" + "=" * 80)
    print("TEST 3: Complaint Guidance for Waiting Period Rejection")
    print("=" * 80)
    
    advisor = OmbudsmanAdvisor()
    
    claim_details = {
        "claim_type": "surgery",
        "claim_amount": 180000,
        "treatment": "Knee replacement surgery"
    }
    rejection_reason = "Claim filed during waiting period for joint replacement procedures"
    
    guide = advisor.generate_complaint_guidance(
        claim_id="CLM-2024-003",
        claim_details=claim_details,
        rejection_reason=rejection_reason,
        policy_id="POL-SBI-003"
    )
    
    # Verify waiting period-specific argument points
    waiting_arguments = [arg for arg in guide.argument_points if "waiting period" in arg.lower()]
    print(f"\n✓ Waiting period-specific argument points found: {len(waiting_arguments)}")
    assert len(waiting_arguments) > 0, "Should have waiting period-specific arguments"
    
    for arg in waiting_arguments:
        print(f"  - {arg}")
    
    print("\n✅ TEST 3 PASSED: Waiting period-specific guidance generated correctly")


def test_complaint_guidance_exclusion():
    """Test complaint guidance for exclusion-based rejection."""
    print("\n" + "=" * 80)
    print("TEST 4: Complaint Guidance for Exclusion Rejection")
    print("=" * 80)
    
    advisor = OmbudsmanAdvisor()
    
    claim_details = {
        "claim_type": "treatment",
        "claim_amount": 50000,
        "treatment": "Cosmetic procedure"
    }
    rejection_reason = "Treatment falls under policy exclusions - cosmetic procedures not covered"
    
    guide = advisor.generate_complaint_guidance(
        claim_id="CLM-2024-004",
        claim_details=claim_details,
        rejection_reason=rejection_reason,
        policy_id="POL-MAX-004"
    )
    
    # Verify exclusion-specific argument points
    exclusion_arguments = [arg for arg in guide.argument_points if "exclusion" in arg.lower()]
    print(f"\n✓ Exclusion-specific argument points found: {len(exclusion_arguments)}")
    assert len(exclusion_arguments) > 0, "Should have exclusion-specific arguments"
    
    for arg in exclusion_arguments:
        print(f"  - {arg}")
    
    print("\n✅ TEST 4 PASSED: Exclusion-specific guidance generated correctly")


def test_complaint_guidance_documentation():
    """Test complaint guidance for documentation-related rejection."""
    print("\n" + "=" * 80)
    print("TEST 5: Complaint Guidance for Documentation Rejection")
    print("=" * 80)
    
    advisor = OmbudsmanAdvisor()
    
    claim_details = {
        "claim_type": "hospitalization",
        "claim_amount": 120000,
        "treatment": "Emergency surgery"
    }
    rejection_reason = "Incomplete documentation - missing discharge summary and medical bills"
    
    guide = advisor.generate_complaint_guidance(
        claim_id="CLM-2024-005",
        claim_details=claim_details,
        rejection_reason=rejection_reason,
        policy_id="POL-STAR-005"
    )
    
    # Verify documentation-specific argument points
    doc_arguments = [arg for arg in guide.argument_points if "document" in arg.lower()]
    print(f"\n✓ Documentation-specific argument points found: {len(doc_arguments)}")
    assert len(doc_arguments) > 0, "Should have documentation-specific arguments"
    
    for arg in doc_arguments:
        print(f"  - {arg}")
    
    print("\n✅ TEST 5 PASSED: Documentation-specific guidance generated correctly")


def test_complaint_guide_completeness():
    """Test that complaint guide contains all required fields per Requirement 7.5."""
    print("\n" + "=" * 80)
    print("TEST 6: Complaint Guide Completeness (Requirement 7.5)")
    print("=" * 80)
    
    advisor = OmbudsmanAdvisor()
    
    guide = advisor.generate_complaint_guidance(
        claim_id="CLM-TEST",
        claim_details={"claim_type": "test", "claim_amount": 100000},
        rejection_reason="Test rejection",
        policy_id="POL-TEST"
    )
    
    # Requirement 7.5: Generate filing process instructions
    print("\n✓ Checking filing process instructions...")
    assert hasattr(guide, 'filing_process'), "Guide must have filing_process"
    assert len(guide.filing_process) > 0, "Filing process must not be empty"
    assert isinstance(guide.filing_process, list), "Filing process must be a list"
    print(f"  ✓ Filing process has {len(guide.filing_process)} steps")
    
    # Requirement 7.5: List required documentation
    print("\n✓ Checking required documentation...")
    assert hasattr(guide, 'required_documents'), "Guide must have required_documents"
    assert len(guide.required_documents) > 0, "Required documents must not be empty"
    assert isinstance(guide.required_documents, list), "Required documents must be a list"
    print(f"  ✓ Required documents list has {len(guide.required_documents)} items")
    
    # Requirement 7.5: Provide timeline and next steps
    print("\n✓ Checking timeline and next steps...")
    assert hasattr(guide, 'expected_timeline'), "Guide must have expected_timeline"
    assert len(guide.expected_timeline) > 0, "Timeline must not be empty"
    assert hasattr(guide, 'important_deadlines'), "Guide must have important_deadlines"
    assert len(guide.important_deadlines) > 0, "Deadlines must not be empty"
    print(f"  ✓ Timeline provided: {guide.expected_timeline[:80]}...")
    print(f"  ✓ Important deadlines: {len(guide.important_deadlines)} items")
    
    # Additional checks for completeness
    print("\n✓ Checking additional guidance fields...")
    assert hasattr(guide, 'argument_points'), "Guide must have argument_points"
    assert hasattr(guide, 'tips_and_warnings'), "Guide must have tips_and_warnings"
    assert hasattr(guide, 'explanation'), "Guide must have explanation"
    assert hasattr(guide, 'citations'), "Guide must have citations"
    print(f"  ✓ Argument points: {len(guide.argument_points)} items")
    print(f"  ✓ Tips and warnings: {len(guide.tips_and_warnings)} items")
    print(f"  ✓ Explanation length: {len(guide.explanation)} characters")
    print(f"  ✓ Citations: {len(guide.citations)} items")
    
    print("\n✅ TEST 6 PASSED: Complaint guide meets all Requirement 7.5 criteria")


def main():
    """Run all verification tests."""
    print("\n" + "=" * 80)
    print("TASK 9.3 VERIFICATION: Complaint Guidance Generator")
    print("=" * 80)
    print("\nThis script verifies that the generate_complaint_guidance method")
    print("generates comprehensive guidance for filing complaints with the")
    print("Insurance Ombudsman, including:")
    print("  - Filing process instructions")
    print("  - Required documentation")
    print("  - Timeline and next steps")
    print("  - Argument points based on rejection reason")
    print("\nValidates: Requirement 7.5")
    print("=" * 80)
    
    try:
        # Run all tests
        test_complaint_guidance_basic()
        test_complaint_guidance_ped_rejection()
        test_complaint_guidance_waiting_period()
        test_complaint_guidance_exclusion()
        test_complaint_guidance_documentation()
        test_complaint_guide_completeness()
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\nTask 9.3 Implementation Summary:")
        print("✓ Complaint guidance generator implemented successfully")
        print("✓ Generates filing process instructions")
        print("✓ Lists required documentation")
        print("✓ Provides timeline and important deadlines")
        print("✓ Generates context-specific argument points")
        print("✓ Includes tips, warnings, and explanations")
        print("✓ Provides proper citations")
        print("\n✅ Requirement 7.5 validated successfully")
        print("=" * 80)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
