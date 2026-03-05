"""Claim details data models."""

from datetime import date, datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class TreatmentDetails(BaseModel):
    """Treatment information for a claim."""
    
    condition: str = Field(..., min_length=1, description="Medical condition being treated")
    hospital: str = Field(..., min_length=1, description="Hospital or healthcare facility name")
    admission_date: date = Field(..., description="Date of admission")
    discharge_date: Optional[date] = Field(None, description="Date of discharge (None if ongoing)")
    procedures: List[str] = Field(default_factory=list, description="Medical procedures performed")
    diagnosis: str = Field(..., min_length=1, description="Medical diagnosis")
    
    @field_validator('admission_date')
    @classmethod
    def validate_admission_date(cls, v):
        """Ensure admission date is not in the future."""
        if v > date.today():
            raise ValueError("Admission date cannot be in the future")
        return v
    
    @field_validator('discharge_date')
    @classmethod
    def validate_discharge_date(cls, v):
        """Ensure discharge date is not in the future."""
        if v and v > date.today():
            raise ValueError("Discharge date cannot be in the future")
        return v
    
    @field_validator('procedures')
    @classmethod
    def validate_procedures(cls, v):
        """Ensure procedures list contains valid non-empty strings."""
        for procedure in v:
            if not procedure or not procedure.strip():
                raise ValueError("Procedure names cannot be empty")
        return v
    
    @model_validator(mode='after')
    def validate_dates(self):
        """Validate date consistency."""
        if self.discharge_date and self.admission_date > self.discharge_date:
            raise ValueError("Admission date cannot be after discharge date")
        return self


class DocumentProvided(BaseModel):
    """Document provided for a claim."""
    
    document_type: str = Field(..., min_length=1, description="Type of document")
    file_name: str = Field(..., min_length=1, description="File name of the document")
    upload_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Document upload timestamp"
    )
    
    @field_validator('upload_date')
    @classmethod
    def validate_upload_date(cls, v):
        """Ensure upload date is not in the future."""
        if v > datetime.now(timezone.utc):
            raise ValueError("Upload date cannot be in the future")
        return v


class ClaimDetails(BaseModel):
    """
    Complete claim details data model with validation.
    
    This model represents an insurance claim with treatment information,
    document tracking, and claim status. Includes validation for claim
    amounts and dates to ensure data integrity.
    Validates: Requirements 5.1, 6.1
    """
    
    claim_id: str = Field(..., min_length=1, description="Unique claim identifier")
    user_id: str = Field(..., min_length=1, description="User identifier who filed the claim")
    policy_id: str = Field(..., min_length=1, description="Policy identifier for the claim")
    claim_type: str = Field(..., description="Type of claim: hospitalization, surgery, diagnostic, pharmacy")
    claim_amount: float = Field(..., ge=0, description="Claim amount in currency")
    treatment_details: TreatmentDetails = Field(..., description="Treatment information")
    documents_provided: List[DocumentProvided] = Field(
        default_factory=list,
        description="Documents provided with the claim"
    )
    claim_date: date = Field(
        default_factory=date.today,
        description="Date the claim was filed"
    )
    status: str = Field(
        default="pending",
        description="Claim status: pending, approved, rejected"
    )
    rejection_reason: Optional[str] = Field(
        None,
        description="Reason for rejection if status is rejected"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Claim creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Claim last update timestamp"
    )
    
    @field_validator('claim_type')
    @classmethod
    def validate_claim_type(cls, v):
        """Validate claim type."""
        valid_types = {'hospitalization', 'surgery', 'diagnostic', 'pharmacy'}
        if v.lower() not in valid_types:
            raise ValueError(f"Claim type must be one of: {', '.join(valid_types)}")
        return v.lower()
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate claim status."""
        valid_statuses = {'pending', 'approved', 'rejected'}
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.lower()
    
    @field_validator('claim_amount')
    @classmethod
    def validate_claim_amount(cls, v):
        """Validate claim amount is reasonable."""
        if v > 100_000_000:  # 10 crore
            raise ValueError("Claim amount seems unreasonably high")
        return v
    
    @field_validator('claim_date')
    @classmethod
    def validate_claim_date(cls, v):
        """Ensure claim date is not in the future."""
        if v > date.today():
            raise ValueError("Claim date cannot be in the future")
        return v
    
    @model_validator(mode='after')
    def validate_rejection_reason(self):
        """Ensure rejection reason is provided when status is rejected."""
        if self.status == 'rejected' and not self.rejection_reason:
            raise ValueError("Rejection reason must be provided when status is rejected")
        if self.status != 'rejected' and self.rejection_reason:
            raise ValueError("Rejection reason should only be provided when status is rejected")
        return self
    
    @model_validator(mode='after')
    def validate_claim_date_consistency(self):
        """Validate claim date is after or equal to admission date."""
        if self.claim_date < self.treatment_details.admission_date:
            raise ValueError("Claim date cannot be before admission date")
        return self
    
    def to_dict(self) -> dict:
        """
        Serialize the claim details to a dictionary.
        
        Returns:
            dict: Dictionary representation of the claim details
        """
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ClaimDetails':
        """
        Deserialize claim details from a dictionary.
        
        Args:
            data: Dictionary containing claim details data
            
        Returns:
            ClaimDetails: Validated claim details instance
        """
        return cls.model_validate(data)
    
    def add_document(self, document_type: str, file_name: str) -> None:
        """
        Add a document to the claim.
        
        Args:
            document_type: Type of document being added
            file_name: Name of the document file
        """
        document = DocumentProvided(
            document_type=document_type,
            file_name=file_name
        )
        self.documents_provided.append(document)
        self.update_timestamp()
    
    def get_document_types(self) -> List[str]:
        """
        Get list of document types provided with the claim.
        
        Returns:
            List of document type names
        """
        return [doc.document_type for doc in self.documents_provided]
    
    def has_document_type(self, document_type: str) -> bool:
        """
        Check if a specific document type has been provided.
        
        Args:
            document_type: Type of document to check
            
        Returns:
            True if document type is in provided documents
        """
        document_type_lower = document_type.lower()
        return any(
            document_type_lower in doc.document_type.lower()
            for doc in self.documents_provided
        )
    
    def update_status(self, new_status: str, rejection_reason: Optional[str] = None) -> None:
        """
        Update the claim status.
        
        Args:
            new_status: New status value (pending, approved, rejected)
            rejection_reason: Reason for rejection (required if status is rejected)
        """
        valid_statuses = {'pending', 'approved', 'rejected'}
        if new_status.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        if new_status.lower() == 'rejected' and not rejection_reason:
            raise ValueError("Rejection reason must be provided when status is rejected")
        
        self.status = new_status.lower()
        self.rejection_reason = rejection_reason
        self.update_timestamp()
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now(timezone.utc)
    
    def get_treatment_duration_days(self) -> Optional[int]:
        """
        Calculate treatment duration in days.
        
        Returns:
            Number of days between admission and discharge, or None if not discharged
        """
        if self.treatment_details.discharge_date:
            delta = self.treatment_details.discharge_date - self.treatment_details.admission_date
            return delta.days
        return None
    
    def is_pending(self) -> bool:
        """Check if claim is pending."""
        return self.status == 'pending'
    
    def is_approved(self) -> bool:
        """Check if claim is approved."""
        return self.status == 'approved'
    
    def is_rejected(self) -> bool:
        """Check if claim is rejected."""
        return self.status == 'rejected'
