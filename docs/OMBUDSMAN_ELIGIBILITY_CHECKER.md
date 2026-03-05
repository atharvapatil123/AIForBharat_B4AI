# Ombudsman Eligibility Checker

## Overview

The Ombudsman Eligibility Checker is part of the Ombudsman Advisor service that helps users determine if they are eligible to file complaints with the Insurance Ombudsman in India. The service validates eligibility based on three key criteria:

1. **Jurisdiction Validation**: Claim amount must be ≤ ₹20 lakh
2. **Deadline Calculation**: Complaint must be filed within 1 year of claim rejection
3. **Regional Office Routing**: Identifies the appropriate regional office based on user location

## Implementation

### Service: `OmbudsmanAdvisor`

Location: `healthcare_insurance_platform/services/ombudsman_advisor.py`

The service provides two main methods:

#### 1. `check_eligibility()`

Checks if a user is eligible to file a complaint with the Insurance Ombudsman.

**Parameters:**
- `claim_amount` (float): Claim amount in rupees
- `rejection_date` (str, optional): Date of claim rejection in ISO format (YYYY-MM-DD)
- `user_location` (str): User's location (city or state)
- `claim_id` (str, optional): Claim identifier
- `language` (str, optional): Language for output (default: "en")

**Returns:** `EligibilityResult` object containing:
- `is_eligible`: Boolean indicating overall eligibility
- `within_jurisdiction`: Whether claim amount is ≤ ₹20 lakh
- `within_deadline`: Whether complaint is within 1-year filing deadline
- `regional_office`: Details of the appropriate regional office
- `days_remaining`: Days remaining to file complaint
- `eligibility_reasons`: List of reasons for eligibility determination
- `explanation`: Detailed explanation of the result
- `next_steps`: Recommended actions for the user

**Example:**
```python
from healthcare_insurance_platform.services.ombudsman_advisor import OmbudsmanAdvisor

advisor = OmbudsmanAdvisor()

result = advisor.check_eligibility(
    claim_amount=1500000.0,  # ₹15 lakh
    rejection_date="2024-10-15",
    user_location="Mumbai",
    claim_id="CLM-2024-001"
)

if result.is_eligible:
    print(f"Eligible! File with: {result.get_office_name()}")
    print(f"Days remaining: {result.days_remaining}")
else:
    print(f"Not eligible: {result.explanation}")
```

#### 2. `generate_complaint_guidance()`

Generates comprehensive guidance for filing a complaint with the Ombudsman.

**Parameters:**
- `claim_id` (str): Claim identifier
- `claim_details` (dict): Dictionary with claim information
- `rejection_reason` (str): Insurer's rejection explanation
- `policy_id` (str): Policy identifier
- `language` (str, optional): Language for output (default: "en")

**Returns:** `ComplaintGuide` object containing:
- `filing_process`: Step-by-step filing instructions
- `required_documents`: List of required documents
- `argument_points`: Key points to support the complaint
- `expected_timeline`: Timeline for resolution
- `tips_and_warnings`: Important tips and common pitfalls

**Example:**
```python
guide = advisor.generate_complaint_guidance(
    claim_id="CLM-2024-001",
    claim_details={
        "claim_type": "hospitalization",
        "treatment": "Cardiac surgery",
        "amount": 1500000.0
    },
    rejection_reason="Pre-existing disease exclusion",
    policy_id="POL-2024-001"
)

print("Filing Process:")
for step in guide.filing_process:
    print(f"  - {step}")
```

## Eligibility Criteria

### 1. Jurisdiction Validation (Requirement 7.2)

The Insurance Ombudsman has jurisdiction over claims up to ₹20 lakh (₹2,000,000).

**Implementation:**
```python
def _check_jurisdiction(self, claim_amount: float) -> bool:
    return claim_amount <= self.JURISDICTION_LIMIT  # 2000000.0
```

**Test Cases:**
- ₹10 lakh → Within jurisdiction ✓
- ₹20 lakh (exactly) → Within jurisdiction ✓
- ₹25 lakh → Exceeds jurisdiction ✗

### 2. Deadline Calculation (Requirement 7.3)

Complaints must be filed within 1 year (365 days) from the date of claim rejection.

**Implementation:**
```python
def _calculate_deadline(self, rejection_date: Optional[str]) -> dict:
    rejection_dt = datetime.fromisoformat(rejection_date)
    deadline_dt = rejection_dt + timedelta(days=365)
    days_remaining = (deadline_dt - datetime.now()).days
    within_deadline = days_remaining >= 0
    return {
        'filing_deadline': deadline_dt.date().isoformat(),
        'days_remaining': days_remaining,
        'within_deadline': within_deadline
    }
```

**Test Cases:**
- Rejection 30 days ago → ~335 days remaining ✓
- Rejection 330 days ago → ~35 days remaining ✓
- Rejection 400 days ago → Deadline passed ✗
- No rejection date → Treated as within deadline ✓

### 3. Regional Office Routing (Requirement 7.4)

Identifies the appropriate regional Ombudsman office based on user location.

**Implementation:**
```python
def _get_regional_office(self, user_location: str) -> Optional[OmbudsmanOffice]:
    return self.ombudsman_db.get_office_by_location(user_location)
```

The system supports:
- **17 regional offices** covering all states and union territories
- **City-based lookup**: "Mumbai" → Mumbai office
- **State-based lookup**: "Maharashtra" → Mumbai office
- **Case-insensitive matching**
- **Common city aliases**: "Bangalore" → Bengaluru office

**Test Cases:**
- "Mumbai" → Mumbai office ✓
- "Bangalore" → Bengaluru office ✓
- "Tamil Nadu" → Chennai office ✓
- "Unknown City" → No office found ✗

## Data Models

### EligibilityResult

Location: `healthcare_insurance_platform/models/results.py`

**Key Fields:**
- `is_eligible`: Overall eligibility determination
- `claim_amount`: Claim amount in rupees
- `jurisdiction_limit`: ₹20 lakh limit
- `within_jurisdiction`: Jurisdiction check result
- `rejection_date`: Date of claim rejection
- `filing_deadline`: Last date to file complaint
- `days_remaining`: Days remaining to file
- `within_deadline`: Deadline check result
- `user_location`: User's location
- `regional_office`: Regional office details (dict)
- `eligibility_reasons`: List of reasons
- `explanation`: Detailed explanation
- `next_steps`: Recommended actions
- `citations`: Source citations
- `language`: Output language

**Helper Methods:**
- `is_urgent(threshold_days=30)`: Check if deadline is approaching
- `get_office_name()`: Get regional office name
- `get_office_contact()`: Get office contact information

### ComplaintGuide

Location: `healthcare_insurance_platform/models/results.py`

**Key Fields:**
- `filing_process`: Step-by-step instructions
- `required_documents`: List of required documents
- `argument_points`: Key argument points
- `expected_timeline`: Resolution timeline
- `important_deadlines`: Critical deadlines
- `tips_and_warnings`: Tips and common pitfalls
- `explanation`: Overall explanation
- `citations`: Source citations
- `language`: Output language

## Regional Offices

The system includes all 17 regional Insurance Ombudsman offices:

| Office ID | Region | Jurisdiction |
|-----------|--------|--------------|
| AHMEDABAD | Ahmedabad | Gujarat, Dadra and Nagar Haveli, Daman and Diu |
| BENGALURU | Bengaluru | Karnataka |
| BHOPAL | Bhopal | Madhya Pradesh, Chhattisgarh |
| BHUBANESWAR | Bhubaneswar | Odisha |
| CHANDIGARH | Chandigarh | Punjab, Haryana, Himachal Pradesh, J&K, Ladakh, Chandigarh |
| CHENNAI | Chennai | Tamil Nadu, Puducherry, Andaman & Nicobar |
| DELHI | Delhi | Delhi |
| GUWAHATI | Guwahati | Assam, Meghalaya, Manipur, Mizoram, Arunachal Pradesh, Nagaland, Tripura |
| HYDERABAD | Hyderabad | Telangana, Andhra Pradesh |
| JAIPUR | Jaipur | Rajasthan |
| ERNAKULAM | Ernakulam | Kerala, Lakshadweep |
| KOLKATA | Kolkata | West Bengal, Sikkim, Andaman & Nicobar |
| LUCKNOW | Lucknow | Uttar Pradesh, Uttarakhand |
| MUMBAI | Mumbai | Maharashtra, Goa |
| NOIDA | Noida | UP (Noida, Greater Noida, Ghaziabad, Gautam Budh Nagar) |
| PATNA | Patna | Bihar, Jharkhand |
| PUNE | Pune | Maharashtra (excluding Mumbai Metro), Goa |

## Usage Examples

### Example 1: Check Eligibility for Recent Rejection

```python
from datetime import datetime, timedelta
from healthcare_insurance_platform.services.ombudsman_advisor import OmbudsmanAdvisor

advisor = OmbudsmanAdvisor()

# Claim rejected 2 months ago
rejection_date = (datetime.now() - timedelta(days=60)).date().isoformat()

result = advisor.check_eligibility(
    claim_amount=1500000.0,  # ₹15 lakh
    rejection_date=rejection_date,
    user_location="Mumbai"
)

print(f"Eligible: {result.is_eligible}")
print(f"Days remaining: {result.days_remaining}")
print(f"Office: {result.get_office_name()}")
```

### Example 2: Handle Ineligible Cases

```python
# Claim amount exceeds limit
result = advisor.check_eligibility(
    claim_amount=2500000.0,  # ₹25 lakh
    rejection_date="2024-10-15",
    user_location="Bangalore"
)

if not result.is_eligible:
    print(f"Reason: {result.explanation}")
    print("Next steps:")
    for step in result.next_steps:
        print(f"  - {step}")
```

### Example 3: Urgent Deadline Warning

```python
# Claim rejected 11 months ago
rejection_date = (datetime.now() - timedelta(days=340)).date().isoformat()

result = advisor.check_eligibility(
    claim_amount=1000000.0,
    rejection_date=rejection_date,
    user_location="Chennai"
)

if result.is_urgent():
    print(f"⚠️ URGENT: Only {result.days_remaining} days remaining!")
```

### Example 4: Generate Complaint Guidance

```python
guide = advisor.generate_complaint_guidance(
    claim_id="CLM-2024-001",
    claim_details={
        "claim_type": "hospitalization",
        "treatment": "Cardiac surgery",
        "hospital": "Apollo Hospital",
        "amount": 1500000.0
    },
    rejection_reason="Pre-existing disease exclusion",
    policy_id="POL-2024-001"
)

print("Filing Process:")
for i, step in enumerate(guide.filing_process, 1):
    print(f"{i}. {step}")

print("\nRequired Documents:")
for doc in guide.required_documents:
    print(f"  - {doc}")
```

## Testing

### Unit Tests

Location: `test_ombudsman_simple.py`

Tests cover:
- Jurisdiction validation (₹20 lakh limit)
- Deadline calculation (1 year from rejection)
- Regional office routing
- Overall eligibility determination
- Edge cases (exactly at limit, deadline boundary)

Run tests:
```bash
python test_ombudsman_simple.py
```

### Service Tests

Location: `test_ombudsman_service.py`

Tests the full service functionality including:
- Eligible claims
- Ineligible claims (amount, deadline, location)
- Complaint guidance generation
- Result model helper methods

Run tests:
```bash
python test_ombudsman_service.py
```

## Requirements Validation

This implementation validates the following requirements:

- **Requirement 7.2**: ✓ Validates claim amount against ₹20 lakh jurisdiction limit
- **Requirement 7.3**: ✓ Calculates filing deadline (1 year from rejection date)
- **Requirement 7.4**: ✓ Identifies appropriate regional Ombudsman office based on location
- **Requirement 7.5**: ✓ Provides complaint filing guidance with process and documentation

## Future Enhancements

Potential improvements for future iterations:

1. **Multilingual Support**: Translate eligibility results and guidance to regional languages
2. **Document Upload**: Allow users to upload rejection letters for automatic date extraction
3. **Email Notifications**: Send reminders as deadline approaches
4. **Online Filing Integration**: Direct integration with Ombudsman portal for filing
5. **Case Tracking**: Track complaint status after filing
6. **Success Rate Analytics**: Show success rates for different rejection reasons
7. **Legal Precedents**: Include relevant Ombudsman decisions for similar cases

## References

- Insurance Ombudsman Rules, 2017
- IRDAI (Insurance Ombudsman) Regulations
- Official Ombudsman website: https://www.cioins.co.in
