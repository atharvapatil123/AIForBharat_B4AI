# Policy Comparison Functionality

## Overview

The Policy Analyzer service provides comprehensive insurance policy comparison functionality that helps users make informed decisions about health insurance plans. The service analyzes policies based on user profiles, medical history, and preferences, providing scored comparisons with detailed explanations.

## Features

### 1. Policy Retrieval with Filters

The service retrieves policies from the knowledge base using semantic search and applies various filters:

- **Coverage Amount**: Filter by minimum/maximum coverage
- **Premium Range**: Filter by affordable premium limits
- **Policy Type**: Filter by individual, family, or senior citizen policies
- **Provider**: Filter by specific insurance companies
- **Required Benefits**: Search for policies covering specific medical conditions or treatments

### 2. Intelligent Scoring Algorithm

Each policy is scored on four key factors:

#### PED Compatibility (40% weight)
- Analyzes compatibility with user's pre-existing diseases
- Checks for explicit exclusions
- Considers waiting periods for PED coverage
- Higher score = better coverage for user's conditions

#### Cost Effectiveness (30% weight)
- Evaluates premium relative to coverage amount
- Adjusts expectations based on user age
- Considers value for money
- Higher score = better value

#### Coverage Comprehensiveness (20% weight)
- Assesses breadth of inclusions
- Checks for comprehensive medical coverage
- Evaluates quality of benefits
- Higher score = more comprehensive coverage

#### Claim Settlement Ratio (10% weight)
- Considers insurer's track record
- Evaluates reliability of claim processing
- Higher score = better claim settlement history

### 3. Structured Comparison Results

The service generates detailed comparison results including:

- **Overall Score**: Weighted score (0-100) for each policy
- **Score Breakdown**: Individual scores for each factor
- **Pros and Cons**: Clear advantages and disadvantages
- **Rejection Risk**: Low/Medium/High risk assessment
- **Reasoning**: Detailed explanation of scores
- **Recommendations**: Personalized policy suggestions
- **Citations**: Source references for transparency

### 4. Multilingual Support

All comparison results can be generated in multiple languages:
- English (en)
- Hindi (hi)
- Tamil (ta)
- Telugu (te)
- Bengali (bn)
- Marathi (mr)
- Gujarati (gu)

Technical terms are preserved with explanations in the target language.

### 5. Missing Data Handling

The service gracefully handles incomplete policy information:
- Clearly indicates missing data fields
- Provides partial comparisons when possible
- Does not fail the entire comparison due to missing data
- Warns users about incomplete information

## Usage

### Basic Usage

```python
from healthcare_insurance_platform.services.policy_analyzer import (
    PolicyAnalyzer,
    PolicyFilters,
)
from healthcare_insurance_platform.models.user_profile import UserProfile

# Initialize analyzer
analyzer = PolicyAnalyzer()

# Define filters
filters = PolicyFilters(
    min_coverage=500000,
    max_premium=25000,
    policy_type="individual",
    required_benefits=["hospitalization", "diabetes coverage"],
)

# Compare policies
result = await analyzer.compare_plans(
    user_profile=user_profile,
    filters=filters,
    language="en",
    max_policies=10,
)

# Access results
top_policy = result.compared_policies[0]
print(f"Top recommendation: {top_policy.policy_name}")
print(f"Score: {top_policy.overall_score}/100")
print(f"Rejection risk: {top_policy.rejection_risk}")
```

### With Multilingual Output

```python
# Request results in Hindi
result = await analyzer.compare_plans(
    user_profile=user_profile,
    filters=filters,
    language="hi",  # Hindi output
    max_policies=5,
)

# Recommendations will be in Hindi
for recommendation in result.recommendations:
    print(recommendation)
```

### Accessing Specific Results

```python
# Get top 3 policies
top_3 = result.get_top_policies(n=3)

# Get only low-risk policies
low_risk = result.get_low_risk_policies()

# Access score breakdown
for policy in result.compared_policies:
    print(f"{policy.policy_name}:")
    print(f"  PED Score: {policy.score_breakdown.ped_compatibility}")
    print(f"  Cost Score: {policy.score_breakdown.cost_effectiveness}")
    print(f"  Coverage Score: {policy.score_breakdown.coverage_comprehensiveness}")
```

## Requirements Validation

This implementation validates the following requirements:

### Requirement 1.1: Policy Retrieval
✓ Retrieves policy documents from multiple insurance providers in the Knowledge Base
✓ Uses semantic search for intelligent policy matching
✓ Applies filters for targeted search

### Requirement 1.2: Structured Comparison
✓ Presents key features: coverage amount, premium, waiting periods, exclusions
✓ Provides structured format with scores and breakdowns
✓ Includes pros/cons for each policy

### Requirement 1.3: Filtering Support
✓ Supports filtering by coverage amount range
✓ Supports filtering by premium range
✓ Supports filtering by specific benefits
✓ Supports filtering by policy type and provider

### Requirement 1.4: Multilingual Display
✓ Displays comparison results in user's selected language
✓ Supports all required Indian languages
✓ Preserves technical terms with explanations

### Requirement 1.5: Missing Data Handling
✓ Indicates missing data clearly
✓ Does not fail comparison due to incomplete information
✓ Provides partial results when possible

## Architecture

### Dependencies

The Policy Analyzer depends on:

1. **Knowledge Base Service**: For policy document retrieval and semantic search
2. **LLM Engine**: For generating explanations and reasoning
3. **Translation Service**: For multilingual output support

### Data Flow

```
User Profile + Filters
        ↓
Policy Retrieval (Knowledge Base)
        ↓
Policy Scoring (Multiple Factors)
        ↓
Pros/Cons Generation
        ↓
Recommendations Generation
        ↓
Translation (if needed)
        ↓
Comparison Result
```

### Scoring Algorithm

```
Overall Score = (PED Score × 0.4) + 
                (Cost Score × 0.3) + 
                (Coverage Score × 0.2) + 
                (Claim Ratio × 0.1)
```

## Error Handling

The service handles various error conditions:

- **No Policies Found**: Raises ValueError with helpful message
- **Invalid Language**: Validates language codes
- **Missing User Profile Data**: Uses defaults where appropriate
- **Knowledge Base Unavailable**: Provides clear error messages

## Performance Considerations

- Retrieves 2× requested policies initially for filtering
- Deduplicates results by policy ID
- Limits semantic search results to prevent overload
- Caches policy documents when possible

## Future Enhancements

Potential improvements for future versions:

1. **Real-time Claim Settlement Data**: Integrate actual claim settlement ratios
2. **User Reviews**: Include customer satisfaction scores
3. **Network Hospital Coverage**: Consider hospital network in scoring
4. **Premium Calculators**: Provide personalized premium estimates
5. **Comparison History**: Track user's previous comparisons
6. **Side-by-Side View**: Enhanced visualization of policy differences

## See Also

- [Knowledge Base Documentation](./KNOWLEDGE_BASE.md)
- [LLM Integration Guide](./LLM_INTEGRATION.md)
- [Translation Service Guide](./TRANSLATION_SERVICE.md)
- [Example Usage](../examples/policy_comparison_example.py)
