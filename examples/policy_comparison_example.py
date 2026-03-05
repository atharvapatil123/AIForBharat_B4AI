"""Example usage of Policy Analyzer service for comparing insurance policies.

This example demonstrates how to use the PolicyAnalyzer service to compare
multiple insurance policies based on a user's profile and preferences.
"""

import asyncio
from datetime import date

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


async def main():
    """Example: Compare insurance policies for a user with pre-existing conditions."""
    
    # Step 1: Create a user profile
    user_profile = UserProfile(
        user_id="user_123",
        demographics=Demographics(
            age=45,
            gender="male",
            location="Mumbai, Maharashtra",
        ),
        medical_history=MedicalHistory(
            pre_existing_diseases=[
                PreExistingDisease(
                    condition="Hypertension",
                    diagnosis_date=date(2020, 3, 15),
                    severity="moderate",
                ),
                PreExistingDisease(
                    condition="Diabetes Mellitus Type 2",
                    diagnosis_date=date(2019, 8, 22),
                    severity="controlled",
                ),
            ],
            current_medications=[],
            allergies=[],
            past_surgeries=[],
        ),
        language_preference="en",
        consent_given=True,
        data_retention_preference="standard",
    )
    
    # Step 2: Define filters for policy search
    filters = PolicyFilters(
        min_coverage=500000,  # Minimum 5 lakh coverage
        max_premium=25000,    # Maximum 25k annual premium
        policy_type="individual",
        required_benefits=[
            "hospitalization",
            "diabetes coverage",
            "cardiovascular coverage",
        ],
    )
    
    # Step 3: Initialize Policy Analyzer
    analyzer = PolicyAnalyzer()
    
    # Step 4: Compare policies
    print("Comparing insurance policies...")
    print(f"User: {user_profile.demographics.age} year old {user_profile.demographics.gender}")
    print(f"Pre-existing conditions: {', '.join([ped.condition for ped in user_profile.medical_history.pre_existing_diseases])}")
    print(f"Filters: Coverage {filters.min_coverage:,} - Premium max {filters.max_premium:,}")
    print("\n" + "="*80 + "\n")
    
    try:
        comparison_result = await analyzer.compare_plans(
            user_profile=user_profile,
            filters=filters,
            language="en",
            max_policies=5,
        )
        
        # Step 5: Display results
        print(f"Comparison Results (Request ID: {comparison_result.request_id})")
        print(f"Generated at: {comparison_result.generated_at}")
        print(f"\nCompared {len(comparison_result.compared_policies)} policies\n")
        
        # Display each policy
        for i, policy in enumerate(comparison_result.compared_policies, 1):
            print(f"{i}. {policy.policy_name} ({policy.provider})")
            print(f"   Overall Score: {policy.overall_score}/100")
            print(f"   Rejection Risk: {policy.rejection_risk.upper()}")
            print(f"\n   Score Breakdown:")
            print(f"   - PED Compatibility: {policy.score_breakdown.ped_compatibility}/100")
            print(f"   - Cost Effectiveness: {policy.score_breakdown.cost_effectiveness}/100")
            print(f"   - Coverage: {policy.score_breakdown.coverage_comprehensiveness}/100")
            print(f"   - Claim Settlement: {policy.score_breakdown.claim_settlement_ratio}/100")
            
            print(f"\n   Pros:")
            for pro in policy.pros:
                print(f"   ✓ {pro}")
            
            print(f"\n   Cons:")
            for con in policy.cons:
                print(f"   ✗ {con}")
            
            print(f"\n   Reasoning: {policy.reasoning}")
            print("\n" + "-"*80 + "\n")
        
        # Display recommendations
        print("Recommendations:")
        for i, rec in enumerate(comparison_result.recommendations, 1):
            print(f"{i}. {rec}")
        
        print(f"\n{comparison_result.explanation}")
        
        # Display top 3 policies
        print("\n" + "="*80)
        print("TOP 3 RECOMMENDED POLICIES:")
        print("="*80 + "\n")
        
        top_policies = comparison_result.get_top_policies(n=3)
        for i, policy in enumerate(top_policies, 1):
            print(f"{i}. {policy.policy_name}")
            print(f"   Score: {policy.overall_score}/100")
            print(f"   Risk: {policy.rejection_risk}")
            print()
        
        # Display low-risk policies
        low_risk = comparison_result.get_low_risk_policies()
        if low_risk:
            print("="*80)
            print("LOW REJECTION RISK POLICIES:")
            print("="*80 + "\n")
            for policy in low_risk:
                print(f"- {policy.policy_name} (Score: {policy.overall_score}/100)")
        
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def multilingual_example():
    """Example: Compare policies with Hindi language output."""
    
    # Create user profile
    user_profile = UserProfile(
        user_id="user_456",
        demographics=Demographics(
            age=35,
            gender="female",
            location="Jaipur, Rajasthan",
        ),
        medical_history=MedicalHistory(
            pre_existing_diseases=[],
            current_medications=[],
            allergies=[],
            past_surgeries=[],
        ),
        language_preference="hi",  # Hindi
        consent_given=True,
        data_retention_preference="standard",
    )
    
    # Define filters
    filters = PolicyFilters(
        min_coverage=300000,
        max_premium=15000,
        policy_type="family",
    )
    
    # Initialize analyzer
    analyzer = PolicyAnalyzer()
    
    # Compare policies in Hindi
    print("\nComparing policies with Hindi output...")
    
    try:
        comparison_result = await analyzer.compare_plans(
            user_profile=user_profile,
            filters=filters,
            language="hi",  # Request Hindi output
            max_policies=3,
        )
        
        print(f"\nLanguage: {comparison_result.language}")
        print(f"Policies compared: {len(comparison_result.compared_policies)}")
        print(f"\nExplanation (in Hindi):")
        print(comparison_result.explanation)
        
        print(f"\nRecommendations (in Hindi):")
        for rec in comparison_result.recommendations:
            print(f"- {rec}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("="*80)
    print("POLICY COMPARISON EXAMPLE")
    print("="*80 + "\n")
    
    # Run basic example
    asyncio.run(main())
    
    # Run multilingual example
    print("\n\n" + "="*80)
    print("MULTILINGUAL EXAMPLE")
    print("="*80 + "\n")
    asyncio.run(multilingual_example())
