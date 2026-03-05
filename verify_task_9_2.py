"""
Verification script for Task 9.2: Ombudsman Advisor eligibility checker.

This script tests the eligibility checker implementation to ensure it:
1. Validates claim amount against ₹20 lakh limit
2. Calculates deadline from rejection date
3. Determines appropriate regional office
"""

from datetime import datetime, timedelta
from healthcare_insurance_platform.services.ombudsman_advisor import OmbudsmanAdvisor


def test_jurisdiction_validation():
    """Test claim amount validation against ₹20 lakh limit."""
    print("=" * 70)
    print("Test 1: Jurisdiction Validation (₹20 lakh limit)")
    print("=" * 70)
    
    advisor = OmbudsmanAdvisor()
    
    # Test case 1: Within jurisdiction (₹10 lakh)
    print("\nCase 1: Claim amount ₹10 lakh (within limit)")
    result = advisor.check_eligibility(
        claim_amount=1000000.0,
        rejection_date=None,
        user_location="Mumbai"
    )
    print(f"  Within jurisdiction: {result.within_jurisdiction}")
    print(f"  Claim amount: ₹{result.claim_amount:,.2f}")
    print(f"  Jurisdiction limit: ₹{result.jurisdiction_limit:,.2f}")
    assert result.within_jurisdiction == True, "Should be within jurisdiction"
    
    # Test case 2: At the limit (₹20 lakh exactly)
    print("\nCase 2: Claim amount ₹20 lakh (exactly at limit)")
    result = advisor.check_eligibility(
        claim_amount=2000000.0,
        rejection_date=None,
        user_location="Mumbai"
    )
    print(f"  Within jurisdiction: {result.within_jurisdiction}")
    print(f"  Claim amount: ₹{result.claim_amount:,.2f}")
    assert result.within_jurisdiction == True, "Should be within jurisdiction at exactly ₹20 lakh"
    
    # Test case 3: Exceeds jurisdiction (₹25 lakh)
    print("\nCase 3: Claim amount ₹25 lakh (exceeds limit)")
    result = advisor.check_eligibility(
        claim_amount=2500000.0,
        rejection_date=None,
        user_location="Mumbai"
    )
    print(f"  Within jurisdiction: {result.within_jurisdiction}")
    print(f"  Claim amount: ₹{result.claim_amount:,.2f}")
    assert result.within_jurisdiction == False, "Should exceed jurisdiction"
    
    print("\n✓ Jurisdiction validation tests passed!")


def test_deadline_calculation():
    """Test deadline calculation from rejection date."""
    print("\n" + "=" * 70)
    print("Test 2: Deadline Calculation (1 year from rejection)")
    print("=" * 70)
    
    advisor = OmbudsmanAdvisor()
    
    # Test case 1: Recent rejection (30 days ago)
    print("\nCase 1: Rejection 30 days ago")
    rejection_date = (datetime.now() - timedelta(days=30)).date().isoformat()
    result = advisor.check_eligibility(
        claim_amount=1000000.0,
        rejection_date=rejection_date,
        user_location="Mumbai"
    )
    print(f"  Rejection date: {result.rejection_date}")
    print(f"  Filing deadline: {result.filing_deadline}")
    print(f"  Days remaining: {result.days_remaining}")
    print(f"  Within deadline: {result.within_deadline}")
    assert result.within_deadline == True, "Should be within deadline"
    assert result.days_remaining > 300, "Should have ~335 days remaining"
    
    # Test case 2: Rejection 11 months ago (still within deadline)
    print("\nCase 2: Rejection 11 months ago (330 days)")
    rejection_date = (datetime.now() - timedelta(days=330)).date().isoformat()
    result = advisor.check_eligibility(
        claim_amount=1000000.0,
        rejection_date=rejection_date,
        user_location="Mumbai"
    )
    print(f"  Days remaining: {result.days_remaining}")
    print(f"  Within deadline: {result.within_deadline}")
    assert result.within_deadline == True, "Should still be within deadline"
    assert result.days_remaining > 0 and result.days_remaining < 40, "Should have ~35 days remaining"
    
    # Test case 3: Rejection over 1 year ago (deadline passed)
    print("\nCase 3: Rejection 400 days ago (deadline passed)")
    rejection_date = (datetime.now() - timedelta(days=400)).date().isoformat()
    result = advisor.check_eligibility(
        claim_amount=1000000.0,
        rejection_date=rejection_date,
        user_location="Mumbai"
    )
    print(f"  Days remaining: {result.days_remaining}")
    print(f"  Within deadline: {result.within_deadline}")
    assert result.within_deadline == False, "Should be past deadline"
    assert result.days_remaining < 0, "Should have negative days remaining"
    
    # Test case 4: No rejection date (not yet rejected)
    print("\nCase 4: No rejection date provided")
    result = advisor.check_eligibility(
        claim_amount=1000000.0,
        rejection_date=None,
        user_location="Mumbai"
    )
    print(f"  Rejection date: {result.rejection_date}")
    print(f"  Days remaining: {result.days_remaining}")
    print(f"  Within deadline: {result.within_deadline}")
    assert result.within_deadline == True, "Should be within deadline when no rejection date"
    assert result.days_remaining is None, "Days remaining should be None"
    
    print("\n✓ Deadline calculation tests passed!")


def test_regional_office_routing():
    """Test regional office identification based on location."""
    print("\n" + "=" * 70)
    print("Test 3: Regional Office Routing")
    print("=" * 70)
    
    advisor = OmbudsmanAdvisor()
    
    # Test various locations
    test_locations = [
        ("Mumbai", "MUMBAI", "Maharashtra"),
        ("Bangalore", "BENGALURU", "Karnataka"),
        ("Chennai", "CHENNAI", "Tamil Nadu"),
        ("Delhi", "DELHI", "Delhi"),
        ("Kolkata", "KOLKATA", "West Bengal"),
        ("Hyderabad", "HYDERABAD", "Telangana"),
        ("Pune", "PUNE", "Maharashtra"),
        ("Gujarat", "AHMEDABAD", "Gujarat"),
        ("Tamil Nadu", "CHENNAI", "Tamil Nadu"),
    ]
    
    for location, expected_office_id, expected_jurisdiction in test_locations:
        print(f"\nTesting location: {location}")
        result = advisor.check_eligibility(
            claim_amount=1000000.0,
            rejection_date=None,
            user_location=location
        )
        
        if result.regional_office:
            print(f"  Office: {result.regional_office['name']}")
            print(f"  Region: {result.regional_office['region']}")
            print(f"  Jurisdiction: {', '.join(result.regional_office['jurisdiction'])}")
            assert result.regional_office['office_id'] == expected_office_id, \
                f"Expected office {expected_office_id}, got {result.regional_office['office_id']}"
            assert expected_jurisdiction in result.regional_office['jurisdiction'], \
                f"Expected {expected_jurisdiction} in jurisdiction"
        else:
            print(f"  ✗ No office found for {location}")
            raise AssertionError(f"Should find office for {location}")
    
    # Test unknown location
    print("\nTesting unknown location: Unknown City")
    result = advisor.check_eligibility(
        claim_amount=1000000.0,
        rejection_date=None,
        user_location="Unknown City"
    )
    print(f"  Office found: {result.regional_office is not None}")
    assert result.regional_office is None, "Should not find office for unknown location"
    
    print("\n✓ Regional office routing tests passed!")


def test_overall_eligibility():
    """Test overall eligibility determination."""
    print("\n" + "=" * 70)
    print("Test 4: Overall Eligibility Determination")
    print("=" * 70)
    
    advisor = OmbudsmanAdvisor()
    
    # Test case 1: Fully eligible
    print("\nCase 1: Fully eligible (all criteria met)")
    rejection_date = (datetime.now() - timedelta(days=30)).date().isoformat()
    result = advisor.check_eligibility(
        claim_amount=1500000.0,
        rejection_date=rejection_date,
        user_location="Mumbai"
    )
    print(f"  Is eligible: {result.is_eligible}")
    print(f"  Within jurisdiction: {result.within_jurisdiction}")
    print(f"  Within deadline: {result.within_deadline}")
    print(f"  Office found: {result.regional_office is not None}")
    print(f"  Explanation: {result.explanation[:100]}...")
    assert result.is_eligible == True, "Should be eligible"
    assert len(result.eligibility_reasons) >= 3, "Should have multiple eligibility reasons"
    assert len(result.next_steps) > 0, "Should have next steps"
    
    # Test case 2: Ineligible due to amount
    print("\nCase 2: Ineligible (amount exceeds limit)")
    result = advisor.check_eligibility(
        claim_amount=2500000.0,
        rejection_date=rejection_date,
        user_location="Mumbai"
    )
    print(f"  Is eligible: {result.is_eligible}")
    print(f"  Explanation: {result.explanation[:100]}...")
    assert result.is_eligible == False, "Should be ineligible due to amount"
    
    # Test case 3: Ineligible due to deadline
    print("\nCase 3: Ineligible (deadline passed)")
    old_rejection_date = (datetime.now() - timedelta(days=400)).date().isoformat()
    result = advisor.check_eligibility(
        claim_amount=1500000.0,
        rejection_date=old_rejection_date,
        user_location="Mumbai"
    )
    print(f"  Is eligible: {result.is_eligible}")
    print(f"  Explanation: {result.explanation[:100]}...")
    assert result.is_eligible == False, "Should be ineligible due to deadline"
    
    # Test case 4: Ineligible due to unknown location
    print("\nCase 4: Ineligible (unknown location)")
    result = advisor.check_eligibility(
        claim_amount=1500000.0,
        rejection_date=rejection_date,
        user_location="Unknown City"
    )
    print(f"  Is eligible: {result.is_eligible}")
    print(f"  Explanation: {result.explanation[:100]}...")
    assert result.is_eligible == False, "Should be ineligible due to unknown location"
    
    print("\n✓ Overall eligibility tests passed!")


def test_result_model_methods():
    """Test EligibilityResult model helper methods."""
    print("\n" + "=" * 70)
    print("Test 5: EligibilityResult Model Methods")
    print("=" * 70)
    
    advisor = OmbudsmanAdvisor()
    
    # Create a result with urgent deadline
    print("\nTesting urgent deadline detection")
    rejection_date = (datetime.now() - timedelta(days=350)).date().isoformat()
    result = advisor.check_eligibility(
        claim_amount=1500000.0,
        rejection_date=rejection_date,
        user_location="Mumbai"
    )
    
    print(f"  Days remaining: {result.days_remaining}")
    print(f"  Is urgent (< 30 days): {result.is_urgent()}")
    assert result.is_urgent() == True, "Should be urgent with < 30 days remaining"
    
    # Test office name extraction
    print("\nTesting office name extraction")
    office_name = result.get_office_name()
    print(f"  Office name: {office_name}")
    assert office_name is not None, "Should have office name"
    assert "Mumbai" in office_name, "Office name should contain Mumbai"
    
    # Test contact extraction
    print("\nTesting contact information extraction")
    contact = result.get_office_contact()
    print(f"  Phone: {contact['phone']}")
    print(f"  Email: {contact['email']}")
    assert contact is not None, "Should have contact info"
    assert contact['phone'] is not None, "Should have phone"
    assert contact['email'] is not None, "Should have email"
    
    print("\n✓ Model method tests passed!")


def main():
    """Run all verification tests."""
    print("\n" + "=" * 70)
    print("TASK 9.2 VERIFICATION: Ombudsman Advisor Eligibility Checker")
    print("=" * 70)
    
    try:
        test_jurisdiction_validation()
        test_deadline_calculation()
        test_regional_office_routing()
        test_overall_eligibility()
        test_result_model_methods()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nTask 9.2 implementation verified successfully:")
        print("  ✓ Validates claim amount against ₹20 lakh limit")
        print("  ✓ Calculates deadline from rejection date")
        print("  ✓ Determines appropriate regional office")
        print("  ✓ Provides comprehensive eligibility determination")
        print("  ✓ Includes explanations and next steps")
        print("\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
