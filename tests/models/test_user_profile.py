"""Unit tests for UserProfile data model."""

import pytest
from datetime import date, datetime, timedelta, timezone
from pydantic import ValidationError

from healthcare_insurance_platform.models.user_profile import (
    UserProfile,
    Demographics,
    MedicalHistory,
    PreExistingDisease,
    Medication,
    Surgery,
    InsuranceHistoryEntry,
)


@pytest.fixture
def valid_demographics():
    """Create valid demographics."""
    return Demographics(
        age=35,
        gender="male",
        location="Mumbai, Maharashtra"
    )


@pytest.fixture
def valid_medical_history():
    """Create valid medical history."""
    return MedicalHistory(
        pre_existing_diseases=[
            PreExistingDisease(
                condition="Type 2 Diabetes",
                diagnosis_date=date(2020, 1, 15),
                severity="moderate"
            ),
            PreExistingDisease(
                condition="Hypertension",
                diagnosis_date=date(2019, 6, 10),
                severity="mild"
            )
        ],
        current_medications=[
            Medication(
                name="Metformin",
                dosage="500mg twice daily",
                start_date=date(2020, 1, 20)
            ),
            Medication(
                name="Lisinopril",
                dosage="10mg once daily",
                start_date=date(2019, 6, 15)
            )
        ],
        allergies=["Penicillin", "Sulfa drugs"],
        past_surgeries=[
            Surgery(
                procedure="Appendectomy",
                surgery_date=date(2015, 3, 10)
            )
        ]
    )


@pytest.fixture
def valid_insurance_history():
    """Create valid insurance history."""
    return [
        InsuranceHistoryEntry(
            policy_id="POL-2020-001",
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
            claims_made=2
        ),
        InsuranceHistoryEntry(
            policy_id="POL-2024-001",
            start_date=date(2024, 1, 1),
            end_date=None,  # Active policy
            claims_made=0
        )
    ]


@pytest.fixture
def valid_user_profile_data(valid_demographics, valid_medical_history, valid_insurance_history):
    """Create valid user profile data."""
    return {
        "user_id": "USER-001",
        "demographics": valid_demographics,
        "medical_history": valid_medical_history,
        "insurance_history": valid_insurance_history,
        "language_preference": "en",
        "consent_given": True,
        "data_retention_preference": "standard"
    }


class TestDemographics:
    """Tests for Demographics model."""
    
    def test_valid_demographics(self, valid_demographics):
        """Test creating valid demographics."""
        assert valid_demographics.age == 35
        assert valid_demographics.gender == "male"
        assert valid_demographics.location == "Mumbai, Maharashtra"
    
    def test_negative_age(self):
        """Test that negative age is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Demographics(age=-1, gender="male", location="Mumbai")
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_age_over_150(self):
        """Test that age over 150 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Demographics(age=151, gender="male", location="Mumbai")
        assert "less than or equal to 150" in str(exc_info.value)
    
    def test_invalid_gender(self):
        """Test that invalid gender is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Demographics(age=35, gender="invalid", location="Mumbai")
        assert "Gender must be one of" in str(exc_info.value)
    
    def test_gender_case_insensitive(self):
        """Test that gender is case-insensitive."""
        demo = Demographics(age=35, gender="MALE", location="Mumbai")
        assert demo.gender == "male"
    
    def test_empty_location(self):
        """Test that empty location is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Demographics(age=35, gender="male", location="")
        assert "at least 1 character" in str(exc_info.value)
    
    def test_all_valid_genders(self):
        """Test all valid gender values."""
        valid_genders = ["male", "female", "other", "prefer_not_to_say"]
        for gender in valid_genders:
            demo = Demographics(age=35, gender=gender, location="Mumbai")
            assert demo.gender == gender.lower()


class TestPreExistingDisease:
    """Tests for PreExistingDisease model."""
    
    def test_valid_ped(self):
        """Test creating a valid pre-existing disease."""
        ped = PreExistingDisease(
            condition="Diabetes",
            diagnosis_date=date(2020, 1, 1),
            severity="moderate"
        )
        assert ped.condition == "Diabetes"
        assert ped.severity == "moderate"
    
    def test_empty_condition(self):
        """Test that empty condition is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PreExistingDisease(
                condition="",
                diagnosis_date=date(2020, 1, 1),
                severity="moderate"
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_invalid_severity(self):
        """Test that invalid severity is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PreExistingDisease(
                condition="Diabetes",
                diagnosis_date=date(2020, 1, 1),
                severity="extreme"
            )
        assert "Severity must be one of" in str(exc_info.value)
    
    def test_severity_case_insensitive(self):
        """Test that severity is case-insensitive."""
        ped = PreExistingDisease(
            condition="Diabetes",
            diagnosis_date=date(2020, 1, 1),
            severity="MODERATE"
        )
        assert ped.severity == "moderate"
    
    def test_future_diagnosis_date(self):
        """Test that future diagnosis date is rejected."""
        future_date = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            PreExistingDisease(
                condition="Diabetes",
                diagnosis_date=future_date,
                severity="moderate"
            )
        assert "cannot be in the future" in str(exc_info.value)
    
    def test_diagnosis_date_today(self):
        """Test that diagnosis date today is valid."""
        ped = PreExistingDisease(
            condition="Diabetes",
            diagnosis_date=date.today(),
            severity="moderate"
        )
        assert ped.diagnosis_date == date.today()


class TestMedication:
    """Tests for Medication model."""
    
    def test_valid_medication(self):
        """Test creating a valid medication."""
        med = Medication(
            name="Metformin",
            dosage="500mg twice daily",
            start_date=date(2020, 1, 1)
        )
        assert med.name == "Metformin"
        assert med.dosage == "500mg twice daily"
    
    def test_empty_name(self):
        """Test that empty medication name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Medication(
                name="",
                dosage="500mg",
                start_date=date(2020, 1, 1)
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_empty_dosage(self):
        """Test that empty dosage is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Medication(
                name="Metformin",
                dosage="",
                start_date=date(2020, 1, 1)
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_future_start_date(self):
        """Test that future start date is rejected."""
        future_date = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            Medication(
                name="Metformin",
                dosage="500mg",
                start_date=future_date
            )
        assert "cannot be in the future" in str(exc_info.value)


class TestSurgery:
    """Tests for Surgery model."""
    
    def test_valid_surgery(self):
        """Test creating a valid surgery."""
        surgery = Surgery(
            procedure="Appendectomy",
            surgery_date=date(2015, 1, 1)
        )
        assert surgery.procedure == "Appendectomy"
        assert surgery.surgery_date == date(2015, 1, 1)
    
    def test_empty_procedure(self):
        """Test that empty procedure is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Surgery(procedure="", surgery_date=date(2015, 1, 1))
        assert "at least 1 character" in str(exc_info.value)
    
    def test_future_surgery_date(self):
        """Test that future surgery date is rejected."""
        future_date = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            Surgery(procedure="Appendectomy", surgery_date=future_date)
        assert "cannot be in the future" in str(exc_info.value)


class TestMedicalHistory:
    """Tests for MedicalHistory model."""
    
    def test_valid_medical_history(self, valid_medical_history):
        """Test creating valid medical history."""
        assert len(valid_medical_history.pre_existing_diseases) == 2
        assert len(valid_medical_history.current_medications) == 2
        assert len(valid_medical_history.allergies) == 2
        assert len(valid_medical_history.past_surgeries) == 1
    
    def test_empty_medical_history(self):
        """Test creating empty medical history."""
        history = MedicalHistory()
        assert len(history.pre_existing_diseases) == 0
        assert len(history.current_medications) == 0
        assert len(history.allergies) == 0
        assert len(history.past_surgeries) == 0
    
    def test_empty_allergy_string(self):
        """Test that empty allergy strings are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MedicalHistory(allergies=["Penicillin", ""])
        assert "cannot be empty" in str(exc_info.value)
    
    def test_whitespace_only_allergy(self):
        """Test that whitespace-only allergies are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MedicalHistory(allergies=["Penicillin", "   "])
        assert "cannot be empty" in str(exc_info.value)


class TestInsuranceHistoryEntry:
    """Tests for InsuranceHistoryEntry model."""
    
    def test_valid_completed_policy(self):
        """Test creating a valid completed policy entry."""
        entry = InsuranceHistoryEntry(
            policy_id="POL-001",
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
            claims_made=2
        )
        assert entry.policy_id == "POL-001"
        assert entry.end_date is not None
    
    def test_valid_active_policy(self):
        """Test creating a valid active policy entry."""
        entry = InsuranceHistoryEntry(
            policy_id="POL-002",
            start_date=date(2024, 1, 1),
            end_date=None,
            claims_made=0
        )
        assert entry.end_date is None
    
    def test_empty_policy_id(self):
        """Test that empty policy ID is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InsuranceHistoryEntry(
                policy_id="",
                start_date=date(2020, 1, 1),
                end_date=None,
                claims_made=0
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_negative_claims_made(self):
        """Test that negative claims count is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InsuranceHistoryEntry(
                policy_id="POL-001",
                start_date=date(2020, 1, 1),
                end_date=None,
                claims_made=-1
            )
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_start_date_after_end_date(self):
        """Test that start date after end date is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InsuranceHistoryEntry(
                policy_id="POL-001",
                start_date=date(2024, 1, 1),
                end_date=date(2023, 1, 1),
                claims_made=0
            )
        assert "Start date cannot be after end date" in str(exc_info.value)
    
    def test_future_start_date(self):
        """Test that future start date is rejected."""
        future_date = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            InsuranceHistoryEntry(
                policy_id="POL-001",
                start_date=future_date,
                end_date=None,
                claims_made=0
            )
        assert "cannot be in the future" in str(exc_info.value)
    
    def test_future_end_date(self):
        """Test that future end date is rejected."""
        future_date = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            InsuranceHistoryEntry(
                policy_id="POL-001",
                start_date=date(2020, 1, 1),
                end_date=future_date,
                claims_made=0
            )
        assert "cannot be in the future" in str(exc_info.value)


class TestUserProfile:
    """Tests for UserProfile model."""
    
    def test_valid_user_profile(self, valid_user_profile_data):
        """Test creating a valid user profile."""
        profile = UserProfile(**valid_user_profile_data)
        assert profile.user_id == "USER-001"
        assert profile.demographics.age == 35
        assert len(profile.medical_history.pre_existing_diseases) == 2
        assert profile.consent_given is True
    
    def test_empty_user_id(self, valid_user_profile_data):
        """Test that empty user ID is rejected."""
        valid_user_profile_data["user_id"] = ""
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(**valid_user_profile_data)
        assert "at least 1 character" in str(exc_info.value)
    
    def test_invalid_language_preference(self, valid_user_profile_data):
        """Test that invalid language preference is rejected."""
        valid_user_profile_data["language_preference"] = "fr"  # French not supported
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(**valid_user_profile_data)
        assert "Language must be one of" in str(exc_info.value)
    
    def test_language_preference_case_insensitive(self, valid_user_profile_data):
        """Test that language preference is case-insensitive."""
        valid_user_profile_data["language_preference"] = "EN"
        profile = UserProfile(**valid_user_profile_data)
        assert profile.language_preference == "en"
    
    def test_all_valid_languages(self, valid_user_profile_data):
        """Test all valid language preferences."""
        valid_languages = ["en", "hi", "ta", "te", "bn", "mr", "gu"]
        for lang in valid_languages:
            valid_user_profile_data["language_preference"] = lang
            profile = UserProfile(**valid_user_profile_data)
            assert profile.language_preference == lang.lower()
    
    def test_invalid_data_retention_preference(self, valid_user_profile_data):
        """Test that invalid data retention preference is rejected."""
        valid_user_profile_data["data_retention_preference"] = "forever"
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(**valid_user_profile_data)
        assert "Data retention preference must be one of" in str(exc_info.value)
    
    def test_data_retention_case_insensitive(self, valid_user_profile_data):
        """Test that data retention preference is case-insensitive."""
        valid_user_profile_data["data_retention_preference"] = "STANDARD"
        profile = UserProfile(**valid_user_profile_data)
        assert profile.data_retention_preference == "standard"
    
    def test_default_values(self, valid_demographics, valid_medical_history):
        """Test that default values are set correctly."""
        profile = UserProfile(
            user_id="USER-002",
            demographics=valid_demographics,
            medical_history=valid_medical_history
        )
        assert profile.language_preference == "en"
        assert profile.consent_given is False
        assert profile.data_retention_preference == "standard"
        assert len(profile.insurance_history) == 0
    
    def test_timestamps_auto_generated(self, valid_user_profile_data):
        """Test that timestamps are automatically generated."""
        profile = UserProfile(**valid_user_profile_data)
        
        assert profile.created_at is not None
        assert profile.updated_at is not None
        assert isinstance(profile.created_at, datetime)
        assert isinstance(profile.updated_at, datetime)
        # Should be very recent
        assert datetime.now(timezone.utc) - profile.created_at < timedelta(minutes=1)
    
    def test_to_dict_with_sensitive_data(self, valid_user_profile_data):
        """Test serialization with sensitive data included."""
        profile = UserProfile(**valid_user_profile_data)
        profile_dict = profile.to_dict(include_sensitive=True)
        
        assert isinstance(profile_dict, dict)
        assert profile_dict["user_id"] == "USER-001"
        assert "medical_history" in profile_dict
        assert "pre_existing_diseases" in profile_dict["medical_history"]
        assert len(profile_dict["medical_history"]["pre_existing_diseases"]) == 2
    
    def test_to_dict_without_sensitive_data(self, valid_user_profile_data):
        """Test privacy-aware serialization without sensitive data."""
        profile = UserProfile(**valid_user_profile_data)
        profile_dict = profile.to_dict(include_sensitive=False)
        
        assert isinstance(profile_dict, dict)
        assert profile_dict["user_id"] == "USER-001"
        assert "medical_history" in profile_dict
        # Should only have counts, not actual data
        assert "pre_existing_diseases_count" in profile_dict["medical_history"]
        assert profile_dict["medical_history"]["pre_existing_diseases_count"] == 2
        assert "pre_existing_diseases" not in profile_dict["medical_history"]
        assert profile_dict["medical_history"]["current_medications_count"] == 2
        assert profile_dict["medical_history"]["allergies_count"] == 2
        assert profile_dict["medical_history"]["past_surgeries_count"] == 1
    
    def test_from_dict_deserialization(self, valid_user_profile_data):
        """Test deserialization from dictionary."""
        profile = UserProfile(**valid_user_profile_data)
        profile_dict = profile.to_dict(include_sensitive=True)
        
        # Deserialize back
        restored_profile = UserProfile.from_dict(profile_dict)
        
        assert restored_profile.user_id == profile.user_id
        assert restored_profile.demographics.age == profile.demographics.age
        assert len(restored_profile.medical_history.pre_existing_diseases) == 2
    
    def test_get_ped_list(self, valid_user_profile_data):
        """Test getting list of pre-existing disease names."""
        profile = UserProfile(**valid_user_profile_data)
        ped_list = profile.get_ped_list()
        
        assert len(ped_list) == 2
        assert "Type 2 Diabetes" in ped_list
        assert "Hypertension" in ped_list
    
    def test_get_ped_list_empty(self, valid_demographics):
        """Test getting PED list when empty."""
        profile = UserProfile(
            user_id="USER-003",
            demographics=valid_demographics,
            medical_history=MedicalHistory()
        )
        ped_list = profile.get_ped_list()
        assert len(ped_list) == 0
    
    def test_get_medication_list(self, valid_user_profile_data):
        """Test getting list of medication names."""
        profile = UserProfile(**valid_user_profile_data)
        med_list = profile.get_medication_list()
        
        assert len(med_list) == 2
        assert "Metformin" in med_list
        assert "Lisinopril" in med_list
    
    def test_get_allergy_list(self, valid_user_profile_data):
        """Test getting list of allergies."""
        profile = UserProfile(**valid_user_profile_data)
        allergy_list = profile.get_allergy_list()
        
        assert len(allergy_list) == 2
        assert "Penicillin" in allergy_list
        assert "Sulfa drugs" in allergy_list
    
    def test_has_ped_exact_match(self, valid_user_profile_data):
        """Test checking for specific PED with exact match."""
        profile = UserProfile(**valid_user_profile_data)
        
        assert profile.has_ped("Type 2 Diabetes") is True
        assert profile.has_ped("Hypertension") is True
        assert profile.has_ped("Asthma") is False
    
    def test_has_ped_partial_match(self, valid_user_profile_data):
        """Test checking for PED with partial match."""
        profile = UserProfile(**valid_user_profile_data)
        
        assert profile.has_ped("Diabetes") is True
        assert profile.has_ped("diabetes") is True  # Case insensitive
        assert profile.has_ped("Hyper") is True
    
    def test_has_ped_case_insensitive(self, valid_user_profile_data):
        """Test that PED check is case-insensitive."""
        profile = UserProfile(**valid_user_profile_data)
        
        assert profile.has_ped("TYPE 2 DIABETES") is True
        assert profile.has_ped("hypertension") is True
    
    def test_has_allergy(self, valid_user_profile_data):
        """Test checking for specific allergy."""
        profile = UserProfile(**valid_user_profile_data)
        
        assert profile.has_allergy("Penicillin") is True
        assert profile.has_allergy("Sulfa drugs") is True
        assert profile.has_allergy("Peanuts") is False
    
    def test_has_allergy_partial_match(self, valid_user_profile_data):
        """Test checking for allergy with partial match."""
        profile = UserProfile(**valid_user_profile_data)
        
        assert profile.has_allergy("Penicil") is True
        assert profile.has_allergy("Sulfa") is True
    
    def test_has_allergy_case_insensitive(self, valid_user_profile_data):
        """Test that allergy check is case-insensitive."""
        profile = UserProfile(**valid_user_profile_data)
        
        assert profile.has_allergy("PENICILLIN") is True
        assert profile.has_allergy("sulfa drugs") is True
    
    def test_get_active_policies(self, valid_user_profile_data):
        """Test getting active insurance policies."""
        profile = UserProfile(**valid_user_profile_data)
        active_policies = profile.get_active_policies()
        
        assert len(active_policies) == 1
        assert active_policies[0].policy_id == "POL-2024-001"
        assert active_policies[0].end_date is None
    
    def test_get_active_policies_none(self, valid_demographics, valid_medical_history):
        """Test getting active policies when none exist."""
        profile = UserProfile(
            user_id="USER-004",
            demographics=valid_demographics,
            medical_history=valid_medical_history,
            insurance_history=[
                InsuranceHistoryEntry(
                    policy_id="POL-OLD",
                    start_date=date(2020, 1, 1),
                    end_date=date(2023, 12, 31),
                    claims_made=1
                )
            ]
        )
        active_policies = profile.get_active_policies()
        assert len(active_policies) == 0
    
    def test_update_timestamp(self, valid_user_profile_data):
        """Test updating the timestamp."""
        profile = UserProfile(**valid_user_profile_data)
        original_updated_at = profile.updated_at
        
        # Wait a tiny bit to ensure time difference
        import time
        time.sleep(0.01)
        
        profile.update_timestamp()
        
        assert profile.updated_at > original_updated_at


class TestUserProfileEdgeCases:
    """Edge case tests for UserProfile."""
    
    def test_minimum_valid_profile(self, valid_demographics):
        """Test creating a profile with minimum required fields."""
        profile = UserProfile(
            user_id="MIN-001",
            demographics=valid_demographics,
            medical_history=MedicalHistory()
        )
        
        assert profile.user_id == "MIN-001"
        assert len(profile.medical_history.pre_existing_diseases) == 0
        assert len(profile.insurance_history) == 0
    
    def test_profile_with_many_peds(self, valid_demographics):
        """Test profile with many pre-existing diseases."""
        many_peds = [
            PreExistingDisease(
                condition=f"Condition {i}",
                diagnosis_date=date(2020, 1, 1),
                severity="mild"
            )
            for i in range(50)
        ]
        
        profile = UserProfile(
            user_id="USER-MANY-PEDS",
            demographics=valid_demographics,
            medical_history=MedicalHistory(pre_existing_diseases=many_peds)
        )
        
        assert len(profile.medical_history.pre_existing_diseases) == 50
        assert len(profile.get_ped_list()) == 50
    
    def test_profile_with_many_medications(self, valid_demographics):
        """Test profile with many medications."""
        many_meds = [
            Medication(
                name=f"Medication {i}",
                dosage="100mg",
                start_date=date(2020, 1, 1)
            )
            for i in range(30)
        ]
        
        profile = UserProfile(
            user_id="USER-MANY-MEDS",
            demographics=valid_demographics,
            medical_history=MedicalHistory(current_medications=many_meds)
        )
        
        assert len(profile.medical_history.current_medications) == 30
    
    def test_profile_with_many_allergies(self, valid_demographics):
        """Test profile with many allergies."""
        many_allergies = [f"Allergen {i}" for i in range(100)]
        
        profile = UserProfile(
            user_id="USER-MANY-ALLERGIES",
            demographics=valid_demographics,
            medical_history=MedicalHistory(allergies=many_allergies)
        )
        
        assert len(profile.medical_history.allergies) == 100
    
    def test_profile_with_long_insurance_history(self, valid_demographics, valid_medical_history):
        """Test profile with extensive insurance history."""
        long_history = [
            InsuranceHistoryEntry(
                policy_id=f"POL-{i}",
                start_date=date(2000 + i, 1, 1),
                end_date=date(2000 + i, 12, 31),
                claims_made=i % 5
            )
            for i in range(20)
        ]
        
        profile = UserProfile(
            user_id="USER-LONG-HISTORY",
            demographics=valid_demographics,
            medical_history=valid_medical_history,
            insurance_history=long_history
        )
        
        assert len(profile.insurance_history) == 20
    
    def test_very_old_diagnosis(self, valid_demographics):
        """Test PED with very old diagnosis date."""
        old_ped = PreExistingDisease(
            condition="Old Condition",
            diagnosis_date=date(1950, 1, 1),
            severity="mild"
        )
        
        profile = UserProfile(
            user_id="USER-OLD-PED",
            demographics=valid_demographics,
            medical_history=MedicalHistory(pre_existing_diseases=[old_ped])
        )
        
        assert profile.medical_history.pre_existing_diseases[0].diagnosis_date.year == 1950
    
    def test_boundary_age_zero(self):
        """Test demographics with age zero (newborn)."""
        demo = Demographics(age=0, gender="other", location="Mumbai")
        assert demo.age == 0
    
    def test_boundary_age_150(self):
        """Test demographics with age 150 (maximum)."""
        demo = Demographics(age=150, gender="other", location="Mumbai")
        assert demo.age == 150
    
    def test_profile_without_consent(self, valid_demographics, valid_medical_history):
        """Test profile without consent given."""
        profile = UserProfile(
            user_id="USER-NO-CONSENT",
            demographics=valid_demographics,
            medical_history=valid_medical_history,
            consent_given=False
        )
        
        assert profile.consent_given is False
    
    def test_profile_with_minimal_retention(self, valid_demographics, valid_medical_history):
        """Test profile with minimal data retention preference."""
        profile = UserProfile(
            user_id="USER-MINIMAL",
            demographics=valid_demographics,
            medical_history=valid_medical_history,
            data_retention_preference="minimal"
        )
        
        assert profile.data_retention_preference == "minimal"
