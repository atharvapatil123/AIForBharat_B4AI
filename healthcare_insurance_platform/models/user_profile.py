"""User profile data models with medical history."""

from datetime import date, datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class Demographics(BaseModel):
    """User demographic information."""
    
    age: int = Field(..., ge=0, le=150, description="User age in years")
    gender: str = Field(..., description="User gender")
    location: str = Field(..., min_length=1, description="User location (city/state)")
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        """Validate gender field."""
        valid_genders = {'male', 'female', 'other', 'prefer_not_to_say'}
        if v.lower() not in valid_genders:
            raise ValueError(f"Gender must be one of: {', '.join(valid_genders)}")
        return v.lower()


class PreExistingDisease(BaseModel):
    """Pre-existing disease information."""
    
    condition: str = Field(..., min_length=1, description="Medical condition name")
    diagnosis_date: date = Field(..., description="Date of diagnosis")
    severity: str = Field(..., description="Severity level: mild, moderate, severe")
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        """Validate severity level."""
        valid_severities = {'mild', 'moderate', 'severe'}
        if v.lower() not in valid_severities:
            raise ValueError(f"Severity must be one of: {', '.join(valid_severities)}")
        return v.lower()
    
    @field_validator('diagnosis_date')
    @classmethod
    def validate_diagnosis_date(cls, v):
        """Ensure diagnosis date is not in the future."""
        if v > date.today():
            raise ValueError("Diagnosis date cannot be in the future")
        return v


class Medication(BaseModel):
    """Current medication information."""
    
    name: str = Field(..., min_length=1, description="Medication name")
    dosage: str = Field(..., min_length=1, description="Dosage information")
    start_date: date = Field(..., description="Date medication started")
    
    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, v):
        """Ensure start date is not in the future."""
        if v > date.today():
            raise ValueError("Medication start date cannot be in the future")
        return v


class Surgery(BaseModel):
    """Past surgery information."""
    
    procedure: str = Field(..., min_length=1, description="Surgical procedure name")
    surgery_date: date = Field(..., description="Date of surgery")
    
    @field_validator('surgery_date')
    @classmethod
    def validate_surgery_date(cls, v):
        """Ensure surgery date is not in the future."""
        if v > date.today():
            raise ValueError("Surgery date cannot be in the future")
        return v


class MedicalHistory(BaseModel):
    """Complete medical history information."""
    
    pre_existing_diseases: List[PreExistingDisease] = Field(
        default_factory=list,
        description="List of pre-existing diseases"
    )
    current_medications: List[Medication] = Field(
        default_factory=list,
        description="List of current medications"
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="List of known allergies"
    )
    past_surgeries: List[Surgery] = Field(
        default_factory=list,
        description="List of past surgeries"
    )
    
    @field_validator('allergies')
    @classmethod
    def validate_allergies(cls, v):
        """Ensure allergy list contains valid non-empty strings."""
        for allergy in v:
            if not allergy or not allergy.strip():
                raise ValueError("Allergy entries cannot be empty")
        return v


class InsuranceHistoryEntry(BaseModel):
    """Single insurance history entry."""
    
    policy_id: str = Field(..., min_length=1, description="Policy identifier")
    start_date: date = Field(..., description="Policy start date")
    end_date: Optional[date] = Field(None, description="Policy end date (None if active)")
    claims_made: int = Field(..., ge=0, description="Number of claims made")
    
    @model_validator(mode='after')
    def validate_dates(self):
        """Validate date consistency."""
        if self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date")
        if self.start_date > date.today():
            raise ValueError("Start date cannot be in the future")
        if self.end_date and self.end_date > date.today():
            raise ValueError("End date cannot be in the future")
        return self


class UserProfile(BaseModel):
    """
    Complete user profile with demographics and medical history.
    
    This model represents a user's profile including personal information,
    medical history, insurance history, and privacy preferences.
    Implements privacy-aware serialization to protect sensitive data.
    Validates: Requirements 2.1, 15.1
    """
    
    user_id: str = Field(..., min_length=1, description="Unique user identifier")
    demographics: Demographics = Field(..., description="User demographic information")
    medical_history: MedicalHistory = Field(..., description="User medical history")
    insurance_history: List[InsuranceHistoryEntry] = Field(
        default_factory=list,
        description="User insurance history"
    )
    language_preference: str = Field(
        default="en",
        description="ISO language code for user preference"
    )
    consent_given: bool = Field(
        default=False,
        description="Whether user has given consent for data processing"
    )
    data_retention_preference: str = Field(
        default="standard",
        description="Data retention preference: minimal, standard, extended"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Profile creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Profile last update timestamp"
    )
    
    @field_validator('language_preference')
    @classmethod
    def validate_language(cls, v):
        """Validate language preference."""
        valid_languages = {'en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu'}
        if v.lower() not in valid_languages:
            raise ValueError(
                f"Language must be one of: {', '.join(valid_languages)} "
                "(en=English, hi=Hindi, ta=Tamil, te=Telugu, bn=Bengali, mr=Marathi, gu=Gujarati)"
            )
        return v.lower()
    
    @field_validator('data_retention_preference')
    @classmethod
    def validate_retention(cls, v):
        """Validate data retention preference."""
        valid_preferences = {'minimal', 'standard', 'extended'}
        if v.lower() not in valid_preferences:
            raise ValueError(f"Data retention preference must be one of: {', '.join(valid_preferences)}")
        return v.lower()
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Serialize the user profile to a dictionary with privacy controls.
        
        Args:
            include_sensitive: If False, excludes sensitive medical information
            
        Returns:
            dict: Dictionary representation of the user profile
        """
        data = self.model_dump(mode='json')
        
        if not include_sensitive:
            # Remove sensitive fields for privacy-aware serialization
            if 'medical_history' in data:
                # Keep only counts, not actual data
                medical = data['medical_history']
                data['medical_history'] = {
                    'pre_existing_diseases_count': len(medical.get('pre_existing_diseases', [])),
                    'current_medications_count': len(medical.get('current_medications', [])),
                    'allergies_count': len(medical.get('allergies', [])),
                    'past_surgeries_count': len(medical.get('past_surgeries', []))
                }
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserProfile':
        """
        Deserialize a user profile from a dictionary.
        
        Args:
            data: Dictionary containing user profile data
            
        Returns:
            UserProfile: Validated user profile instance
        """
        return cls.model_validate(data)
    
    def get_ped_list(self) -> List[str]:
        """
        Get list of pre-existing disease names.
        
        Returns:
            List of condition names
        """
        return [ped.condition for ped in self.medical_history.pre_existing_diseases]
    
    def get_medication_list(self) -> List[str]:
        """
        Get list of current medication names.
        
        Returns:
            List of medication names
        """
        return [med.name for med in self.medical_history.current_medications]
    
    def get_allergy_list(self) -> List[str]:
        """
        Get list of known allergies.
        
        Returns:
            List of allergies
        """
        return self.medical_history.allergies
    
    def has_ped(self, condition: str) -> bool:
        """
        Check if user has a specific pre-existing disease.
        
        Args:
            condition: Medical condition to check
            
        Returns:
            True if condition is in PED list
        """
        condition_lower = condition.lower()
        return any(
            condition_lower in ped.condition.lower()
            for ped in self.medical_history.pre_existing_diseases
        )
    
    def has_allergy(self, allergen: str) -> bool:
        """
        Check if user has a specific allergy.
        
        Args:
            allergen: Allergen to check
            
        Returns:
            True if allergen is in allergy list
        """
        allergen_lower = allergen.lower()
        return any(
            allergen_lower in allergy.lower()
            for allergy in self.medical_history.allergies
        )
    
    def get_active_policies(self) -> List[InsuranceHistoryEntry]:
        """
        Get list of currently active insurance policies.
        
        Returns:
            List of active insurance history entries (end_date is None)
        """
        return [entry for entry in self.insurance_history if entry.end_date is None]
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now(timezone.utc)
