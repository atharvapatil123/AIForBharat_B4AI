"""
Simple verification script for Task 8.4: Missing Document Identifier

This script tests the identify_missing_documents functionality without
requiring full service initialization.
"""

import asyncio
from datetime import date, datetime, timezone
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from healthcare_insurance_platform.models.claim import ClaimDetails, TreatmentDetails
from healthcare_insurance_platform.models.policy import PolicyDocument, WaitingPeriod, ParsedClause
from healthcare_insurance_platform.models.results import MissingDocument


def test_document_normalization():
    """Test document name normalization logic."""
    print("=" * 80)
    print("Test 1: Document Name Normalization")
    print("=" * 80)
    
    # Import the normalization function
    from healthcare_insurance_platform.services.claim_predictor import ClaimPredictorService
    
    service = ClaimPredictorService()
    
    test_cases = [
        ("Discharge_Summary", "discharge summary"),
        ("discharge summary", "discharge summary"),
        ("DISCHARGE SUMMARY", "discharge summary"),
        ("original_discharge_summary", "discharge summary"),
        ("discharge-summary-copy", "discharge summary"),
        ("Hospital Bill", "hospital bill"),
        ("hospital_bill_original", "hospital bill"),
        ("ID Proof", "id proof"),
        ("id_proof", "id proof"),
        ("identity_proof", "id proof"),
        ("Surgery Report", "surgery report"),
        ("operation_notes", "surgery report"),
        ("Lab Report", "lab report"),
        ("diagnostic_report", "lab report"),
    ]
    
    all_passed = True
    for input_name, expected in test_cases:
        result = service._normalize_document_name(input_name)
        passed = result == expected
        status = "✓" if passed else "✗"
        print(f"  {status} '{input_name}' -> '{result}' (expected: '{expected}')")
        if not passed:
            all_passed = False
    
    return all_passed


def test_document_matching():
    """Test document matching logic."""
    print("\n" + "=" * 80)
    print("Test 2: Document Matching Logic")
    print("=" * 80)
    
    from healthcare_insurance_platform.services.claim_predictor import ClaimPredictorService
    
    service = ClaimPredictorService()
    
    # Test cases: (required_doc, provided_docs, should_match)
    test_cases = [
        # Exact match
        (
            MissingDocument(
                document_type="discharge_summary",
                importance="critical",
                reason="Required for claim",
                alternatives=[],
            ),
            {"discharge summary"},
            True,
            "Exact match"
        ),
        # Partial match
        (
            MissingDocument(
                document_type="discharge_summary",
                importance="critical",
                reason="Required for claim",
                alternatives=[],
            ),
            {"discharge summary report"},
            True,
            "Partial match (required in provided)"
        ),
        # Alternative match
        (
            MissingDocument(
                document_type="discharge_summary",
                importance="critical",
                reason="Required for claim",
                alternatives=["discharge_card", "hospital_discharge_certificate"],
            ),
            {"discharge card"},
            True,
            "Alternative match"
        ),
        # No match
        (
            MissingDocument(
                document_type="discharge_summary",
                importance="critical",
                reason="Required for claim",
                alternatives=[],
            ),
            {"hospital bill"},
            False,
            "No match"
        ),
        # Fuzzy match with similar name
        (
            MissingDocument(
                document_type="hospital_bill",
                importance="critical",
                reason="Required for claim",
                alternatives=[],
            ),
            {"final hospital invoice"},
            True,
            "Fuzzy match"
        ),
    ]
    
    all_passed = True
    for required_doc, provided_docs, should_match, description in test_cases:
        normalized_required = service._normalize_document_name(required_doc.document_type)
        result = service._check_document_provided(
            required_doc=required_doc,
            normalized_required=normalized_required,
            normalized_provided=provided_docs,
        )
        passed = result == should_match
        status = "✓" if passed else "✗"
        print(f"  {status} {description}: {required_doc.document_type} vs {provided_docs}")
        print(f"      Expected: {should_match}, Got: {result}")
        if not passed:
            all_passed = False
    
    return all_passed


async def test_missing_document_identification():
    """Test the complete missing document identification flow."""
    print("\n" + "=" * 80)
    print("Test 3: Missing Document Identification")
    print("=" * 80)
    
    from healthcare_insurance_platform.services.claim_predictor import ClaimPredictorService
    
    # Create a sample policy document
    policy = PolicyDocument(
        policy_id="POL-TEST-001",
        provider_id="PROVIDER-001",
        policy_name="Test Health Insurance Policy",
        policy_type="individual",
        version="1.0",
        effective_date=date(2024, 1, 1),
        coverage_amount=500000,
        premium=15000,
        waiting_periods=WaitingPeriod(
            general=30,
            pre_existing=730,
            specific_conditions=[
                {"condition": "hernia", "days": 365},
            ],
        ),
        inclusions=[
            "hospitalization expenses",
            "surgery costs",
        ],
        exclusions=[
            "cosmetic surgery",
        ],
        ped_policy="Covered after 2 years",
        claim_process="Submit within 30 days",
        document_requirements=[
            {
                "claim_type": "surgery",
                "documents": [
                    "discharge_summary",
                    "hospital_bill",
                    "surgery_report",
                    "claim_form",
                    "id_proof",
                ],
            },
        ],
        full_text="Full policy text...",
        parsed_clauses=[
            ParsedClause(
                clause_type="coverage",
                text="This policy covers hospitalization expenses",
                importance="critical",
            ),
        ],
        last_updated=datetime.now(timezone.utc),
    )
    
    # Create a sample claim
    claim = ClaimDetails(
        claim_id="CLAIM-TEST-001",
        user_id="USER-001",
        policy_id="POL-TEST-001",
        claim_type="surgery",
        claim_amount=150000,
        treatment_details=TreatmentDetails(
            condition="Appendicitis",
            hospital="City Hospital",
            admission_date=date(2024, 6, 1),
            discharge_date=date(2024, 6, 5),
            procedures=["Appendectomy"],
            diagnosis="Acute appendicitis",
        ),
        documents_provided=[],
        claim_date=date(2024, 6, 10),
        status="pending",
    )
    
    # Initialize the service
    service = ClaimPredictorService()
    
    # Mock the policy retrieval
    async def mock_get_policy(policy_id: str):
        return policy
    
    service._get_policy_for_prediction = mock_get_policy
    
    # Test Case 1: No documents provided
    print("\n  Test Case 1: No documents provided")
    provided_docs_1 = []
    missing_docs_1 = await service.identify_missing_documents(
        claim_details=claim,
        policy_id="POL-TEST-001",
        provided_docs=provided_docs_1,
    )
    print(f"    Provided: {len(provided_docs_1)} documents")
    print(f"    Missing: {len(missing_docs_1)} documents")
    test1_passed = len(missing_docs_1) >= 5  # Should have at least 5 missing docs
    print(f"    {'✓' if test1_passed else '✗'} Expected at least 5 missing documents")
    
    # Test Case 2: Some documents provided
    print("\n  Test Case 2: Some documents provided")
    provided_docs_2 = ["discharge_summary", "hospital_bill"]
    missing_docs_2 = await service.identify_missing_documents(
        claim_details=claim,
        policy_id="POL-TEST-001",
        provided_docs=provided_docs_2,
    )
    print(f"    Provided: {len(provided_docs_2)} documents")
    print(f"    Missing: {len(missing_docs_2)} documents")
    test2_passed = len(missing_docs_2) < len(missing_docs_1)
    print(f"    {'✓' if test2_passed else '✗'} Missing count decreased")
    
    # Test Case 3: Alternative documents provided
    print("\n  Test Case 3: Alternative documents provided")
    provided_docs_3 = [
        "discharge_card",  # Alternative to discharge_summary
        "medical_bill",    # Alternative to hospital_bill
        "operation_notes", # Alternative to surgery_report
        "claim_application", # Alternative to claim_form
        "aadhaar_card",    # Alternative to id_proof
    ]
    missing_docs_3 = await service.identify_missing_documents(
        claim_details=claim,
        policy_id="POL-TEST-001",
        provided_docs=provided_docs_3,
    )
    print(f"    Provided: {len(provided_docs_3)} documents (alternatives)")
    print(f"    Missing: {len(missing_docs_3)} documents")
    test3_passed = len(missing_docs_3) < len(missing_docs_2)
    print(f"    {'✓' if test3_passed else '✗'} Alternatives recognized")
    
    # Test Case 4: Fuzzy matching
    print("\n  Test Case 4: Fuzzy matching")
    provided_docs_4 = [
        "Discharge Summary Report",
        "Final Hospital Invoice",
        "Surgical Procedure Report",
        "Insurance Claim Form",
        "Aadhaar Card Copy",
    ]
    missing_docs_4 = await service.identify_missing_documents(
        claim_details=claim,
        policy_id="POL-TEST-001",
        provided_docs=provided_docs_4,
    )
    print(f"    Provided: {len(provided_docs_4)} documents (fuzzy names)")
    print(f"    Missing: {len(missing_docs_4)} documents")
    test4_passed = len(missing_docs_4) < len(missing_docs_2)
    print(f"    {'✓' if test4_passed else '✗'} Fuzzy matching works")
    
    return test1_passed and test2_passed and test3_passed and test4_passed


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("Task 8.4: Missing Document Identifier - Simple Verification")
    print("=" * 80)
    
    try:
        test1_passed = test_document_normalization()
        test2_passed = test_document_matching()
        test3_passed = await test_missing_document_identification()
        
        print("\n" + "=" * 80)
        print("Test Results Summary")
        print("=" * 80)
        print(f"  {'✓' if test1_passed else '✗'} Test 1: Document Name Normalization")
        print(f"  {'✓' if test2_passed else '✗'} Test 2: Document Matching Logic")
        print(f"  {'✓' if test3_passed else '✗'} Test 3: Missing Document Identification")
        
        all_passed = test1_passed and test2_passed and test3_passed
        
        print("\n" + "=" * 80)
        if all_passed:
            print("✓ All tests passed! Task 8.4 implementation is working correctly.")
        else:
            print("✗ Some tests failed. Please review the implementation.")
        print("=" * 80)
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
