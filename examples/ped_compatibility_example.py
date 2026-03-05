"""
Example: PED Compatibility Analysis

This example demonstrates how to use the PolicyAnalyzer service to analyze
pre-existing disease (PED) compatibility with insurance policies.

Requirements validated: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import asyncio
from healthcare_insurance_platform.services.policy_analyzer import PolicyAnalyzer


async def main():
    """Demonstrate PED compatibility analysis."""
    
    # Initialize the PolicyAnalyzer service
    analyzer = PolicyAnalyzer()
    
    print("=" * 80)
    print("PED Compatibility Analysis Example")
    print("=" * 80)
    print()
    
    # Example 1: Analyze PED compatibility with medications
    print("Example 1: Analyzing PED compatibility with medications")
    print("-" * 80)
    
    ped_list = [
        "Type 2 Diabetes",
        "Hypertension",
        "Asthma"
    ]
    
    medications = [
        "Metformin",
        "Amlodipine",
        "Salbutamol inhaler"
    ]
    
    print(f"Pre-existing Diseases: {', '.join(ped_list)}")
    print(f"Current Medications: {', '.join(medications)}")
    print()
    
    try:
        # Analyze PED compatibility across all policies
        report = await analyzer.analyze_ped_compatibility(
            ped_list=ped_list,
            medications=medications,
            policy_id=None,  # Analyze all policies
            language="en"
        )
        
        print(f"Report ID: {report.report_id}")
        print(f"Generated at: {report.generated_at}")
        print()
        
        # Display PED analyses
        print("Pre-existing Disease Analysis:")
        print("-" * 80)
        for ped_analysis in report.ped_analyses:
            print(f"\nCondition: {ped_analysis.condition}")
            print(f"  Excluded: {'Yes' if ped_analysis.is_excluded else 'No'}")
            if ped_analysis.waiting_period_days:
                years = ped_analysis.waiting_period_days // 365
                days = ped_analysis.waiting_period_days % 365
                print(f"  Waiting Period: {years} years, {days} days")
            print(f"  Rejection Risk: {ped_analysis.rejection_risk.upper()}")
            print(f"  Coverage Details: {ped_analysis.coverage_details}")
        
        # Display medication analyses
        if report.medication_analyses:
            print("\n\nMedication Analysis:")
            print("-" * 80)
            for med_analysis in report.medication_analyses:
                print(f"\nMedication: {med_analysis.medication}")
                print(f"  Implied Conditions: {', '.join(med_analysis.implied_conditions)}")
                print(f"  Risk Level: {med_analysis.risk_level.upper()}")
                print(f"  Impact: {med_analysis.impact_on_acceptance}")
        
        # Display rejection probability
        print("\n\nRejection Probability Analysis:")
        print("-" * 80)
        rejection_pct = report.overall_rejection_probability * 100
        print(f"Overall Rejection Probability: {rejection_pct:.1f}%")
        print(f"\nExplanation:")
        print(report.rejection_probability_explanation)
        
        # Display compatible policies
        if report.compatible_policies:
            print("\n\nCompatible Policies (Higher Acceptance Likelihood):")
            print("-" * 80)
            for i, policy in enumerate(report.compatible_policies[:3], 1):
                print(f"\n{i}. {policy.policy_name} ({policy.provider})")
                print(f"   Compatibility Score: {policy.compatibility_score}/100")
                print(f"   Acceptance Likelihood: {policy.acceptance_likelihood.upper()}")
                print(f"   Key Benefits:")
                for benefit in policy.key_benefits:
                    print(f"     • {benefit}")
                if policy.limitations:
                    print(f"   Limitations:")
                    for limitation in policy.limitations:
                        print(f"     • {limitation}")
        
        # Display recommendations
        print("\n\nRecommendations:")
        print("-" * 80)
        for i, recommendation in enumerate(report.recommendations, 1):
            print(f"{i}. {recommendation}")
        
        # Display overall explanation
        print("\n\nOverall Explanation:")
        print("-" * 80)
        print(report.explanation)
        
        print("\n" + "=" * 80)
        print("Analysis Complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    # Example 2: Analyze specific policy
    print("\n\n")
    print("=" * 80)
    print("Example 2: Analyzing specific policy")
    print("-" * 80)
    
    try:
        # Analyze a specific policy (if available)
        report = await analyzer.analyze_ped_compatibility(
            ped_list=["Diabetes"],
            medications=["Insulin"],
            policy_id="policy_001",  # Specific policy
            language="en"
        )
        
        print(f"Analyzed Policy: {report.policy_id}")
        print(f"Rejection Probability: {report.overall_rejection_probability * 100:.1f}%")
        print(f"\nTop Recommendation: {report.recommendations[0]}")
        
    except ValueError as e:
        print(f"Note: {e}")
        print("(This is expected if the specific policy doesn't exist in the knowledge base)")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
