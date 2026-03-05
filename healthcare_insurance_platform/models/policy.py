"""Policy document data models."""

from datetime import date, datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class WaitingPeriod(BaseModel):
    """Waiting period configuration for a policy."""
    
    general: int = Field(..., ge=0, description="General waiting period in days")
    pre_existing: int = Field(..., ge=0, description="Pre-existing disease waiting period in days")
    specific_conditions: List[dict] = Field(
        default_factory=list,
        description="Specific conditions with custom waiting periods"
    )
    
    @field_validator('specific_conditions')
    @classmethod
    def validate_specific_conditions(cls, v):
        """Validate specific conditions structure."""
        for condition in v:
            if 'condition' not in condition or 'days' not in condition:
                raise ValueError("Each specific condition must have 'condition' and 'days' fields")
            if not isinstance(condition['days'], int) or condition['days'] < 0:
                raise ValueError("Days must be a non-negative integer")
        return v


class DocumentRequirement(BaseModel):
    """Document requirements for specific claim types."""
    
    claim_type: str = Field(..., min_length=1, description="Type of claim")
    documents: List[str] = Field(..., min_length=1, description="Required documents")
    
    @field_validator('documents')
    @classmethod
    def validate_documents(cls, v):
        """Ensure documents list is not empty and contains valid strings."""
        if not v:
            raise ValueError("Documents list cannot be empty")
        for doc in v:
            if not doc or not doc.strip():
                raise ValueError("Document names cannot be empty")
        return v


class ParsedClause(BaseModel):
    """Parsed policy clause with metadata."""
    
    clause_type: str = Field(..., min_length=1, description="Type of clause")
    text: str = Field(..., min_length=1, description="Clause text content")
    importance: str = Field(..., description="Importance level: critical, high, medium, low")
    
    @field_validator('importance')
    @classmethod
    def validate_importance(cls, v):
        """Validate importance level."""
        valid_levels = {'critical', 'high', 'medium', 'low'}
        if v.lower() not in valid_levels:
            raise ValueError(f"Importance must be one of: {', '.join(valid_levels)}")
        return v.lower()


class PolicyDocument(BaseModel):
    """
    Complete policy document data model with validation.
    
    This model represents an insurance policy document with all relevant
    information including coverage, exclusions, waiting periods, and terms.
    Validates: Requirements 12.2
    """
    
    policy_id: str = Field(..., min_length=1, description="Unique policy identifier")
    provider_id: str = Field(..., min_length=1, description="Insurance company identifier")
    policy_name: str = Field(..., min_length=1, description="Policy name")
    policy_type: str = Field(..., description="Policy type: individual, family, senior_citizen")
    version: str = Field(..., min_length=1, description="Policy version")
    effective_date: date = Field(..., description="Policy effective date")
    coverage_amount: float = Field(..., gt=0, description="Coverage amount in currency")
    premium: float = Field(..., gt=0, description="Premium amount in currency")
    waiting_periods: WaitingPeriod = Field(..., description="Waiting period configuration")
    inclusions: List[str] = Field(..., min_length=1, description="Covered treatments/conditions")
    exclusions: List[str] = Field(..., min_length=1, description="Not covered treatments/conditions")
    ped_policy: str = Field(..., min_length=1, description="Pre-existing disease policy")
    claim_process: str = Field(..., min_length=1, description="Claim filing requirements")
    document_requirements: List[DocumentRequirement] = Field(
        ...,
        min_length=1,
        description="Document requirements by claim type"
    )
    full_text: str = Field(..., min_length=1, description="Complete policy document text")
    parsed_clauses: List[ParsedClause] = Field(
        ...,
        min_length=1,
        description="Parsed policy clauses with metadata"
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp"
    )
    
    @field_validator('policy_type')
    @classmethod
    def validate_policy_type(cls, v):
        """Validate policy type."""
        valid_types = {'individual', 'family', 'senior_citizen'}
        if v.lower() not in valid_types:
            raise ValueError(f"Policy type must be one of: {', '.join(valid_types)}")
        return v.lower()
    
    @field_validator('inclusions', 'exclusions')
    @classmethod
    def validate_coverage_lists(cls, v):
        """Ensure coverage lists contain valid non-empty strings."""
        if not v:
            raise ValueError("Coverage list cannot be empty")
        for item in v:
            if not item or not item.strip():
                raise ValueError("Coverage items cannot be empty")
        return v
    
    @model_validator(mode='after')
    def validate_dates_and_amounts(self):
        """Validate logical consistency of dates and amounts."""
        # Ensure effective date is not in the far future
        if self.effective_date > date.today().replace(year=date.today().year + 10):
            raise ValueError("Effective date cannot be more than 10 years in the future")
        
        # Ensure coverage amount is reasonable
        if self.coverage_amount > 1_000_000_000:  # 100 crore
            raise ValueError("Coverage amount seems unreasonably high")
        
        # Ensure premium is less than coverage
        if self.premium >= self.coverage_amount:
            raise ValueError("Premium cannot be greater than or equal to coverage amount")
        
        return self
    
    def to_dict(self) -> dict:
        """
        Serialize the policy document to a dictionary.
        
        Returns:
            dict: Dictionary representation of the policy document
        """
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PolicyDocument':
        """
        Deserialize a policy document from a dictionary.
        
        Args:
            data: Dictionary containing policy document data
            
        Returns:
            PolicyDocument: Validated policy document instance
        """
        return cls.model_validate(data)
    
    def get_clause_by_type(self, clause_type: str) -> List[ParsedClause]:
        """
        Retrieve all clauses of a specific type.
        
        Args:
            clause_type: Type of clause to retrieve
            
        Returns:
            List of parsed clauses matching the type
        """
        return [clause for clause in self.parsed_clauses if clause.clause_type == clause_type]
    
    def get_document_requirements_for_claim(self, claim_type: str) -> Optional[DocumentRequirement]:
        """
        Get document requirements for a specific claim type.
        
        Args:
            claim_type: Type of claim
            
        Returns:
            DocumentRequirement if found, None otherwise
        """
        for req in self.document_requirements:
            if req.claim_type.lower() == claim_type.lower():
                return req
        return None
    
    def has_exclusion(self, condition: str) -> bool:
        """
        Check if a condition is explicitly excluded.
        
        Args:
            condition: Medical condition to check
            
        Returns:
            True if condition is in exclusions list
        """
        condition_lower = condition.lower()
        return any(condition_lower in exclusion.lower() for exclusion in self.exclusions)
    
    def has_inclusion(self, condition: str) -> bool:
        """
        Check if a condition is explicitly included.
        
        Args:
            condition: Medical condition to check
            
        Returns:
            True if condition is in inclusions list
        """
        condition_lower = condition.lower()
        return any(condition_lower in inclusion.lower() for inclusion in self.inclusions)
