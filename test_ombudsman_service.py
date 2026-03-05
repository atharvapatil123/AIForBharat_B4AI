"""
Direct test of the Ombudsman Advisor service without going through __init__.py
"""

from datetime import datetime, timedelta
import sys
import os

# Direct imports to avoid __init__.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the service module directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "ombudsman_advisor",
    "healthcare_insurance_platform/services/ombudsman_advisor.py"
)
ombudsman_module = importlib.util.module_from_spec(spec)

# We need to set up the dependencies first
from healthcare_insurance_platform.db.ombudsman_offices import ombudsman_db
from healthcare_insurance_platform.models.ombudsman import OmbudsmanOffice
from healthcare_insurance_platform.models.results import EligibilityResult, ComplaintGuide

# Add to sys.modules so imports work
sys.modules['healthcare_insurance_platform.db.ombudsman_offices'] = sys.modules['__main__']
sys.modules['healthcare_insurance_platform.models.ombudsman'] = sys.modules['__main__']
sys.modules['healthcare_insurance_platform.models.results'] = sys.modules['__main__']

# Now load the module
spec.loader.exec_module(ombudsman_module)
OmbudsmanAdvisor = ombudsman_module.OmbudsmanAdvisor


def test_service():
    """Test the Ombudsman Advisor service."""
    print("=" * 70)
    print("Testing Ombudsman Advisor Service")
    print("=" * 70)
    
    advisor = OmbudsmanAdvisor()
    
    # Test 1: Eligible claim
    print("\nTest 1: Eligible claim")
    rejection_date = (datetime.now() - timedelta(days=60)).date().isoformat()
    result = advisor.check_eligibility(
        claim_amount=1500000.0,
        rejection_date=rejection_date,
        user_location="Mumbai",
        claim_id="CLM-001"
    )
    
    print(f"  Is eligible: {result.is_eligible}")
    print(f"  Within jurisdiction: {result.within_jurisdiction}")
    print(f"  Within deadline: {result.within_deadline}")
    print(f"  Office: {result.get_office_name()}")
    print(f"  Days remaining: {result.days_remaining}")
    assert result.is_eligible == True
    
    # Test 2: Amount exceeds limit
    print("\nTest 2: Amount exceeds limit")
    result = advisor.check_eligibility(
        claim_amount=2500000.0,
        rejection_date=rejection_date,
        user_location="Mumbai"
    )
    print(f"  Is eligible: {result.is_eligible}")
    print(f"  Within jurisdiction: {result.within_jurisdiction}")
    assert result.is_eligible == False
    assert result.within_jurisdiction == False
    
    # Test 3: Deadline passed
    print("\nTest 3: Deadline passed")
    old_date = (datetime.now() - timedelta(days=400)).date().isoformat()
    result = advisor.check_eligibility(
        claim_amount=1500000.0,
        rejection_date=old_date,
        user_location="Mumbai"
    )
    print(f"  Is eligible: {result.is_eligible}")
    print(f"  Within deadline: {result.within_deadline}")
    print(f"  Days overdue: {abs(result.days_remaining)}")
    assert result.is_eligible == False
    assert result.within_deadline == False
    
    # Test 4: Complaint guidance
    print("\nTest 4: Generate complaint guidance")
    guide = advisor.generate_complaint_guidance(
        claim_id="CLM-001",
        claim_details={"claim_type": "hospitalization"},
        rejection_reason="Pre-existing disease",
        policy_id="POL-001"
    )
    print(f"  Guide ID: {guide.guide_id}")
    print(f"  Filing steps: {len(guide.filing_process)}")
    print(f"  Required docs: {len(guide.required_documents)}")
    print(f"  Argument points: {len(guide.argument_points)}")
    assert len(guide.filing_process) > 0
    assert len(guide.required_documents) > 0
    
    print("\n✓ All service tests passed!")


if __name__ == "__main__":
    test_service()
