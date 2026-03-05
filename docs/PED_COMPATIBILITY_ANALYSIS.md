# PED Compatibility Analysis

## Overview

The PED (Pre-Existing Disease) Compatibility Analysis feature helps users understand how their medical history affects insurance policy acceptance. This feature analyzes pre-existing conditions and current medications against insurance policies to provide:

- Detailed analysis of each pre-existing disease
- Medication implications for policy acceptance
- Rejection probability scores with explanations
- Compatible policy recommendations
- Actionable recommendations for improving acceptance chances

## Requirements Validated

This implementation validates the following requirements:

- **Requirement 2.1**: Analyze each insurance provider's policy regarding specific PED conditions
- **Requirement 2.2**: Identify policies that explicitly exclude the user's conditions
- **Requirement 2.3**: Provide rejection probability score with explanation
- **Requirement 2.4**: Recommend insurance providers with higher acceptance likelihood
- **Requirement 2.5**: Check if medications indicate conditions that might affect policy acceptance

## Features

### 1. Pre-Existing Disease Analysis

For each pre-existing disease, the system analyzes:

- **Exclusion Status**: Whether the condition is explicitly excluded by the policy
- **Waiting Period**: How long before the condition is covered (if applicable)
- **Coverage Details**: Specific coverage information for the condition
- **Rejection Risk**: Risk level (low, medium, high) for policy rejection

### 2. Medication Analysis

The system uses LLM-powered analysis to:

- Identify medical conditions implied by medications
- Assess how medications affect policy acceptance
- Determine risk levels for each medication
- Provide impact statements on acceptance probability

### 3. Rejection Probability Calculation

The system calculates an overall rejection probability (0-1) based on:

- Number of excluded conditions
- Severity of pre-existing diseases
- Medication risk factors
- Policy waiting periods
- Historical acceptance patterns

### 4. Compatible Policy Recommendations

The system identifies and recommends policies with:

- Higher acceptance likelihood for the user's profile
- Compatibility scores (0-100)
- Key benefits specific to the user's conditions
- Limitations and restrictions
- Acceptance likelihood ratings (high, medium, low)

### 5. Actionable Recommendations

The system provides specific recommendations such as:

- Which policies to apply to
- Which policies to avoid
- How to improve acceptance chances
- Disclosure best practices
- Alternative coverage options

## Usage

### Basic Usage

```python
from healthcare_insurance_platform.services.policy_analyzer import PolicyAnalyzer

# Initialize the analyzer
analyzer = PolicyAnalyzer()

# Analyze PED compatibility
report = await analyzer.analyze_ped_compatibility(
    ped_list=["Type 2 Diabetes", "Hypertension"],
    medications=["Metformin", "Amlodipine"],
    policy_id=None,  # Analyze all policies
    language="en"
)

# Access results
print(f"Rejection Probability: {report.overall_rejection_probability * 100:.1f}%")
print(f"Compatible Policies: {len(report.compatible_policies)}")
```

### Analyzing a Specific Policy

```python
# Analyze against a specific policy
report = await analyzer.analyze_ped_compatibility(
    ped_list=["Asthma"],
    medications=["Salbutamol"],
    policy_id="policy_123",  # Specific policy ID
    language="en"
)
```

### Multilingual Support

```python
# Get results in Hindi
report = await analyzer.analyze_ped_compatibility(
    ped_list=["मधुमेह", "उच्च रक्तचाप"],
    medications=["मेटफॉर्मिन"],
    language="hi"
)
```

## Data Models

### CompatibilityReport

The main output model containing:

```python
class CompatibilityReport(BaseModel):
    report_id: str
    user_profile_id: str
    policy_id: Optional[str]
    ped_analyses: List[PEDAnalysis]
    medication_analyses: List[MedicationAnalysis]
    overall_rejection_probability: float  # 0-1
    rejection_probability_explanation: str
    compatible_policies: List[CompatiblePolicy]
    recommendations: List[str]
    explanation: str
    citations: List[str]
    language: str
    generated_at: datetime
```

### PEDAnalysis

Analysis of a specific pre-existing disease:

```python
class PEDAnalysis(BaseModel):
    condition: str
    is_excluded: bool
    waiting_period_days: Optional[int]
    coverage_details: str
    rejection_risk: str  # low, medium, high
```

### MedicationAnalysis

Analysis of medication implications:

```python
class MedicationAnalysis(BaseModel):
    medication: str
    implied_conditions: List[str]
    impact_on_acceptance: str
    risk_level: str  # low, medium, high
```

### CompatiblePolicy

Recommended compatible policy:

```python
class CompatiblePolicy(BaseModel):
    policy_id: str
    policy_name: str
    provider: str
    compatibility_score: float  # 0-100
    acceptance_likelihood: str  # high, medium, low
    key_benefits: List[str]
    limitations: List[str]
```

## Algorithm Details

### Rejection Probability Calculation

The rejection probability is calculated using a weighted formula:

1. **Base Probability**: Calculated from exclusion rate
   - `exclusion_rate = excluded_conditions / total_conditions`
   - `base_probability = exclusion_rate * 0.7`

2. **Medication Adjustment**: Added based on medication risks
   - High-risk medications: +15% each
   - Medium-risk medications: +8% each

3. **Waiting Period Adjustment**: Added for long waiting periods
   - Medium-risk PEDs with long waiting periods: +20%

4. **Final Probability**: `min(1.0, base + medication_adj + waiting_adj)`

### Compatibility Scoring

Policy compatibility is scored (0-100) based on:

1. **Non-exclusion Rate**: Percentage of conditions not excluded
2. **Waiting Period Penalty**: 15% reduction for waiting periods > 3 years
3. **Coverage Amount Bonus**: Higher scores for better coverage

### Risk Level Determination

- **High Risk**: Condition is explicitly excluded
- **Medium Risk**: Long waiting period (> 3 years)
- **Low Risk**: Covered with reasonable waiting period or no waiting period

## Error Handling

The system handles various error conditions:

- **No PEDs or Medications**: Returns error requiring at least one input
- **Policy Not Found**: Returns error if specific policy ID doesn't exist
- **No Policies Available**: Returns error if knowledge base is empty
- **LLM Analysis Failure**: Falls back to default medication analysis
- **Translation Failure**: Returns English text with warning

## Examples

See `examples/ped_compatibility_example.py` for complete working examples.

## Integration

### With Policy Comparison

```python
# First compare policies
comparison = await analyzer.compare_plans(
    user_profile=user_profile,
    filters=filters,
    language="en"
)

# Then analyze PED compatibility for top policy
ped_report = await analyzer.analyze_ped_compatibility(
    ped_list=user_profile.get_ped_list(),
    medications=user_profile.get_medications(),
    policy_id=comparison.compared_policies[0].policy_id,
    language="en"
)
```

### With User Profile

```python
# Extract PEDs and medications from user profile
user_profile = UserProfile(...)
ped_list = user_profile.get_ped_list()
medications = user_profile.get_medications()

# Analyze compatibility
report = await analyzer.analyze_ped_compatibility(
    ped_list=ped_list,
    medications=medications,
    language=user_profile.language_preference
)
```

## Performance Considerations

- **LLM Calls**: One LLM call per medication for analysis
- **Policy Retrieval**: Retrieves up to 20 policies for comparison
- **Caching**: Consider caching medication analyses for common drugs
- **Batch Processing**: Process multiple medications in parallel when possible

## Future Enhancements

Potential improvements for future versions:

1. **Historical Data**: Use actual claim acceptance data for more accurate predictions
2. **Machine Learning**: Train models on historical acceptance patterns
3. **Medication Database**: Pre-computed medication implications database
4. **Real-time Updates**: Monitor policy changes and update analyses
5. **Comparative Analysis**: Compare rejection probabilities across multiple policies
6. **Risk Mitigation**: Suggest specific actions to reduce rejection risk

## Testing

The implementation should be tested with:

- Various combinations of PEDs and medications
- Edge cases (no PEDs, no medications, all excluded)
- Different policy types and providers
- Multilingual scenarios
- Error conditions (missing policies, LLM failures)

## References

- Design Document: `.kiro/specs/healthcare-insurance-intelligence/design.md`
- Requirements: `.kiro/specs/healthcare-insurance-intelligence/requirements.md`
- Task List: `.kiro/specs/healthcare-insurance-intelligence/tasks.md`
