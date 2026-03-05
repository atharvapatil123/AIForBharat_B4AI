"""
Example usage of the Ombudsman Advisor eligibility checker.

This example demonstrates how to check eligibility for filing complaints
with the Insurance Ombudsman, including jurisdiction validation, deadline
calculation, and regional office identification.
"""

from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from healthcare_insurance_platform.services.ombudsman_advisor import OmbudsmanAdvisor


def example_1_eligible_claim():
    """Example 1: Eligible claim - all criteria met."""
    print("=" * 70)
    print("Example 1: Eligible Claim")
    print("=" * 70)
    
    advisor = OmbudsmanAdvisor()
    
    # Claim rejected 2 months ago, amount within limit
    rejection_date = (datetime.now() - timedelta(days=60)).date().isoformat()
    
    result = advisor.check_eligibility(
        claim_amount=1500000.0,  # ₹15 lakh
        rejection_date=rejection_date,
        user_location="Mumbai",
        claim_id="CLM-2024-001"
    )
    
    print(f"\nClaim ID: {result.claim_id}")
    print(f"Claim Amount: ₹{result.claim_amount:,.2f}")
    print(f"User Location: {result.user_location}")
    print(f"\n{'='*70}")
    print(f"ELIGIBILITY: {'✓ ELIGIBLE' if result.is_eligible else '✗ NOT ELIGIBLE'}")
    print(f"{'='*70}")
    
    print(f"\nJurisdiction Check:")
    print(f"  Within ₹20 lakh limit: {result.within_jurisdiction}")
    print(f"  Jurisdiction limit: ₹{result.jurisdiction_limit:,.2f}")
    
    print(f"\nDeadline Check:")
    print(f"  Rejection date: {result.rejection_date}")
    print(f"  Filing deadline: {result.filing_deadline}")
    print(f"  Days remaining: {result.days_remaining}")
    print(f"  Within deadline: {result.within_deadline}")
    
    if result.regional_office:
        print(f"\nRegional Office:")
        print(f"  Name: {result.regional_office['name']}")
        print(f"  Region: {result.regional_office['region']}")
        print(f"  Address: {result.regional_office['address']}")
        print(f"  Phone: {result.regional_office['contact_phone']}")
        print(f"  Email: {result.regional_office['contact_email']}")
    
    print(f"\nEligibility Reasons:")
    for i, reason in enumerate(result.eligibility_reasons, 1):
        print(f"  {i}. {reason}")
    
    print(f"\nExplanation:")
    print(f"  {result.explanation}")
    
    print(f"\nNext Steps:")
    for i, step in enumerate(result.next_steps, 1):
        print(f"  {i}. {step}")
    
    print()


def example_2_amount_exceeds_limit():
    """Example 2: Ineligible - claim amount exceeds ₹20 lakh."""
    print("\n" + "=" * 70)
    print("Example 2: Claim Amount Exceeds Jurisdiction Limit")
    print("=" * 70)
    
    advisor = OmbudsmanAdvisor()
    
    rejection_date = (datetime.now() - timedelta(days=30)).date().isoformat()
    
    result = advisor.check_eligibility(
        claim_amount=2500000.0,  # ₹25 lakh - exceeds limit
        rejection_date=rejection_date,
        user_location="Bangalore",
        claim_id="CLM-2024-002"
    )
    
    print(f"\nClaim Amount: ₹{result.claim_amount:,.2f}")
    print(f"\n{'='*70}")
    print(f"ELIGIBILITY: {'✓ ELIGIBLE' if result.is_eligible else '✗ NOT ELIGIBLE'}")
    print(f"{'='*70}")
    
    print(f"\nJurisdiction Check:")
    print(f"  Within ₹20 lakh limit: {result.within_jurisdiction}")
    print(f"  Amount exceeds limit by: ₹{result.claim_amount - result.jurisdiction_limit:,.2f}")
    
    print(f"\nExplanation:")
    print(f"  {result.explanation}")
    
    print(f"\nNext Steps:")
    for i, step in enumerate(result.next_steps, 1):
        print(f"  {i}. {step}")
    
    print()


def example_3_deadline_passed():
    """Example 3: Ineligible - filing deadline has passed."""
    print("\n" + "=" * 70)
    print("Example 3: Filing Deadline Has Passed")
    print("=" * 70)
    
    advisor = OmbudsmanAdvisor()
    
    # Claim rejected 14 months ago - past the 1-year deadline
    rejection_date = (datetime.now() - timedelta(days=420)).date().isoformat()
    
    result = advisor.check_eligibility(
        claim_amount=1000000.0,  # ₹10 lakh
        rejection_date=rejection_date,
        user_location="Chennai",
        claim_id="CLM-2023-003"
    )
    
    print(f"\nClaim Amount: ₹{result.claim_amount:,.2f}")
    print(f"\n{'='*70}")
    print(f"ELIGIBILITY: {'✓ ELIGIBLE' if result.is_eligible else '✗ NOT ELIGIBLE'}")
    print(f"{'='*70}")
    
    print(f"\nDeadline Check:")
    print(f"  Rejection date: {result.rejection_date}")
    print(f"  Filing deadline: {result.filing_deadline}")
    print(f"  Days overdue: {abs(result.days_remaining)}")
    print(f"  Within deadline: {result.within_deadline}")
    
    print(f"\nExplanation:")
    print(f"  {result.explanation}")
    
    print(f"\nNext Steps:")
    for i, step in enumerate(result.next_steps, 1):
        print(f"  {i}. {step}")
    
    print()


def example_4_urgent_deadline():
    """Example 4: Eligible but urgent - deadline approaching."""
    print("\n" + "=" * 70)
    print("Example 4: Urgent - Deadline Approaching")
    print("=" * 70)
    
    advisor = OmbudsmanAdvisor()
    
    # Claim rejected 11 months ago - only ~1 month remaining
    rejection_date = (datetime.now() - timedelta(days=340)).date().isoformat()
    
    result = advisor.check_eligibility(
        claim_amount=800000.0,  # ₹8 lakh
        rejection_date=rejection_date,
        user_location="Delhi",
        claim_id="CLM-2024-004"
    )
    
    print(f"\nClaim Amount: ₹{result.claim_amount:,.2f}")
    print(f"\n{'='*70}")
    print(f"ELIGIBILITY: {'✓ ELIGIBLE' if result.is_eligible else '✗ NOT ELIGIBLE'}")
    if result.is_urgent():
        print(f"⚠️  URGENT: Deadline approaching!")
    print(f"{'='*70}")
    
    print(f"\nDeadline Check:")
    print(f"  Rejection date: {result.rejection_date}")
    print(f"  Filing deadline: {result.filing_deadline}")
    print(f"  Days remaining: {result.days_remaining}")
    print(f"  Is urgent (< 30 days): {result.is_urgent()}")
    
    print(f"\nExplanation:")
    print(f"  {result.explanation}")
    
    print(f"\nNext Steps:")
    for i, step in enumerate(result.next_steps, 1):
        print(f"  {i}. {step}")
    
    print()


def example_5_multiple_locations():
    """Example 5: Check eligibility for different locations."""
    print("\n" + "=" * 70)
    print("Example 5: Regional Office Routing for Different Locations")
    print("=" * 70)
    
    advisor = OmbudsmanAdvisor()
    
    locations = [
        "Mumbai",
        "Bangalore",
        "Chennai",
        "Delhi",
        "Kolkata",
        "Hyderabad",
        "Pune",
        "Ahmedabad"
    ]
    
    rejection_date = (datetime.now() - timedelta(days=60)).date().isoformat()
    
    print(f"\nClaim: ₹12 lakh, Rejected 60 days ago\n")
    print(f"{'Location':<15} {'Regional Office':<30} {'Contact'}")
    print("-" * 70)
    
    for location in locations:
        result = advisor.check_eligibility(
            claim_amount=1200000.0,
            rejection_date=rejection_date,
            user_location=location
        )
        
        if result.regional_office:
            office_name = result.regional_office['region']
            contact = result.regional_office['contact_phone']
            print(f"{location:<15} {office_name:<30} {contact}")
    
    print()


def example_6_complaint_guidance():
    """Example 6: Generate complaint filing guidance."""
    print("\n" + "=" * 70)
    print("Example 6: Complaint Filing Guidance")
    print("=" * 70)
    
    advisor = OmbudsmanAdvisor()
    
    claim_details = {
        "claim_type": "hospitalization",
        "treatment": "Cardiac surgery",
        "hospital": "Apollo Hospital",
        "amount": 1500000.0
    }
    
    guide = advisor.generate_complaint_guidance(
        claim_id="CLM-2024-005",
        claim_details=claim_details,
        rejection_reason="Pre-existing disease exclusion",
        policy_id="POL-2024-001"
    )
    
    print(f"\nClaim ID: {guide.claim_id}")
    print(f"\nFiling Process:")
    for i, step in enumerate(guide.filing_process, 1):
        print(f"  {i}. {step}")
    
    print(f"\nRequired Documents:")
    for i, doc in enumerate(guide.required_documents, 1):
        print(f"  {i}. {doc}")
    
    print(f"\nArgument Points:")
    for i, point in enumerate(guide.argument_points, 1):
        print(f"  {i}. {point}")
    
    print(f"\nExpected Timeline:")
    print(f"  {guide.expected_timeline}")
    
    print(f"\nTips and Warnings:")
    for i, tip in enumerate(guide.tips_and_warnings[:5], 1):  # Show first 5
        print(f"  {i}. {tip}")
    
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("OMBUDSMAN ADVISOR - ELIGIBILITY CHECKER EXAMPLES")
    print("=" * 70)
    print("\nThese examples demonstrate the Ombudsman Advisor service")
    print("for checking eligibility to file complaints with the")
    print("Insurance Ombudsman in India.")
    print()
    
    try:
        example_1_eligible_claim()
        example_2_amount_exceeds_limit()
        example_3_deadline_passed()
        example_4_urgent_deadline()
        example_5_multiple_locations()
        example_6_complaint_guidance()
        
        print("=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)
        print()
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
