"""Standalone test for Policy Analyzer to verify basic functionality."""

import asyncio
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from healthcare_insurance_platform.models.policy import (
    DocumentRequirement,
    ParsedClause,
    PolicyDocument,
    WaitingPeriod,
)
from healthcare_insurance_platform.models.user_profile import (
    Demographics,
    MedicalHistory,
    PreExistingDisease,
    UserProfile,
)
from healthcare_insurance_platform.services.policy_analyzer import (
    PolicyAnalyzer,
    PolicyFilters,
)


def create_sample_user_profile():
    """Create a sample user profile for testing."""
    return UserProfile(
        user_id="user123",
        demographics=Demographics(
            age=35,
            gender="male",
            location="Mumbai",
        ),
        medical_history=MedicalHistory(
            pre_existing_diseases=[
                PreExistingDisease(
                    condition="Hypertension",
                    diagnosis_date=date(2020, 1, 1),
                    severity="moderate",
                ),
                PreExistingDisease(
                    condition="Diabetes",
                    diagnosis_date=date(2019, 6, 15),
                    severity="mild",
                ),
            ],
            current_medications=[],
            allergies=[],
            past_surgeries=[],
        ),
        language_preference="en",
        consent_given=True,
    )


def create_sample_policy():
    """Create a sample policy document for testing."""
    return PolicyDocument(
        policy_id="policy123",
        provider_id="provider1",
        policy_name="Comprehensive Health Plan",
        policy_type="individual",
        version="1.0",
        effective_date=date.today(),
        coverage_amount=500000.0,
        premium=12000.0,
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
            "Day care procedures",
        ],
        exclusions=[
            "Cosmetic procedures",
            "Dental treatment",
            "Infertility treatment",
        ],
        ped_policy="Pre-existing diseases covered after 2-year waiting period",
        claim_process="Submit claim with required documents within 30 days",
        document_requirements=[
            DocumentRequirement(
                claim_type="hospitalization",
                documents=["Hospital discharge summary", "Medical bills", "Diagnostic reports"],
            ),
        ],
        full_text="Sample policy document text",
        parsed_clauses=[
            ParsedClause(
                clause_type="coverage",
                text="Coverage amount: Rs. 5,00,000",
                importance="critical",
            ),
        ],
    )


async def test_basic_comparison():
    """Test basic policy comparison functionality."""
    print("Testing Policy Analyzer - Basic Comparison")
    print("=" * 60)
    
    # Create test data
    user_profile = create_sample_user_profile()
    sample_policy = create_sample_policy()
    
    # Create analyzer with mocked dependencies
    mock_kb = MagicMock()
    mock_llm = MagicMock()
    mock_translation = MagicMock()
    
    analyzer = PolicyAnalyzer(
        knowledge_base=mock_kb,
        llm_engine=mock_llm,
        translation_service=mock_translation,
    )
    
    # Mock knowledge base to return sample policy
    mock_kb.search_policies = AsyncMock(
        return_value=[
            {
                'policy_id': sample_policy.policy_id,
                'policy_name': sample_policy.policy_name,
                'provider_id': sample_policy.provider_id,
                'policy_type': sample_policy.policy_type,
                'content': sample_policy.full_text,
                'metadata': {
                    'coverage_amount': sample_policy.coverage_amount,
                    'premium': sample_policy.premium,
                    'version': sample_policy.version,
                },
            }
        ]
    )
    
    # Mock translation service
    mock_translation.translate = AsyncMock(
        side_effect=lambda text, **kwargs: MagicMock(translated_content=text)
    )
    
    # Execute comparison
    print(f"\nUser Profile: {user_profile.user_id}")
    print(f"Age: {user_profile.demographics.age}")
    print(f"PEDs: {user_profile.get_ped_list()}")
    
    result = await analyzer.compare_plans(
        user_profile=user_profile,
        filters=None,
        language="en",
        max_policies=10,
    )
    
    # Display results
    print(f"\n✓ Comparison completed successfully!")
    print(f"  Request ID: {result.request_id}")
    print(f"  Policies compared: {len(result.compared_policies)}")
    print(f"  Language: {result.language}")
    
    # Display first policy details
    if result.compared_policies:
        policy = result.compared_policies[0]
        print(f"\n  Top Policy: {policy.policy_name}")
        print(f"  Overall Score: {policy.overall_score}/100")
        print(f"  Rejection Risk: {policy.rejection_risk}")
        print(f"\n  Score Breakdown:")
        print(f"    - PED Compatibility: {policy.score_breakdown.ped_compatibility}/100")
        print(f"    - Cost Effectiveness: {policy.score_breakdown.cost_effectiveness}/100")
        print(f"    - Coverage: {policy.score_breakdown.coverage_comprehensiveness}/100")
        print(f"    - Claim Settlement: {policy.score_breakdown.claim_settlement_ratio}/100")
        
        print(f"\n  Pros ({len(policy.pros)}):")
        for pro in policy.pros:
            print(f"    + {pro}")
        
        print(f"\n  Cons ({len(policy.cons)}):")
        for con in policy.cons:
            print(f"    - {con}")
        
        print(f"\n  Reasoning:")
        print(f"    {policy.reasoning}")
    
    print(f"\n  Recommendations ({len(result.recommendations)}):")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"    {i}. {rec}")
    
    print(f"\n  Explanation:")
    print(f"    {result.explanation}")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    
    return result


def test_scoring_functions():
    """Test individual scoring functions."""
    print("\nTesting Scoring Functions")
    print("=" * 60)
    
    user_profile = create_sample_user_profile()
    sample_policy = create_sample_policy()
    
    analyzer = PolicyAnalyzer()
    
    # Test PED compatibility score
    ped_score = analyzer._calculate_ped_compatibility_score(sample_policy, user_profile)
    print(f"\n✓ PED Compatibility Score: {ped_score:.2f}/100")
    assert 0 <= ped_score <= 100, "PED score out of range"
    
    # Test cost effectiveness score
    cost_score = analyzer._calculate_cost_effectiveness_score(sample_policy, user_profile)
    print(f"✓ Cost Effectiveness Score: {cost_score:.2f}/100")
    assert 0 <= cost_score <= 100, "Cost score out of range"
    
    # Test coverage score
    coverage_score = analyzer._calculate_coverage_score(sample_policy)
    print(f"✓ Coverage Score: {coverage_score:.2f}/100")
    assert 0 <= coverage_score <= 100, "Coverage score out of range"
    
    # Test rejection risk
    rejection_risk = analyzer._calculate_rejection_risk(sample_policy, user_profile, ped_score)
    print(f"✓ Rejection Risk: {rejection_risk}")
    assert rejection_risk in ['low', 'medium', 'high'], "Invalid rejection risk"
    
    # Test pros/cons generation
    scores = {
        'ped': ped_score,
        'cost': cost_score,
        'coverage': coverage_score,
        'claim_ratio': 85.0,
    }
    pros, cons = analyzer._generate_pros_cons(sample_policy, user_profile, scores)
    print(f"✓ Generated {len(pros)} pros and {len(cons)} cons")
    assert len(pros) > 0, "Should have at least one pro"
    
    print("\n" + "=" * 60)
    print("✓ All scoring tests passed!")


def test_filters():
    """Test policy filters."""
    print("\nTesting Policy Filters")
    print("=" * 60)
    
    # Test creating filters
    filters = PolicyFilters(
        min_coverage=300000.0,
        max_premium=15000.0,
        policy_type="individual",
        required_benefits=["Hospitalization", "Surgery"],
    )
    
    print(f"\n✓ Created filters:")
    print(f"  Min Coverage: Rs. {filters.min_coverage:,.0f}")
    print(f"  Max Premium: Rs. {filters.max_premium:,.0f}")
    print(f"  Policy Type: {filters.policy_type}")
    print(f"  Required Benefits: {', '.join(filters.required_benefits)}")
    
    # Test optional filters
    empty_filters = PolicyFilters()
    print(f"\n✓ Created empty filters (all optional)")
    assert empty_filters.min_coverage is None
    assert len(empty_filters.required_benefits) == 0
    
    print("\n" + "=" * 60)
    print("✓ Filter tests passed!")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("POLICY ANALYZER STANDALONE TESTS")
    print("=" * 60)
    
    try:
        # Test 1: Scoring functions
        test_scoring_functions()
        
        # Test 2: Filters
        test_filters()
        
        # Test 3: Basic comparison (async)
        asyncio.run(test_basic_comparison())
        
        print("\n" + "=" * 60)
        print("✓✓✓ ALL TESTS PASSED SUCCESSFULLY! ✓✓✓")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
