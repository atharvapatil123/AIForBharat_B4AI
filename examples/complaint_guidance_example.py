"""
Example: Complaint Guidance Generator

This example demonstrates how to use the OmbudsmanAdvisor service to generate
comprehensive complaint filing guidance for rejected insurance claims.

Validates: Requirement 7.5
"""

from healthcare_insurance_platform.services.ombudsman_advisor import OmbudsmanAdvisor


def example_basic_complaint_guidance():
    """Example: Generate basic complaint guidance."""
    print("=" * 80)
    print("Example 1: Basic Complaint Guidance")
    print("=" * 80)
    
    advisor = OmbudsmanAdvisor()
    
    # Claim details
    claim_details = {
        "claim_type": "hospitalization",
        "claim_amount": 150000,
        "treatment": "Cardiac surgery",
        "hospital": "Apollo Hospital",
        "admission_date": "2024-01-15",
        "discharge_date": "2024-01-20"
    }
    
    # Generate complaint guidance
    guide = advisor.generate_complaint_guidance(
        claim_id="CLM-2024-001",
        claim_details=claim_details,
        rejection_reason="Pre-existing disease not disclosed",
        policy_id="POL-HDFC-001",
        language="en"
    )
    
    print(f"\nComplaint Guide Generated:")
    print(f"Guide ID: {guide.guide_id}")
    print(f"Claim ID: {guide.claim_id}")
    
    print(f"\n📋 Filing Process ({len(guide.filing_process)} steps):")
    for i, step in enumerate(guide.filing_process, 1):
        print(f"  {i}. {step}")
    
    print(f"\n📄 Required Documents ({len(guide.required_documents)} items):")
    for i, doc in enumerate(guide.required_documents, 1):
        print(f"  {i}. {doc}")
    
    print(f"\n💡 Argument Points ({len(guide.argument_points)} points):")
    for i, arg in enumerate(guide.argument_points, 1):
        print(f"  {i}. {arg}")
    
    print(f"\n⏰ Expected Timeline:")
    print(f"  {guide.expected_timeline}")
    
    print(f"\n⚠️ Important Deadlines:")
    for deadline in guide.important_deadlines:
        print(f"  - {deadline}")
    
    print(f"\n💭 Tips and Warnings:")
    for tip in guide.tips_and_warnings[:3]:
        print(f"  - {tip}")
    print(f"  ... and {len(guide.tips_and_warnings) - 3} more tips")
    
    print(f"\n📚 Citations:")
    for citation in guide.citations:
        print(f"  - {citation}")


def example_ped_rejection_guidance():
    """Example: Guidance for PED-related rejection."""
    print("\n" + "=" * 80)
    print("Example 2: PED Rejection Guidance")
    print("=" * 80)
    
    advisor = OmbudsmanAdvisor()
    
    claim_details = {
        "claim_type": "hospitalization",
        "claim_amount": 200000,
        "treatment": "Diabetes complications",
        "condition": "Type 2 Diabetes"
    }
    
    guide = advisor.generate_complaint_guidance(
        claim_id="CLM-2024-002",
        claim_details=claim_details,
        rejection_reason="Pre-existing disease - diabetes not disclosed during policy purchase",
        policy_id="POL-ICICI-002"
    )
    
    print(f"\nPED-Specific Argument Points:")
    ped_args = [arg for arg in guide.argument_points if "pre-existing" in arg.lower() or "disclosed" in arg.lower()]
    for arg in ped_args:
        print(f"  ✓ {arg}")


def example_waiting_period_guidance():
    """Example: Guidance for waiting period rejection."""
    print("\n" + "=" * 80)
    print("Example 3: Waiting Period Rejection Guidance")
    print("=" * 80)
    
    advisor = OmbudsmanAdvisor()
    
    claim_details = {
        "claim_type": "surgery",
        "claim_amount": 180000,
        "treatment": "Knee replacement surgery"
    }
    
    guide = advisor.generate_complaint_guidance(
        claim_id="CLM-2024-003",
        claim_details=claim_details,
        rejection_reason="Claim filed during waiting period for joint replacement procedures",
        policy_id="POL-SBI-003"
    )
    
    print(f"\nWaiting Period-Specific Argument Points:")
    waiting_args = [arg for arg in guide.argument_points if "waiting period" in arg.lower()]
    for arg in waiting_args:
        print(f"  ✓ {arg}")


def example_documentation_guidance():
    """Example: Guidance for documentation rejection."""
    print("\n" + "=" * 80)
    print("Example 4: Documentation Rejection Guidance")
    print("=" * 80)
    
    advisor = OmbudsmanAdvisor()
    
    claim_details = {
        "claim_type": "hospitalization",
        "claim_amount": 120000,
        "treatment": "Emergency surgery"
    }
    
    guide = advisor.generate_complaint_guidance(
        claim_id="CLM-2024-004",
        claim_details=claim_details,
        rejection_reason="Incomplete documentation - missing discharge summary and medical bills",
        policy_id="POL-STAR-004"
    )
    
    print(f"\nDocumentation-Specific Argument Points:")
    doc_args = [arg for arg in guide.argument_points if "document" in arg.lower()]
    for arg in doc_args:
        print(f"  ✓ {arg}")
    
    print(f"\nRelevant Tips:")
    doc_tips = [tip for tip in guide.tips_and_warnings if "document" in tip.lower()]
    for tip in doc_tips:
        print(f"  💡 {tip}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("COMPLAINT GUIDANCE GENERATOR EXAMPLES")
    print("=" * 80)
    print("\nThese examples demonstrate the complaint guidance generator")
    print("functionality of the Ombudsman Advisor service.")
    print("\nValidates: Requirement 7.5")
    print("=" * 80)
    
    example_basic_complaint_guidance()
    example_ped_rejection_guidance()
    example_waiting_period_guidance()
    example_documentation_guidance()
    
    print("\n" + "=" * 80)
    print("Examples completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
