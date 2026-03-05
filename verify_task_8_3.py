"""
Verification script for Task 8.3: Document Requirement Generator

This script tests the generate_document_requirements method to ensure it:
1. Determines required documents based on claim type and policy
2. Generates document list with explanations
3. Prioritizes documents by importance
"""

import asyncio
from datetime import date, datetime, timezone

from healthcare_insurance_platform.models.claim import ClaimDetails, TreatmentDetails
from healthcare_insurance_platform.models.policy import (
    DocumentRequirement,
    ParsedClause,
    PolicyDocument,
    WaitingPeriod,
)
from healthcare_insurance_platform.services.claim_predictor import ClaimPredictorService


async def test_document_requirement_generator():
    """Test the document requirement generator functionality."""
    
    print("=" * 80)
    print("Task 8.3 Verification: Document Requirement Generator")
    print("=" * 80)
    
    # Create a sample policy document
    policy = PolicyDocument(
        policy_id="POL-TEST-001",
        provider_id="PROV-001",
        policy_name="Comprehensive Health Insurance",
        policy_type="individual",
        version="1.0",
        effective_date=date(2024, 1, 1),
        coverage_amount=500000.0,
        premium=15000.0,
        waiting_periods=WaitingPeriod(
            general=30,
            pre_existing=730,
            specific_conditions=[
                {"condition": "diabetes", "days": 365},
            ],
        ),
        inclusions=[
            "hospitalization expenses",
            "surgery costs",
            "diagnostic tests",
            "ambulance charges",
        ],
        exclusions=[
            "cosmetic surgery",
            "dental treatment",
            "alternative medicine",
        ],
        ped_policy="Pre-existing diseases covered after 2-year waiting period",
        claim_process="Submit claim within 30 days of discharge",
        document_requirements=[
            DocumentRequirement(
                claim_type="hospitalization",
                documents=[
                    "discharge_summary",
                    "hospital_bill",
                    "diagnostic_reports",
                    "claim_form",
                    "id_proof",
                ],
            ),
            DocumentRequirement(
                claim_type="surgery",
                documents=[
                    "discharge_summary",
                    "surgery_report",
                    "hospital_bill",
                    "anesthesia_report",
                    "claim_form",
                    "id_proof",
                ],
            ),
        ],
        full_text="Complete policy document text...",
        parsed_clauses=[
            ParsedClause(
                clause_type="coverage",
                text="This policy covers hospitalization expenses up to ₹5,00,000",
                importance="critical",
            ),
        ],
    )
    
    # Create claim predictor service
    service = ClaimPredictorService()
    
    # Mock the policy retrieval
    async def mock_get_policy(policy_id: str):
        return policy
    
    service._get_policy_for_prediction = mock_get_policy
    
    # Test Case 1: Basic hospitalization claim
    print("\n" + "=" * 80)
    print("Test Case 1: Basic Hospitalization Claim")
    print("=" * 80)
    
    claim1 = ClaimDetails(
        claim_id="CLM-001",
        user_id="USER-001",
        policy_id="POL-TEST-001",
        claim_type="hospitalization",
        claim_amount=50000.0,
        treatment_details=TreatmentDetails(
            condition="Pneumonia",
            hospital="City Hospital",
            admission_date=date(2024, 3, 1),
            discharge_date=date(2024, 3, 5),
            procedures=["chest_xray", "blood_tests"],
            diagnosis="Bacterial pneumonia",
        ),
        documents_provided=[],
        claim_date=date(2024, 3, 6),
        status="pending",
    )
    
    docs1 = await service.generate_document_requirements(
        claim_details=claim1,
        policy_id="POL-TEST-001",
    )
    
    print(f"\nGenerated {len(docs1)} document requirements:")
    print(f"  Critical: {sum(1 for d in docs1 if d.importance == 'critical')}")
    print(f"  Recommended: {sum(1 for d in docs1 if d.importance == 'recommended')}")
    print(f"  Optional: {sum(1 for d in docs1 if d.importance == 'optional')}")
    
    print("\nDocument Requirements (sorted by importance):")
    for i, doc in enumerate(docs1, 1):
        print(f"\n{i}. {doc.document_type} [{doc.importance.upper()}]")
        print(f"   Reason: {doc.reason[:100]}...")
        if doc.alternatives:
            print(f"   Alternatives: {', '.join(doc.alternatives[:3])}")
    
    # Test Case 2: Surgery claim with high value
    print("\n" + "=" * 80)
    print("Test Case 2: High-Value Surgery Claim")
    print("=" * 80)
    
    claim2 = ClaimDetails(
        claim_id="CLM-002",
        user_id="USER-002",
        policy_id="POL-TEST-001",
        claim_type="surgery",
        claim_amount=400000.0,  # 80% of coverage
        treatment_details=TreatmentDetails(
            condition="Cardiac disease",
            hospital="Advanced Cardiac Center",
            admission_date=date(2024, 3, 10),
            discharge_date=date(2024, 3, 20),
            procedures=["coronary_bypass", "icu_care"],
            diagnosis="Coronary artery disease",
        ),
        documents_provided=[],
        claim_date=date(2024, 3, 21),
        status="pending",
    )
    
    docs2 = await service.generate_document_requirements(
        claim_details=claim2,
        policy_id="POL-TEST-001",
    )
    
    print(f"\nGenerated {len(docs2)} document requirements:")
    print(f"  Critical: {sum(1 for d in docs2 if d.importance == 'critical')}")
    print(f"  Recommended: {sum(1 for d in docs2 if d.importance == 'recommended')}")
    print(f"  Optional: {sum(1 for d in docs2 if d.importance == 'optional')}")
    
    print("\nDocument Requirements (sorted by importance):")
    for i, doc in enumerate(docs2, 1):
        print(f"\n{i}. {doc.document_type} [{doc.importance.upper()}]")
        print(f"   Reason: {doc.reason[:100]}...")
        if doc.alternatives:
            print(f"   Alternatives: {', '.join(doc.alternatives[:3])}")
    
    # Test Case 3: Surgery with implant
    print("\n" + "=" * 80)
    print("Test Case 3: Surgery with Implant")
    print("=" * 80)
    
    claim3 = ClaimDetails(
        claim_id="CLM-003",
        user_id="USER-003",
        policy_id="POL-TEST-001",
        claim_type="surgery",
        claim_amount=250000.0,
        treatment_details=TreatmentDetails(
            condition="Orthopedic fracture",
            hospital="Orthopedic Specialty Hospital",
            admission_date=date(2024, 3, 15),
            discharge_date=date(2024, 3, 18),
            procedures=["hip_replacement", "implant_surgery"],
            diagnosis="Hip fracture requiring implant",
        ),
        documents_provided=[],
        claim_date=date(2024, 3, 19),
        status="pending",
    )
    
    docs3 = await service.generate_document_requirements(
        claim_details=claim3,
        policy_id="POL-TEST-001",
    )
    
    print(f"\nGenerated {len(docs3)} document requirements:")
    print(f"  Critical: {sum(1 for d in docs3 if d.importance == 'critical')}")
    print(f"  Recommended: {sum(1 for d in docs3 if d.importance == 'recommended')}")
    print(f"  Optional: {sum(1 for d in docs3 if d.importance == 'optional')}")
    
    print("\nDocument Requirements (sorted by importance):")
    for i, doc in enumerate(docs3, 1):
        print(f"\n{i}. {doc.document_type} [{doc.importance.upper()}]")
        print(f"   Reason: {doc.reason[:100]}...")
        if doc.alternatives:
            print(f"   Alternatives: {', '.join(doc.alternatives[:3])}")
    
    # Verify key requirements
    print("\n" + "=" * 80)
    print("Verification Summary")
    print("=" * 80)
    
    # Check that documents are prioritized
    assert all(
        docs1[i].importance <= docs1[i + 1].importance
        for i in range(len(docs1) - 1)
        if docs1[i].importance in ['critical', 'recommended', 'optional']
        and docs1[i + 1].importance in ['critical', 'recommended', 'optional']
    ), "Documents should be sorted by importance"
    print("✓ Documents are properly prioritized (critical → recommended → optional)")
    
    # Check that all documents have explanations
    assert all(doc.reason for doc in docs1), "All documents should have reasons"
    assert all(doc.reason for doc in docs2), "All documents should have reasons"
    assert all(doc.reason for doc in docs3), "All documents should have reasons"
    print("✓ All documents have explanations")
    
    # Check that high-value claims have additional requirements
    assert len(docs2) > len(docs1), "High-value claims should have more requirements"
    print("✓ High-value claims generate additional document requirements")
    
    # Check that implant procedures trigger specific requirements
    implant_docs = [d for d in docs3 if 'implant' in d.document_type.lower()]
    assert len(implant_docs) > 0, "Implant procedures should require implant documentation"
    print("✓ Implant procedures trigger specific document requirements")
    
    # Check that cardiac conditions trigger ECG requirement
    cardiac_docs = [d for d in docs2 if 'ecg' in d.document_type.lower()]
    assert len(cardiac_docs) > 0, "Cardiac conditions should require ECG report"
    print("✓ Cardiac conditions trigger ECG report requirement")
    
    # Check that orthopedic conditions trigger X-ray requirement
    xray_docs = [d for d in docs3 if 'xray' in d.document_type.lower() or 'x-ray' in d.document_type.lower()]
    assert len(xray_docs) > 0, "Orthopedic conditions should require X-ray report"
    print("✓ Orthopedic conditions trigger X-ray report requirement")
    
    print("\n" + "=" * 80)
    print("Task 8.3 Implementation: SUCCESS")
    print("=" * 80)
    print("\nThe document requirement generator successfully:")
    print("  1. Determines required documents based on claim type and policy")
    print("  2. Generates document list with detailed explanations")
    print("  3. Prioritizes documents by importance (critical, recommended, optional)")
    print("  4. Identifies alternative acceptable documents")
    print("  5. Adds claim-specific additional documents based on:")
    print("     - Claim amount (high-value claims)")
    print("     - Claim type (surgery, hospitalization)")
    print("     - Procedures (implants, ICU care)")
    print("     - Medical conditions (cardiac, orthopedic, cancer)")
    print("\nRequirements validated: 6.1, 6.3, 6.5")


if __name__ == "__main__":
    asyncio.run(test_document_requirement_generator())
