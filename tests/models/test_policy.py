"""Unit tests for PolicyDocument data model."""

import pytest
from datetime import date, datetime, timedelta, timezone
from pydantic import ValidationError

from healthcare_insurance_platform.models.policy import (
    PolicyDocument,
    WaitingPeriod,
    DocumentRequirement,
    ParsedClause,
)


@pytest.fixture
def valid_waiting_period():
    """Create a valid waiting period."""
    return WaitingPeriod(
        general=30,
        pre_existing=730,
        specific_conditions=[
            {"condition": "diabetes", "days": 365},
            {"condition": "hypertension", "days": 180}
        ]
    )


@pytest.fixture
def valid_document_requirements():
    """Create valid document requirements."""
    return [
        DocumentRequirement(
            claim_type="hospitalization",
            documents=["discharge_summary", "bills", "prescriptions"]
        ),
        DocumentRequirement(
            claim_type="surgery",
            documents=["surgery_report", "bills", "anesthesia_report"]
        )
    ]


@pytest.fixture
def valid_parsed_clauses():
    """Create valid parsed clauses."""
    return [
        ParsedClause(
            clause_type="coverage",
            text="Covers all hospitalization expenses",
            importance="critical"
        ),
        ParsedClause(
            clause_type="exclusion",
            text="Does not cover cosmetic procedures",
            importance="high"
        )
    ]


@pytest.fixture
def valid_policy_data(valid_waiting_period, valid_document_requirements, valid_parsed_clauses):
    """Create valid policy document data."""
    return {
        "policy_id": "POL-2024-001",
        "provider_id": "PROV-001",
        "policy_name": "Comprehensive Health Insurance",
        "policy_type": "family",
        "version": "1.0",
        "effective_date": date.today(),
        "coverage_amount": 500000.0,
        "premium": 15000.0,
        "waiting_periods": valid_waiting_period,
        "inclusions": ["hospitalization", "surgery", "diagnostic_tests"],
        "exclusions": ["cosmetic_surgery", "dental"],
        "ped_policy": "Covered after 2 years waiting period",
        "claim_process": "Submit claim within 30 days of discharge",
        "document_requirements": valid_document_requirements,
        "full_text": "This is the complete policy document text...",
        "parsed_clauses": valid_parsed_clauses,
    }


class TestWaitingPeriod:
    """Tests for WaitingPeriod model."""
    
    def test_valid_waiting_period(self, valid_waiting_period):
        """Test creating a valid waiting period."""
        assert valid_waiting_period.general == 30
        assert valid_waiting_period.pre_existing == 730
        assert len(valid_waiting_period.specific_conditions) == 2
    
    def test_negative_general_waiting_period(self):
        """Test that negative general waiting period is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WaitingPeriod(general=-1, pre_existing=730, specific_conditions=[])
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_negative_pre_existing_waiting_period(self):
        """Test that negative pre-existing waiting period is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WaitingPeriod(general=30, pre_existing=-100, specific_conditions=[])
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_invalid_specific_condition_structure(self):
        """Test that invalid specific condition structure is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WaitingPeriod(
                general=30,
                pre_existing=730,
                specific_conditions=[{"condition": "diabetes"}]  # Missing 'days'
            )
        assert "must have 'condition' and 'days' fields" in str(exc_info.value)
    
    def test_negative_days_in_specific_condition(self):
        """Test that negative days in specific condition is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WaitingPeriod(
                general=30,
                pre_existing=730,
                specific_conditions=[{"condition": "diabetes", "days": -10}]
            )
        assert "non-negative integer" in str(exc_info.value)


class TestDocumentRequirement:
    """Tests for DocumentRequirement model."""
    
    def test_valid_document_requirement(self):
        """Test creating a valid document requirement."""
        req = DocumentRequirement(
            claim_type="hospitalization",
            documents=["discharge_summary", "bills"]
        )
        assert req.claim_type == "hospitalization"
        assert len(req.documents) == 2
    
    def test_empty_claim_type(self):
        """Test that empty claim type is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentRequirement(claim_type="", documents=["bill"])
        assert "at least 1 character" in str(exc_info.value)
    
    def test_empty_documents_list(self):
        """Test that empty documents list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentRequirement(claim_type="hospitalization", documents=[])
        assert "at least 1 item" in str(exc_info.value)
    
    def test_empty_document_name(self):
        """Test that empty document names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentRequirement(claim_type="hospitalization", documents=["bill", ""])
        assert "cannot be empty" in str(exc_info.value)


class TestParsedClause:
    """Tests for ParsedClause model."""
    
    def test_valid_parsed_clause(self):
        """Test creating a valid parsed clause."""
        clause = ParsedClause(
            clause_type="coverage",
            text="Covers hospitalization",
            importance="critical"
        )
        assert clause.clause_type == "coverage"
        assert clause.importance == "critical"
    
    def test_invalid_importance_level(self):
        """Test that invalid importance level is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ParsedClause(
                clause_type="coverage",
                text="Some text",
                importance="super_important"
            )
        assert "Importance must be one of" in str(exc_info.value)
    
    def test_importance_case_insensitive(self):
        """Test that importance level is case-insensitive."""
        clause = ParsedClause(
            clause_type="coverage",
            text="Some text",
            importance="CRITICAL"
        )
        assert clause.importance == "critical"


class TestPolicyDocument:
    """Tests for PolicyDocument model."""
    
    def test_valid_policy_document(self, valid_policy_data):
        """Test creating a valid policy document."""
        policy = PolicyDocument(**valid_policy_data)
        assert policy.policy_id == "POL-2024-001"
        assert policy.coverage_amount == 500000.0
        assert policy.premium == 15000.0
        assert policy.policy_type == "family"
    
    def test_empty_policy_id(self, valid_policy_data):
        """Test that empty policy ID is rejected."""
        valid_policy_data["policy_id"] = ""
        with pytest.raises(ValidationError) as exc_info:
            PolicyDocument(**valid_policy_data)
        assert "at least 1 character" in str(exc_info.value)
    
    def test_invalid_policy_type(self, valid_policy_data):
        """Test that invalid policy type is rejected."""
        valid_policy_data["policy_type"] = "corporate"
        with pytest.raises(ValidationError) as exc_info:
            PolicyDocument(**valid_policy_data)
        assert "Policy type must be one of" in str(exc_info.value)
    
    def test_policy_type_case_insensitive(self, valid_policy_data):
        """Test that policy type is case-insensitive."""
        valid_policy_data["policy_type"] = "FAMILY"
        policy = PolicyDocument(**valid_policy_data)
        assert policy.policy_type == "family"
    
    def test_negative_coverage_amount(self, valid_policy_data):
        """Test that negative coverage amount is rejected."""
        valid_policy_data["coverage_amount"] = -1000.0
        with pytest.raises(ValidationError) as exc_info:
            PolicyDocument(**valid_policy_data)
        assert "greater than 0" in str(exc_info.value)
    
    def test_zero_coverage_amount(self, valid_policy_data):
        """Test that zero coverage amount is rejected."""
        valid_policy_data["coverage_amount"] = 0.0
        with pytest.raises(ValidationError) as exc_info:
            PolicyDocument(**valid_policy_data)
        assert "greater than 0" in str(exc_info.value)
    
    def test_negative_premium(self, valid_policy_data):
        """Test that negative premium is rejected."""
        valid_policy_data["premium"] = -500.0
        with pytest.raises(ValidationError) as exc_info:
            PolicyDocument(**valid_policy_data)
        assert "greater than 0" in str(exc_info.value)
    
    def test_premium_greater_than_coverage(self, valid_policy_data):
        """Test that premium greater than coverage is rejected."""
        valid_policy_data["premium"] = 600000.0
        valid_policy_data["coverage_amount"] = 500000.0
        with pytest.raises(ValidationError) as exc_info:
            PolicyDocument(**valid_policy_data)
        assert "Premium cannot be greater than or equal to coverage amount" in str(exc_info.value)
    
    def test_premium_equal_to_coverage(self, valid_policy_data):
        """Test that premium equal to coverage is rejected."""
        valid_policy_data["premium"] = 500000.0
        valid_policy_data["coverage_amount"] = 500000.0
        with pytest.raises(ValidationError) as exc_info:
            PolicyDocument(**valid_policy_data)
        assert "Premium cannot be greater than or equal to coverage amount" in str(exc_info.value)
    
    def test_unreasonably_high_coverage(self, valid_policy_data):
        """Test that unreasonably high coverage is rejected."""
        valid_policy_data["coverage_amount"] = 2_000_000_000.0  # 200 crore
        with pytest.raises(ValidationError) as exc_info:
            PolicyDocument(**valid_policy_data)
        assert "unreasonably high" in str(exc_info.value)
    
    def test_far_future_effective_date(self, valid_policy_data):
        """Test that far future effective date is rejected."""
        valid_policy_data["effective_date"] = date.today().replace(year=date.today().year + 15)
        with pytest.raises(ValidationError) as exc_info:
            PolicyDocument(**valid_policy_data)
        assert "more than 10 years in the future" in str(exc_info.value)
    
    def test_empty_inclusions(self, valid_policy_data):
        """Test that empty inclusions list is rejected."""
        valid_policy_data["inclusions"] = []
        with pytest.raises(ValidationError) as exc_info:
            PolicyDocument(**valid_policy_data)
        assert "at least 1 item" in str(exc_info.value)
    
    def test_empty_exclusions(self, valid_policy_data):
        """Test that empty exclusions list is rejected."""
        valid_policy_data["exclusions"] = []
        with pytest.raises(ValidationError) as exc_info:
            PolicyDocument(**valid_policy_data)
        assert "at least 1 item" in str(exc_info.value)
    
    def test_empty_inclusion_item(self, valid_policy_data):
        """Test that empty inclusion items are rejected."""
        valid_policy_data["inclusions"] = ["hospitalization", ""]
        with pytest.raises(ValidationError) as exc_info:
            PolicyDocument(**valid_policy_data)
        assert "cannot be empty" in str(exc_info.value)
    
    def test_to_dict_serialization(self, valid_policy_data):
        """Test serialization to dictionary."""
        policy = PolicyDocument(**valid_policy_data)
        policy_dict = policy.to_dict()
        
        assert isinstance(policy_dict, dict)
        assert policy_dict["policy_id"] == "POL-2024-001"
        assert policy_dict["coverage_amount"] == 500000.0
        assert "last_updated" in policy_dict
    
    def test_from_dict_deserialization(self, valid_policy_data):
        """Test deserialization from dictionary."""
        policy = PolicyDocument(**valid_policy_data)
        policy_dict = policy.to_dict()
        
        # Deserialize back
        restored_policy = PolicyDocument.from_dict(policy_dict)
        
        assert restored_policy.policy_id == policy.policy_id
        assert restored_policy.coverage_amount == policy.coverage_amount
        assert restored_policy.premium == policy.premium
    
    def test_get_clause_by_type(self, valid_policy_data):
        """Test retrieving clauses by type."""
        policy = PolicyDocument(**valid_policy_data)
        
        coverage_clauses = policy.get_clause_by_type("coverage")
        assert len(coverage_clauses) == 1
        assert coverage_clauses[0].text == "Covers all hospitalization expenses"
        
        exclusion_clauses = policy.get_clause_by_type("exclusion")
        assert len(exclusion_clauses) == 1
        
        nonexistent_clauses = policy.get_clause_by_type("nonexistent")
        assert len(nonexistent_clauses) == 0
    
    def test_get_document_requirements_for_claim(self, valid_policy_data):
        """Test retrieving document requirements for specific claim type."""
        policy = PolicyDocument(**valid_policy_data)
        
        hosp_req = policy.get_document_requirements_for_claim("hospitalization")
        assert hosp_req is not None
        assert hosp_req.claim_type == "hospitalization"
        assert "discharge_summary" in hosp_req.documents
        
        surgery_req = policy.get_document_requirements_for_claim("surgery")
        assert surgery_req is not None
        assert "surgery_report" in surgery_req.documents
        
        nonexistent_req = policy.get_document_requirements_for_claim("dental")
        assert nonexistent_req is None
    
    def test_get_document_requirements_case_insensitive(self, valid_policy_data):
        """Test that document requirement lookup is case-insensitive."""
        policy = PolicyDocument(**valid_policy_data)
        
        req = policy.get_document_requirements_for_claim("HOSPITALIZATION")
        assert req is not None
        assert req.claim_type == "hospitalization"
    
    def test_has_exclusion(self, valid_policy_data):
        """Test checking if a condition is excluded."""
        policy = PolicyDocument(**valid_policy_data)
        
        assert policy.has_exclusion("cosmetic_surgery") is True
        assert policy.has_exclusion("dental") is True
        assert policy.has_exclusion("hospitalization") is False
    
    def test_has_exclusion_partial_match(self, valid_policy_data):
        """Test that exclusion check works with partial matches."""
        policy = PolicyDocument(**valid_policy_data)
        
        assert policy.has_exclusion("cosmetic") is True
        assert policy.has_exclusion("surgery") is True  # Matches cosmetic_surgery
    
    def test_has_exclusion_case_insensitive(self, valid_policy_data):
        """Test that exclusion check is case-insensitive."""
        policy = PolicyDocument(**valid_policy_data)
        
        assert policy.has_exclusion("COSMETIC_SURGERY") is True
        assert policy.has_exclusion("Dental") is True
    
    def test_has_inclusion(self, valid_policy_data):
        """Test checking if a condition is included."""
        policy = PolicyDocument(**valid_policy_data)
        
        assert policy.has_inclusion("hospitalization") is True
        assert policy.has_inclusion("surgery") is True
        assert policy.has_inclusion("dental") is False
    
    def test_has_inclusion_case_insensitive(self, valid_policy_data):
        """Test that inclusion check is case-insensitive."""
        policy = PolicyDocument(**valid_policy_data)
        
        assert policy.has_inclusion("HOSPITALIZATION") is True
        assert policy.has_inclusion("Surgery") is True
    
    def test_last_updated_auto_generated(self, valid_policy_data):
        """Test that last_updated is automatically generated."""
        policy = PolicyDocument(**valid_policy_data)
        
        assert policy.last_updated is not None
        assert isinstance(policy.last_updated, datetime)
        # Should be very recent (within last minute)
        assert datetime.now(timezone.utc) - policy.last_updated < timedelta(minutes=1)
    
    def test_last_updated_can_be_set(self, valid_policy_data):
        """Test that last_updated can be explicitly set."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        valid_policy_data["last_updated"] = custom_time
        
        policy = PolicyDocument(**valid_policy_data)
        assert policy.last_updated == custom_time


class TestPolicyDocumentEdgeCases:
    """Edge case tests for PolicyDocument."""
    
    def test_minimum_valid_policy(self, valid_waiting_period):
        """Test creating a policy with minimum required fields."""
        policy = PolicyDocument(
            policy_id="MIN-001",
            provider_id="PROV-001",
            policy_name="Minimal Policy",
            policy_type="individual",
            version="1.0",
            effective_date=date.today(),
            coverage_amount=100000.0,
            premium=1000.0,
            waiting_periods=valid_waiting_period,
            inclusions=["basic_coverage"],
            exclusions=["cosmetic"],
            ped_policy="Standard",
            claim_process="Standard process",
            document_requirements=[
                DocumentRequirement(claim_type="basic", documents=["id"])
            ],
            full_text="Minimal text",
            parsed_clauses=[
                ParsedClause(clause_type="basic", text="Basic clause", importance="low")
            ]
        )
        
        assert policy.policy_id == "MIN-001"
        assert len(policy.inclusions) == 1
        assert len(policy.exclusions) == 1
    
    def test_policy_with_many_inclusions_and_exclusions(self, valid_policy_data):
        """Test policy with large lists of inclusions and exclusions."""
        valid_policy_data["inclusions"] = [f"inclusion_{i}" for i in range(100)]
        valid_policy_data["exclusions"] = [f"exclusion_{i}" for i in range(100)]
        
        policy = PolicyDocument(**valid_policy_data)
        assert len(policy.inclusions) == 100
        assert len(policy.exclusions) == 100
    
    def test_policy_with_very_long_text(self, valid_policy_data):
        """Test policy with very long full text."""
        valid_policy_data["full_text"] = "A" * 100000  # 100k characters
        
        policy = PolicyDocument(**valid_policy_data)
        assert len(policy.full_text) == 100000
    
    def test_boundary_coverage_amount(self, valid_policy_data):
        """Test boundary values for coverage amount."""
        # Just under the limit
        valid_policy_data["coverage_amount"] = 999_999_999.0
        valid_policy_data["premium"] = 50000.0
        
        policy = PolicyDocument(**valid_policy_data)
        assert policy.coverage_amount == 999_999_999.0
    
    def test_effective_date_today(self, valid_policy_data):
        """Test policy effective today."""
        valid_policy_data["effective_date"] = date.today()
        
        policy = PolicyDocument(**valid_policy_data)
        assert policy.effective_date == date.today()
    
    def test_effective_date_past(self, valid_policy_data):
        """Test policy effective in the past."""
        valid_policy_data["effective_date"] = date.today() - timedelta(days=365)
        
        policy = PolicyDocument(**valid_policy_data)
        assert policy.effective_date < date.today()
    
    def test_effective_date_near_future_limit(self, valid_policy_data):
        """Test policy effective near the 10-year future limit."""
        future_date = date.today().replace(year=date.today().year + 9)
        valid_policy_data["effective_date"] = future_date
        
        policy = PolicyDocument(**valid_policy_data)
        assert policy.effective_date == future_date
