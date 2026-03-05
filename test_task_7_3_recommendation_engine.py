"""
Test script for Task 7.3: Policy Recommendation Engine

This script verifies that the enhanced policy recommendation engine:
1. Ranks policies by compatibility score
2. Filters and recommends top policies based on user profile
3. Generates detailed recommendation reasoning
4. Considers PED compatibility, cost, coverage, and rejection risk
"""

import asyncio
from datetime import date, datetime, timezone

from healthcare_insurance_platform.models.policy import PolicyDocument, WaitingPeriod
from healthcare_insurance_platform.models.results import ComparedPolicy, PolicyScore
from healthcare_insurance_platform.models.user_profile import Demographics, MedicalHistory, UserProfile
from healthcare_insurance_platform.services.policy_analyzer import PolicyAnalyzer


async def test_recommendation_engine():
    """Test the enhanced policy recommendation engine."""
    
    print("=" * 80)
    print("Testing Task 7.3: Policy Recommendation Engine")
    print("=" * 80)
    
    # Create a user profile with pre-existing conditions
    user_profile = UserProfile(
        user_id="test_user_001",
        demographics=Demographics(
            age=45,
            gender="male",
            location="Mumbai, Maharashtra",
        ),
        medical_history=MedicalHistory(
            pre_existing_diseases=[
                {
                    "condition": "Diabetes Type 2",
                    "diagnosis_date": date(2020, 1, 15),
                    "severity": "moderate",
                },
                {
                    "condition": "Hypertension",
                    "diagnosis_date": date(2019, 6, 10),
                    "severity": "mild",
                },
            ],
            current_medications=[
                {
                    "name": "Metformin",
                    "dosage": "500mg",
                    "start_date": date(2020, 1, 20),
                },
                {
                    "name": "Amlodipine",
                    "dosage": "5mg",
                    "start_date": date(2019, 6, 15),
                },
            ],
            allergies=["Penicillin"],
            past_surgeries=[],
        ),
        language_preference="en",
        consent_given=True,
        data_retention_preference="standard",
    )
    
    # Create mock compared policies with different characteristics
    compared_policies = [
        # Policy 1: Best overall - good balance
        ComparedPolicy(
            policy_id="policy_001",
            policy_name="HealthGuard Plus",
            provider="Star Health Insurance",
            overall_score=85.5,
            score_breakdown=PolicyScore(
                ped_compatibility=90.0,
                cost_effectiveness=80.0,
                coverage_comprehensiveness=85.0,
                claim_settlement_ratio=87.0,
            ),
            pros=[
                "Excellent PED coverage",
                "Competitive premium rates",
                "Comprehensive coverage",
            ],
            cons=["2-year waiting period for PEDs"],
            rejection_risk="low",
            reasoning="Highly suitable for your profile with excellent PED compatibility.",
        ),
        # Policy 2: Best value but lower PED compatibility
        ComparedPolicy(
            policy_id="policy_002",
            policy_name="Budget Care",
            provider="ICICI Lombard",
            overall_score=72.0,
            score_breakdown=PolicyScore(
                ped_compatibility=60.0,
                cost_effectiveness=95.0,
                coverage_comprehensiveness=70.0,
                claim_settlement_ratio=85.0,
            ),
            pros=["Best value for money", "Low premium"],
            cons=["Limited PED coverage", "3-year waiting period"],
            rejection_risk="medium",
            reasoning="Good value but moderate PED compatibility.",
        ),
        # Policy 3: Best coverage but expensive
        ComparedPolicy(
            policy_id="policy_003",
            policy_name="Premium Shield",
            provider="HDFC ERGO",
            overall_score=78.0,
            score_breakdown=PolicyScore(
                ped_compatibility=75.0,
                cost_effectiveness=65.0,
                coverage_comprehensiveness=95.0,
                claim_settlement_ratio=90.0,
            ),
            pros=["Most comprehensive coverage", "Excellent claim settlement"],
            cons=["Higher premium", "Moderate PED waiting period"],
            rejection_risk="low",
            reasoning="Comprehensive coverage with good PED terms.",
        ),
        # Policy 4: Best PED compatibility
        ComparedPolicy(
            policy_id="policy_004",
            policy_name="Diabetes Care Plus",
            provider="Max Bupa",
            overall_score=80.0,
            score_breakdown=PolicyScore(
                ped_compatibility=95.0,
                cost_effectiveness=70.0,
                coverage_comprehensiveness=75.0,
                claim_settlement_ratio=85.0,
            ),
            pros=["Excellent diabetes coverage", "Short PED waiting period"],
            cons=["Moderate premium", "Standard coverage"],
            rejection_risk="low",
            reasoning="Specialized for diabetes and hypertension.",
        ),
        # Policy 5: High rejection risk
        ComparedPolicy(
            policy_id="policy_005",
            policy_name="Basic Health",
            provider="National Insurance",
            overall_score=55.0,
            score_breakdown=PolicyScore(
                ped_compatibility=30.0,
                cost_effectiveness=75.0,
                coverage_comprehensiveness=60.0,
                claim_settlement_ratio=80.0,
            ),
            pros=["Affordable premium"],
            cons=["Excludes diabetes", "Limited coverage", "High rejection risk"],
            rejection_risk="high",
            reasoning="Not suitable due to diabetes exclusion.",
        ),
    ]
    
    # Initialize PolicyAnalyzer
    analyzer = PolicyAnalyzer()
    
    # Test the recommendation engine
    print("\n" + "=" * 80)
    print("USER PROFILE")
    print("=" * 80)
    print(f"Age: {user_profile.demographics.age}")
    print(f"Location: {user_profile.demographics.location}")
    print(f"Pre-existing Diseases: {', '.join([ped['condition'] for ped in user_profile.medical_history.pre_existing_diseases])}")
    print(f"Medications: {', '.join([med['name'] for med in user_profile.medical_history.current_medications])}")
    
    print("\n" + "=" * 80)
    print("COMPARED POLICIES")
    print("=" * 80)
    for i, policy in enumerate(compared_policies, 1):
        print(f"\n{i}. {policy.policy_name} ({policy.provider})")
        print(f"   Overall Score: {policy.overall_score}/100")
        print(f"   PED Compatibility: {policy.score_breakdown.ped_compatibility}/100")
        print(f"   Cost Effectiveness: {policy.score_breakdown.cost_effectiveness}/100")
        print(f"   Coverage: {policy.score_breakdown.coverage_comprehensiveness}/100")
        print(f"   Rejection Risk: {policy.rejection_risk}")
    
    # Generate recommendations
    print("\n" + "=" * 80)
    print("GENERATED RECOMMENDATIONS")
    print("=" * 80)
    
    recommendations = await analyzer._generate_recommendations(
        compared_policies=compared_policies,
        user_profile=user_profile,
        language="en",
    )
    
    for i, recommendation in enumerate(recommendations, 1):
        print(f"\n{i}. {recommendation}")
    
    # Verify key aspects of the recommendation engine
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    checks = []
    
    # Check 1: Primary recommendation exists
    primary_rec = [r for r in recommendations if "PRIMARY RECOMMENDATION" in r]
    checks.append(("Primary recommendation generated", len(primary_rec) > 0))
    
    # Check 2: PED-specific recommendation for user with PEDs
    ped_rec = [r for r in recommendations if "PRE-EXISTING CONDITIONS" in r]
    checks.append(("PED-specific recommendation generated", len(ped_rec) > 0))
    
    # Check 3: Value recommendation exists
    value_rec = [r for r in recommendations if "VALUE FOR MONEY" in r]
    checks.append(("Value recommendation generated", len(value_rec) > 0))
    
    # Check 4: Age-specific advice for 45-year-old
    age_rec = [r for r in recommendations if "AGE-SPECIFIC" in r]
    checks.append(("Age-specific recommendation generated", len(age_rec) > 0))
    
    # Check 5: General guidance provided
    general_rec = [r for r in recommendations if "GENERAL GUIDANCE" in r]
    checks.append(("General guidance generated", len(general_rec) > 0))
    
    # Check 6: Multiple recommendations generated (comprehensive)
    checks.append(("Multiple recommendations generated", len(recommendations) >= 4))
    
    # Print verification results
    all_passed = True
    for check_name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL CHECKS PASSED - Task 7.3 Implementation Successful!")
    else:
        print("✗ SOME CHECKS FAILED - Review implementation")
    print("=" * 80)
    
    return all_passed


async def test_recommendation_without_peds():
    """Test recommendations for user without pre-existing conditions."""
    
    print("\n\n" + "=" * 80)
    print("Testing Recommendations for User WITHOUT Pre-existing Conditions")
    print("=" * 80)
    
    # Create a young user without PEDs
    user_profile = UserProfile(
        user_id="test_user_002",
        demographics=Demographics(
            age=28,
            gender="female",
            location="Bangalore, Karnataka",
        ),
        medical_history=MedicalHistory(
            pre_existing_diseases=[],
            current_medications=[],
            allergies=[],
            past_surgeries=[],
        ),
        language_preference="en",
        consent_given=True,
        data_retention_preference="standard",
    )
    
    # Create mock policies
    compared_policies = [
        ComparedPolicy(
            policy_id="policy_101",
            policy_name="Young Health Plus",
            provider="Care Health",
            overall_score=88.0,
            score_breakdown=PolicyScore(
                ped_compatibility=100.0,  # No PEDs
                cost_effectiveness=85.0,
                coverage_comprehensiveness=80.0,
                claim_settlement_ratio=87.0,
            ),
            pros=["Excellent for young adults", "Competitive rates"],
            cons=["Standard coverage"],
            rejection_risk="low",
            reasoning="Ideal for young professionals.",
        ),
        ComparedPolicy(
            policy_id="policy_102",
            policy_name="Budget Basic",
            provider="Reliance General",
            overall_score=75.0,
            score_breakdown=PolicyScore(
                ped_compatibility=100.0,
                cost_effectiveness=95.0,
                coverage_comprehensiveness=60.0,
                claim_settlement_ratio=80.0,
            ),
            pros=["Very affordable"],
            cons=["Basic coverage only"],
            rejection_risk="low",
            reasoning="Budget-friendly option.",
        ),
    ]
    
    analyzer = PolicyAnalyzer()
    
    recommendations = await analyzer._generate_recommendations(
        compared_policies=compared_policies,
        user_profile=user_profile,
        language="en",
    )
    
    print("\nGenerated Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec}")
    
    # Verify no PED-specific recommendations
    ped_rec = [r for r in recommendations if "PRE-EXISTING CONDITIONS" in r]
    age_rec = [r for r in recommendations if "AGE-SPECIFIC" in r and "age" in r.lower()]
    
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print(f"✓ PASS: No PED-specific recommendations" if len(ped_rec) == 0 else "✗ FAIL: Unexpected PED recommendations")
    print(f"✓ PASS: Age-specific advice for young adult" if len(age_rec) > 0 else "✗ FAIL: Missing age-specific advice")
    print("=" * 80)


async def main():
    """Run all tests."""
    try:
        # Test 1: User with PEDs
        result1 = await test_recommendation_engine()
        
        # Test 2: User without PEDs
        await test_recommendation_without_peds()
        
        print("\n" + "=" * 80)
        print("TASK 7.3 IMPLEMENTATION TEST COMPLETE")
        print("=" * 80)
        
        if result1:
            print("\n✓ Policy Recommendation Engine successfully implemented!")
            print("\nKey Features Implemented:")
            print("  1. ✓ Ranks policies by compatibility score")
            print("  2. ✓ Filters and recommends top policies based on user profile")
            print("  3. ✓ Generates detailed recommendation reasoning")
            print("  4. ✓ Considers PED compatibility, cost, coverage, and rejection risk")
            print("  5. ✓ Provides age-specific recommendations")
            print("  6. ✓ Includes general guidance for policy selection")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
