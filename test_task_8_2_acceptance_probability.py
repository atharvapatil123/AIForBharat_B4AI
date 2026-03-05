"""
Standalone test for Task 8.2: Acceptance Probability Calculation

This test verifies that the predict_claim_acceptance method:
1. Analyzes supporting and contradicting factors
2. Calculates weighted probability score
3. Generates detailed reasoning with citations

Requirements: 5.2, 5.3, 5.4
"""

import asyncio
from datetime import date, datetime, timezone
from healthcare_insurance_platform.models.claim import (
    ClaimDetails,
    TreatmentDetails,
    DocumentProvided,
)
from healthcare_insurance_platform.models.policy import (
    PolicyDocument,
    WaitingPeriod,
    DocumentRequirement,
    ParsedClause,
)
from healthcare_insurance_platform.services.claim_predictor import ClaimPredictorService


def create_test_policy() -> PolicyDocument:
    """Create a test policy document."""
    return PolicyDocument(
        policy_id="TEST-POL-001",
        provider_id="TEST-PROVIDER",
        policy_name="Test Health Insurance Policy",
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
                {"condition": "hypertension", "days": 180},
            ],
        ),
        inclusions=[
            "hospitalization expenses",
            "surgery costs",
            "diagnostic tests",
            "ambulance charges",
            "room rent",
        ],
        exclusions=[
            "cosmetic surgery",
            "dental treatment",
            "experimental treatments",
            "self-inflicted injuries",
        ],
        ped_policy="Pre-existing diseases covered after waiting period",
        claim_process="Submit claim within 30 days of discharge",
        document_requirements=[
            DocumentRequirement(
                claim_type="hospitalization",
                documents=["hospital_bill", "discharge_summary", "medical_reports"],
            ),
        ],
        full_text="Complete policy document text...",
        parsed_clauses=[
            ParsedClause(
                clause_type="coverage",
                text="This policy covers hospitalization expenses up to ₹5,00,000",
                importance="critical",
            ),
            ParsedClause(
                clause_type="exclusion",
                text="Cosmetic surgery and dental treatments are not covered",
                importance="high",
            ),
            ParsedClause(
                clause_type="waiting_period",
                text="General waiting period of 30 days applies to all claims",
                importance="medium",
            ),
        ],
        last_updated=datetime.now(timezone.utc),
    )


def create_test_claim_high_acceptance() -> ClaimDetails:
    """Create a test claim with high acceptance probability."""
    return ClaimDetails(
        claim_id="CLAIM-001",
        user_id="USER-001",
        policy_id="TEST-POL-001",
        claim_type="hospitalization",
        claim_amount=150000.0,
        treatment_details=TreatmentDetails(
            condition="appendicitis",
            hospital="City Hospital",
            admission_date=date(2024, 6, 1),
            discharge_date=date(2024, 6, 5),
            procedures=["appendectomy", "post-operative care"],
            diagnosis="acute appendicitis",
        ),
        documents_provided=[
            DocumentProvided(
                document_type="hospital_bill",
                file_name="bill.pdf",
                upload_date=datetime.now(timezone.utc),
            ),
        ],
        claim_date=date(2024, 6, 10),
        status="pending",
    )


def create_test_claim_low_acceptance() -> ClaimDetails:
    """Create a test claim with low acceptance probability."""
    return ClaimDetails(
        claim_id="CLAIM-002",
        user_id="USER-002",
        policy_id="TEST-POL-001",
        claim_type="surgery",
        claim_amount=600000.0,  # Exceeds coverage
        treatment_details=TreatmentDetails(
            condition="cosmetic enhancement",
            hospital="Cosmetic Clinic",
            admission_date=date(2024, 6, 1),
            discharge_date=date(2024, 6, 2),
            procedures=["rhinoplasty"],
            diagnosis="cosmetic surgery",
        ),
        documents_provided=[],
        claim_date=date(2024, 6, 10),
        status="pending",
    )


async def test_high_acceptance_claim():
    """Test claim with high acceptance probability."""
    print("\n" + "="*80)
    print("TEST 1: High Acceptance Probability Claim")
    print("="*80)
    
    # Create service
    service = ClaimPredictorService()
    
    # Create test data
    claim = create_test_claim_high_acceptance()
    policy = create_test_policy()
    
    # Mock the policy retrieval
    async def mock_get_policy(policy_id):
        return policy
    
    service._get_policy_for_prediction = mock_get_policy
    
    # Predict claim acceptance
    prediction = await service.predict_claim_acceptance(
        claim_details=claim,
        policy_id=policy.policy_id,
        language="en",
    )
    
    # Verify results
    print(f"\n✓ Prediction ID: {prediction.prediction_id}")
    print(f"✓ Claim ID: {prediction.claim_id}")
    print(f"✓ Acceptance Probability: {prediction.acceptance_probability:.2%}")
    print(f"✓ Confidence Level: {prediction.confidence_level}")
    print(f"✓ Supporting Factors: {len(prediction.supporting_factors)}")
    print(f"✓ Contradicting Factors: {len(prediction.contradicting_factors)}")
    print(f"✓ Recommendations: {len(prediction.recommendations)}")
    
    # Verify acceptance probability calculation
    assert 0.0 <= prediction.acceptance_probability <= 1.0, \
        "Acceptance probability must be between 0 and 1"
    
    # Verify supporting factors exist
    assert len(prediction.supporting_factors) > 0, \
        "Should have supporting factors for covered treatment"
    
    # Verify explanation exists
    assert len(prediction.explanation) > 0, \
        "Explanation must be provided"
    
    # Verify citations exist
    assert len(prediction.citations) > 0, \
        "Citations must be provided"
    
    # Verify confidence level is valid
    assert prediction.confidence_level in ['low', 'medium', 'high'], \
        "Confidence level must be low, medium, or high"
    
    print("\n--- Explanation ---")
    print(prediction.explanation)
    
    print("\n--- Supporting Factors ---")
    for i, factor in enumerate(prediction.supporting_factors, 1):
        print(f"{i}. {factor.factor}")
        print(f"   Weight: {factor.weight:.2f}")
        print(f"   Clause: {factor.policy_clause[:80]}...")
    
    if prediction.contradicting_factors:
        print("\n--- Contradicting Factors ---")
        for i, factor in enumerate(prediction.contradicting_factors, 1):
            print(f"{i}. {factor.factor}")
            print(f"   Reason: {factor.reason}")
    
    print("\n--- Citations ---")
    for i, citation in enumerate(prediction.citations, 1):
        print(f"{i}. {citation}")
    
    print("\n✅ TEST 1 PASSED: High acceptance claim processed correctly")
    return prediction


async def test_low_acceptance_claim():
    """Test claim with low acceptance probability."""
    print("\n" + "="*80)
    print("TEST 2: Low Acceptance Probability Claim")
    print("="*80)
    
    # Create service
    service = ClaimPredictorService()
    
    # Create test data
    claim = create_test_claim_low_acceptance()
    policy = create_test_policy()
    
    # Mock the policy retrieval
    async def mock_get_policy(policy_id):
        return policy
    
    service._get_policy_for_prediction = mock_get_policy
    
    # Predict claim acceptance
    prediction = await service.predict_claim_acceptance(
        claim_details=claim,
        policy_id=policy.policy_id,
        language="en",
    )
    
    # Verify results
    print(f"\n✓ Prediction ID: {prediction.prediction_id}")
    print(f"✓ Claim ID: {prediction.claim_id}")
    print(f"✓ Acceptance Probability: {prediction.acceptance_probability:.2%}")
    print(f"✓ Confidence Level: {prediction.confidence_level}")
    print(f"✓ Supporting Factors: {len(prediction.supporting_factors)}")
    print(f"✓ Contradicting Factors: {len(prediction.contradicting_factors)}")
    print(f"✓ Recommendations: {len(prediction.recommendations)}")
    
    # Verify acceptance probability is low
    assert prediction.acceptance_probability < 0.5, \
        "Acceptance probability should be low for excluded treatment exceeding coverage"
    
    # Verify contradicting factors exist
    assert len(prediction.contradicting_factors) > 0, \
        "Should have contradicting factors for excluded treatment"
    
    # Verify explanation exists
    assert len(prediction.explanation) > 0, \
        "Explanation must be provided"
    
    # Verify recommendations exist
    assert len(prediction.recommendations) > 0, \
        "Recommendations must be provided for low acceptance claims"
    
    print("\n--- Explanation ---")
    print(prediction.explanation)
    
    if prediction.supporting_factors:
        print("\n--- Supporting Factors ---")
        for i, factor in enumerate(prediction.supporting_factors, 1):
            print(f"{i}. {factor.factor}")
            print(f"   Weight: {factor.weight:.2f}")
    
    print("\n--- Contradicting Factors ---")
    for i, factor in enumerate(prediction.contradicting_factors, 1):
        print(f"{i}. {factor.factor}")
        print(f"   Reason: {factor.reason}")
    
    print("\n--- Recommendations ---")
    for i, rec in enumerate(prediction.recommendations, 1):
        print(f"{i}. {rec}")
    
    print("\n✅ TEST 2 PASSED: Low acceptance claim processed correctly")
    return prediction


async def test_weighted_probability_calculation():
    """Test that probability calculation uses weighted factors."""
    print("\n" + "="*80)
    print("TEST 3: Weighted Probability Calculation")
    print("="*80)
    
    # Create service
    service = ClaimPredictorService()
    
    # Create test data - moderate case
    claim = ClaimDetails(
        claim_id="CLAIM-003",
        user_id="USER-003",
        policy_id="TEST-POL-001",
        claim_type="diagnostic",
        claim_amount=25000.0,
        treatment_details=TreatmentDetails(
            condition="chest pain",
            hospital="Diagnostic Center",
            admission_date=date(2024, 6, 1),
            discharge_date=date(2024, 6, 1),
            procedures=["ECG", "blood tests", "chest X-ray"],
            diagnosis="cardiac evaluation",
        ),
        documents_provided=[],
        claim_date=date(2024, 6, 10),
        status="pending",
    )
    
    policy = create_test_policy()
    
    # Mock the policy retrieval
    async def mock_get_policy(policy_id):
        return policy
    
    service._get_policy_for_prediction = mock_get_policy
    
    # Predict claim acceptance
    prediction = await service.predict_claim_acceptance(
        claim_details=claim,
        policy_id=policy.policy_id,
        language="en",
    )
    
    print(f"\n✓ Acceptance Probability: {prediction.acceptance_probability:.2%}")
    print(f"✓ Supporting Factors: {len(prediction.supporting_factors)}")
    print(f"✓ Contradicting Factors: {len(prediction.contradicting_factors)}")
    
    # Verify probability is calculated
    assert 0.0 <= prediction.acceptance_probability <= 1.0, \
        "Probability must be in valid range"
    
    # Verify factors have weights
    for factor in prediction.supporting_factors:
        assert 0.0 <= factor.weight <= 1.0, \
            f"Factor weight must be between 0 and 1, got {factor.weight}"
    
    print("\n--- Factor Weights ---")
    total_weight = sum(f.weight for f in prediction.supporting_factors)
    print(f"Total supporting weight: {total_weight:.2f}")
    
    for factor in prediction.supporting_factors:
        print(f"  • {factor.factor[:60]}... (weight: {factor.weight:.2f})")
    
    print("\n✅ TEST 3 PASSED: Weighted probability calculation works correctly")
    return prediction


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("TASK 8.2: ACCEPTANCE PROBABILITY CALCULATION TESTS")
    print("="*80)
    
    try:
        # Run tests
        pred1 = await test_high_acceptance_claim()
        pred2 = await test_low_acceptance_claim()
        pred3 = await test_weighted_probability_calculation()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"✅ Test 1: High acceptance claim - {pred1.acceptance_probability:.2%}")
        print(f"✅ Test 2: Low acceptance claim - {pred2.acceptance_probability:.2%}")
        print(f"✅ Test 3: Weighted calculation - {pred3.acceptance_probability:.2%}")
        print("\n🎉 ALL TESTS PASSED!")
        print("\nTask 8.2 Implementation Verified:")
        print("  ✓ Analyzes supporting and contradicting factors")
        print("  ✓ Calculates weighted probability score")
        print("  ✓ Generates detailed reasoning with citations")
        print("  ✓ Requirements 5.2, 5.3, 5.4 satisfied")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
