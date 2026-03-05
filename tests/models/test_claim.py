"""Unit tests for ClaimDetails data model."""

import pytest
from datetime import date, datetime, timedelta, timezone
from pydantic import ValidationError

from healthcare_insurance_platform.models.claim import (
    ClaimDetails,
    TreatmentDetails,
    DocumentProvided,
)


@pytest.fixture
def valid_treatment_details():
    """Create valid treatment details."""
    return TreatmentDetails(
        condition="Acute Appendicitis",
        hospital="City General Hospital",
        admission_date=date.today() - timedelta(days=5),
        discharge_date=date.today() - timedelta(days=2),
        procedures=["Appendectomy", "Post-operative care"],
        diagnosis="Acute appendicitis with peritonitis"
    )


@pytest.fixture
def valid_documents():
    """Create valid document list."""
    return [
        DocumentProvided(
            document_type="discharge_summary",
            file_name="discharge_summary.pdf"
        ),
        DocumentProvided(
            document_type="hospital_bills",
            file_name="bills.pdf"
        )
    ]


@pytest.fixture
def valid_claim_data(valid_treatment_details, valid_documents):
    """Create valid claim details data."""
    return {
        "claim_id": "CLM-2024-001",
        "user_id": "USR-001",
        "policy_id": "POL-2024-001",
        "claim_type": "hospitalization",
        "claim_amount": 50000.0,
        "treatment_details": valid_treatment_details,
        "documents_provided": valid_documents,
        "claim_date": date.today(),
        "status": "pending",
    }


class TestTreatmentDetails:
    """Tests for TreatmentDetails model."""
    
    def test_valid_treatment_details(self, valid_treatment_details):
        """Test creating valid treatment details."""
        assert valid_treatment_details.condition == "Acute Appendicitis"
        assert valid_treatment_details.hospital == "City General Hospital"
        assert len(valid_treatment_details.procedures) == 2
    
    def test_empty_condition(self):
        """Test that empty condition is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TreatmentDetails(
                condition="",
                hospital="Hospital",
                admission_date=date.today(),
                diagnosis="Some diagnosis"
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_empty_hospital(self):
        """Test that empty hospital is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TreatmentDetails(
                condition="Condition",
                hospital="",
                admission_date=date.today(),
                diagnosis="Diagnosis"
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_future_admission_date(self):
        """Test that future admission date is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TreatmentDetails(
                condition="Condition",
                hospital="Hospital",
                admission_date=date.today() + timedelta(days=1),
                diagnosis="Diagnosis"
            )
        assert "cannot be in the future" in str(exc_info.value)
    
    def test_future_discharge_date(self):
        """Test that future discharge date is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TreatmentDetails(
                condition="Condition",
                hospital="Hospital",
                admission_date=date.today(),
                discharge_date=date.today() + timedelta(days=1),
                diagnosis="Diagnosis"
            )
        assert "cannot be in the future" in str(exc_info.value)
    
    def test_discharge_before_admission(self):
        """Test that discharge date before admission date is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TreatmentDetails(
                condition="Condition",
                hospital="Hospital",
                admission_date=date.today(),
                discharge_date=date.today() - timedelta(days=1),
                diagnosis="Diagnosis"
            )
        assert "Admission date cannot be after discharge date" in str(exc_info.value)
    
    def test_same_admission_and_discharge_date(self):
        """Test that same admission and discharge date is valid."""
        treatment = TreatmentDetails(
            condition="Condition",
            hospital="Hospital",
            admission_date=date.today(),
            discharge_date=date.today(),
            diagnosis="Diagnosis"
        )
        assert treatment.admission_date == treatment.discharge_date
    
    def test_no_discharge_date(self):
        """Test that discharge date can be None (ongoing treatment)."""
        treatment = TreatmentDetails(
            condition="Condition",
            hospital="Hospital",
            admission_date=date.today() - timedelta(days=2),
            discharge_date=None,
            diagnosis="Diagnosis"
        )
        assert treatment.discharge_date is None
    
    def test_empty_procedures_list(self):
        """Test that empty procedures list is valid."""
        treatment = TreatmentDetails(
            condition="Condition",
            hospital="Hospital",
            admission_date=date.today(),
            procedures=[],
            diagnosis="Diagnosis"
        )
        assert len(treatment.procedures) == 0
    
    def test_empty_procedure_name(self):
        """Test that empty procedure names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TreatmentDetails(
                condition="Condition",
                hospital="Hospital",
                admission_date=date.today(),
                procedures=["Surgery", ""],
                diagnosis="Diagnosis"
            )
        assert "cannot be empty" in str(exc_info.value)


class TestDocumentProvided:
    """Tests for DocumentProvided model."""
    
    def test_valid_document(self):
        """Test creating a valid document."""
        doc = DocumentProvided(
            document_type="discharge_summary",
            file_name="summary.pdf"
        )
        assert doc.document_type == "discharge_summary"
        assert doc.file_name == "summary.pdf"
        assert doc.upload_date is not None
    
    def test_empty_document_type(self):
        """Test that empty document type is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentProvided(document_type="", file_name="file.pdf")
        assert "at least 1 character" in str(exc_info.value)
    
    def test_empty_file_name(self):
        """Test that empty file name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentProvided(document_type="bill", file_name="")
        assert "at least 1 character" in str(exc_info.value)
    
    def test_upload_date_auto_generated(self):
        """Test that upload date is automatically generated."""
        doc = DocumentProvided(
            document_type="bill",
            file_name="bill.pdf"
        )
        assert doc.upload_date is not None
        assert isinstance(doc.upload_date, datetime)
        # Should be very recent (within last minute)
        assert datetime.now(timezone.utc) - doc.upload_date < timedelta(minutes=1)
    
    def test_upload_date_can_be_set(self):
        """Test that upload date can be explicitly set."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        doc = DocumentProvided(
            document_type="bill",
            file_name="bill.pdf",
            upload_date=custom_time
        )
        assert doc.upload_date == custom_time


class TestClaimDetails:
    """Tests for ClaimDetails model."""
    
    def test_valid_claim_details(self, valid_claim_data):
        """Test creating valid claim details."""
        claim = ClaimDetails(**valid_claim_data)
        assert claim.claim_id == "CLM-2024-001"
        assert claim.user_id == "USR-001"
        assert claim.policy_id == "POL-2024-001"
        assert claim.claim_type == "hospitalization"
        assert claim.claim_amount == 50000.0
        assert claim.status == "pending"
    
    def test_empty_claim_id(self, valid_claim_data):
        """Test that empty claim ID is rejected."""
        valid_claim_data["claim_id"] = ""
        with pytest.raises(ValidationError) as exc_info:
            ClaimDetails(**valid_claim_data)
        assert "at least 1 character" in str(exc_info.value)
    
    def test_empty_user_id(self, valid_claim_data):
        """Test that empty user ID is rejected."""
        valid_claim_data["user_id"] = ""
        with pytest.raises(ValidationError) as exc_info:
            ClaimDetails(**valid_claim_data)
        assert "at least 1 character" in str(exc_info.value)
    
    def test_empty_policy_id(self, valid_claim_data):
        """Test that empty policy ID is rejected."""
        valid_claim_data["policy_id"] = ""
        with pytest.raises(ValidationError) as exc_info:
            ClaimDetails(**valid_claim_data)
        assert "at least 1 character" in str(exc_info.value)
    
    def test_invalid_claim_type(self, valid_claim_data):
        """Test that invalid claim type is rejected."""
        valid_claim_data["claim_type"] = "dental"
        with pytest.raises(ValidationError) as exc_info:
            ClaimDetails(**valid_claim_data)
        assert "Claim type must be one of" in str(exc_info.value)
    
    def test_claim_type_case_insensitive(self, valid_claim_data):
        """Test that claim type is case-insensitive."""
        valid_claim_data["claim_type"] = "HOSPITALIZATION"
        claim = ClaimDetails(**valid_claim_data)
        assert claim.claim_type == "hospitalization"
    
    def test_valid_claim_types(self, valid_claim_data):
        """Test all valid claim types."""
        valid_types = ["hospitalization", "surgery", "diagnostic", "pharmacy"]
        for claim_type in valid_types:
            valid_claim_data["claim_type"] = claim_type
            claim = ClaimDetails(**valid_claim_data)
            assert claim.claim_type == claim_type
    
    def test_negative_claim_amount(self, valid_claim_data):
        """Test that negative claim amount is rejected."""
        valid_claim_data["claim_amount"] = -1000.0
        with pytest.raises(ValidationError) as exc_info:
            ClaimDetails(**valid_claim_data)
        assert "Claim amount cannot be negative" in str(exc_info.value)
    
    def test_zero_claim_amount(self, valid_claim_data):
        """Test that zero claim amount is valid."""
        valid_claim_data["claim_amount"] = 0.0
        claim = ClaimDetails(**valid_claim_data)
        assert claim.claim_amount == 0.0
    
    def test_unreasonably_high_claim_amount(self, valid_claim_data):
        """Test that unreasonably high claim amount is rejected."""
        valid_claim_data["claim_amount"] = 150_000_000.0  # 15 crore
        with pytest.raises(ValidationError) as exc_info:
            ClaimDetails(**valid_claim_data)
        assert "unreasonably high" in str(exc_info.value)
    
    def test_boundary_claim_amount(self, valid_claim_data):
        """Test boundary value for claim amount."""
        valid_claim_data["claim_amount"] = 99_999_999.0
        claim = ClaimDetails(**valid_claim_data)
        assert claim.claim_amount == 99_999_999.0
    
    def test_future_claim_date(self, valid_claim_data):
        """Test that future claim date is rejected."""
        valid_claim_data["claim_date"] = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            ClaimDetails(**valid_claim_data)
        assert "cannot be in the future" in str(exc_info.value)
    
    def test_claim_date_before_admission(self, valid_claim_data):
        """Test that claim date before admission date is rejected."""
        valid_claim_data["treatment_details"].admission_date = date.today()
        valid_claim_data["claim_date"] = date.today() - timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            ClaimDetails(**valid_claim_data)
        assert "Claim date cannot be before admission date" in str(exc_info.value)
    
    def test_claim_date_same_as_admission(self, valid_claim_data):
        """Test that claim date same as admission date is valid."""
        admission = date.today() - timedelta(days=5)
        valid_claim_data["treatment_details"].admission_date = admission
        valid_claim_data["claim_date"] = admission
        claim = ClaimDetails(**valid_claim_data)
        assert claim.claim_date == admission
    
    def test_invalid_status(self, valid_claim_data):
        """Test that invalid status is rejected."""
        valid_claim_data["status"] = "processing"
        with pytest.raises(ValidationError) as exc_info:
            ClaimDetails(**valid_claim_data)
        assert "Status must be one of" in str(exc_info.value)
    
    def test_status_case_insensitive(self, valid_claim_data):
        """Test that status is case-insensitive."""
        valid_claim_data["status"] = "PENDING"
        claim = ClaimDetails(**valid_claim_data)
        assert claim.status == "pending"
    
    def test_valid_statuses(self, valid_claim_data):
        """Test all valid statuses."""
        valid_statuses = ["pending", "approved"]
        for status in valid_statuses:
            valid_claim_data["status"] = status
            valid_claim_data["rejection_reason"] = None
            claim = ClaimDetails(**valid_claim_data)
            assert claim.status == status
    
    def test_rejected_status_without_reason(self, valid_claim_data):
        """Test that rejected status without reason is rejected."""
        valid_claim_data["status"] = "rejected"
        valid_claim_data["rejection_reason"] = None
        with pytest.raises(ValidationError) as exc_info:
            ClaimDetails(**valid_claim_data)
        assert "Rejection reason must be provided" in str(exc_info.value)
    
    def test_rejected_status_with_reason(self, valid_claim_data):
        """Test that rejected status with reason is valid."""
        valid_claim_data["status"] = "rejected"
        valid_claim_data["rejection_reason"] = "Pre-existing condition not covered"
        claim = ClaimDetails(**valid_claim_data)
        assert claim.status == "rejected"
        assert claim.rejection_reason == "Pre-existing condition not covered"
    
    def test_non_rejected_status_with_reason(self, valid_claim_data):
        """Test that non-rejected status with rejection reason is rejected."""
        valid_claim_data["status"] = "approved"
        valid_claim_data["rejection_reason"] = "Some reason"
        with pytest.raises(ValidationError) as exc_info:
            ClaimDetails(**valid_claim_data)
        assert "should only be provided when status is rejected" in str(exc_info.value)
    
    def test_default_status(self, valid_claim_data):
        """Test that default status is pending."""
        del valid_claim_data["status"]
        claim = ClaimDetails(**valid_claim_data)
        assert claim.status == "pending"
    
    def test_default_claim_date(self, valid_claim_data):
        """Test that default claim date is today."""
        del valid_claim_data["claim_date"]
        claim = ClaimDetails(**valid_claim_data)
        assert claim.claim_date == date.today()
    
    def test_empty_documents_list(self, valid_claim_data):
        """Test that empty documents list is valid."""
        valid_claim_data["documents_provided"] = []
        claim = ClaimDetails(**valid_claim_data)
        assert len(claim.documents_provided) == 0
    
    def test_timestamps_auto_generated(self, valid_claim_data):
        """Test that timestamps are automatically generated."""
        claim = ClaimDetails(**valid_claim_data)
        assert claim.created_at is not None
        assert claim.updated_at is not None
        assert isinstance(claim.created_at, datetime)
        assert isinstance(claim.updated_at, datetime)
        # Should be very recent (within last minute)
        assert datetime.now(timezone.utc) - claim.created_at < timedelta(minutes=1)
        assert datetime.now(timezone.utc) - claim.updated_at < timedelta(minutes=1)


class TestClaimDetailsMethods:
    """Tests for ClaimDetails methods."""
    
    def test_to_dict_serialization(self, valid_claim_data):
        """Test serialization to dictionary."""
        claim = ClaimDetails(**valid_claim_data)
        claim_dict = claim.to_dict()
        
        assert isinstance(claim_dict, dict)
        assert claim_dict["claim_id"] == "CLM-2024-001"
        assert claim_dict["claim_amount"] == 50000.0
        assert "created_at" in claim_dict
        assert "updated_at" in claim_dict
    
    def test_from_dict_deserialization(self, valid_claim_data):
        """Test deserialization from dictionary."""
        claim = ClaimDetails(**valid_claim_data)
        claim_dict = claim.to_dict()
        
        # Deserialize back
        restored_claim = ClaimDetails.from_dict(claim_dict)
        
        assert restored_claim.claim_id == claim.claim_id
        assert restored_claim.claim_amount == claim.claim_amount
        assert restored_claim.user_id == claim.user_id
    
    def test_add_document(self, valid_claim_data):
        """Test adding a document to the claim."""
        claim = ClaimDetails(**valid_claim_data)
        initial_count = len(claim.documents_provided)
        initial_updated = claim.updated_at
        
        claim.add_document("prescription", "prescription.pdf")
        
        assert len(claim.documents_provided) == initial_count + 1
        assert claim.documents_provided[-1].document_type == "prescription"
        assert claim.documents_provided[-1].file_name == "prescription.pdf"
        assert claim.updated_at > initial_updated
    
    def test_get_document_types(self, valid_claim_data):
        """Test getting list of document types."""
        claim = ClaimDetails(**valid_claim_data)
        doc_types = claim.get_document_types()
        
        assert isinstance(doc_types, list)
        assert "discharge_summary" in doc_types
        assert "hospital_bills" in doc_types
        assert len(doc_types) == 2
    
    def test_get_document_types_empty(self, valid_claim_data):
        """Test getting document types when no documents provided."""
        valid_claim_data["documents_provided"] = []
        claim = ClaimDetails(**valid_claim_data)
        doc_types = claim.get_document_types()
        
        assert isinstance(doc_types, list)
        assert len(doc_types) == 0
    
    def test_has_document_type(self, valid_claim_data):
        """Test checking if specific document type exists."""
        claim = ClaimDetails(**valid_claim_data)
        
        assert claim.has_document_type("discharge_summary") is True
        assert claim.has_document_type("hospital_bills") is True
        assert claim.has_document_type("prescription") is False
    
    def test_has_document_type_case_insensitive(self, valid_claim_data):
        """Test that document type check is case-insensitive."""
        claim = ClaimDetails(**valid_claim_data)
        
        assert claim.has_document_type("DISCHARGE_SUMMARY") is True
        assert claim.has_document_type("Hospital_Bills") is True
    
    def test_has_document_type_partial_match(self, valid_claim_data):
        """Test that document type check works with partial matches."""
        claim = ClaimDetails(**valid_claim_data)
        
        assert claim.has_document_type("discharge") is True
        assert claim.has_document_type("bills") is True
    
    def test_update_status_to_approved(self, valid_claim_data):
        """Test updating status to approved."""
        claim = ClaimDetails(**valid_claim_data)
        initial_updated = claim.updated_at
        
        claim.update_status("approved")
        
        assert claim.status == "approved"
        assert claim.rejection_reason is None
        assert claim.updated_at > initial_updated
    
    def test_update_status_to_rejected(self, valid_claim_data):
        """Test updating status to rejected with reason."""
        claim = ClaimDetails(**valid_claim_data)
        
        claim.update_status("rejected", "Waiting period not completed")
        
        assert claim.status == "rejected"
        assert claim.rejection_reason == "Waiting period not completed"
    
    def test_update_status_to_rejected_without_reason(self, valid_claim_data):
        """Test that updating to rejected without reason raises error."""
        claim = ClaimDetails(**valid_claim_data)
        
        with pytest.raises(ValueError) as exc_info:
            claim.update_status("rejected")
        assert "Rejection reason must be provided" in str(exc_info.value)
    
    def test_update_status_invalid(self, valid_claim_data):
        """Test that updating to invalid status raises error."""
        claim = ClaimDetails(**valid_claim_data)
        
        with pytest.raises(ValueError) as exc_info:
            claim.update_status("processing")
        assert "Status must be one of" in str(exc_info.value)
    
    def test_update_timestamp(self, valid_claim_data):
        """Test updating timestamp."""
        claim = ClaimDetails(**valid_claim_data)
        initial_updated = claim.updated_at
        
        # Wait a tiny bit to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        claim.update_timestamp()
        
        assert claim.updated_at > initial_updated
    
    def test_get_treatment_duration_days(self, valid_claim_data):
        """Test calculating treatment duration."""
        claim = ClaimDetails(**valid_claim_data)
        duration = claim.get_treatment_duration_days()
        
        assert duration == 3  # 5 days ago to 2 days ago = 3 days
    
    def test_get_treatment_duration_days_no_discharge(self, valid_claim_data):
        """Test treatment duration when not discharged."""
        valid_claim_data["treatment_details"].discharge_date = None
        claim = ClaimDetails(**valid_claim_data)
        duration = claim.get_treatment_duration_days()
        
        assert duration is None
    
    def test_get_treatment_duration_days_same_day(self, valid_claim_data):
        """Test treatment duration for same-day admission and discharge."""
        same_date = date.today()
        valid_claim_data["treatment_details"].admission_date = same_date
        valid_claim_data["treatment_details"].discharge_date = same_date
        valid_claim_data["claim_date"] = same_date
        claim = ClaimDetails(**valid_claim_data)
        duration = claim.get_treatment_duration_days()
        
        assert duration == 0
    
    def test_is_pending(self, valid_claim_data):
        """Test checking if claim is pending."""
        claim = ClaimDetails(**valid_claim_data)
        assert claim.is_pending() is True
        assert claim.is_approved() is False
        assert claim.is_rejected() is False
    
    def test_is_approved(self, valid_claim_data):
        """Test checking if claim is approved."""
        valid_claim_data["status"] = "approved"
        claim = ClaimDetails(**valid_claim_data)
        assert claim.is_pending() is False
        assert claim.is_approved() is True
        assert claim.is_rejected() is False
    
    def test_is_rejected(self, valid_claim_data):
        """Test checking if claim is rejected."""
        valid_claim_data["status"] = "rejected"
        valid_claim_data["rejection_reason"] = "Some reason"
        claim = ClaimDetails(**valid_claim_data)
        assert claim.is_pending() is False
        assert claim.is_approved() is False
        assert claim.is_rejected() is True


class TestClaimDetailsEdgeCases:
    """Edge case tests for ClaimDetails."""
    
    def test_minimum_valid_claim(self):
        """Test creating a claim with minimum required fields."""
        treatment = TreatmentDetails(
            condition="Condition",
            hospital="Hospital",
            admission_date=date.today(),
            diagnosis="Diagnosis"
        )
        
        claim = ClaimDetails(
            claim_id="MIN-001",
            user_id="USR-001",
            policy_id="POL-001",
            claim_type="diagnostic",
            claim_amount=0.0,
            treatment_details=treatment
        )
        
        assert claim.claim_id == "MIN-001"
        assert claim.claim_amount == 0.0
        assert len(claim.documents_provided) == 0
    
    def test_claim_with_many_documents(self, valid_claim_data):
        """Test claim with large number of documents."""
        documents = [
            DocumentProvided(document_type=f"doc_{i}", file_name=f"file_{i}.pdf")
            for i in range(50)
        ]
        valid_claim_data["documents_provided"] = documents
        
        claim = ClaimDetails(**valid_claim_data)
        assert len(claim.documents_provided) == 50
    
    def test_claim_with_many_procedures(self, valid_claim_data):
        """Test claim with many procedures."""
        procedures = [f"Procedure {i}" for i in range(20)]
        valid_claim_data["treatment_details"].procedures = procedures
        
        claim = ClaimDetails(**valid_claim_data)
        assert len(claim.treatment_details.procedures) == 20
    
    def test_claim_with_very_long_diagnosis(self, valid_claim_data):
        """Test claim with very long diagnosis text."""
        long_diagnosis = "A" * 10000
        valid_claim_data["treatment_details"].diagnosis = long_diagnosis
        
        claim = ClaimDetails(**valid_claim_data)
        assert len(claim.treatment_details.diagnosis) == 10000
    
    def test_claim_with_very_long_rejection_reason(self, valid_claim_data):
        """Test claim with very long rejection reason."""
        long_reason = "B" * 5000
        valid_claim_data["status"] = "rejected"
        valid_claim_data["rejection_reason"] = long_reason
        
        claim = ClaimDetails(**valid_claim_data)
        assert len(claim.rejection_reason) == 5000
    
    def test_old_claim_date(self, valid_claim_data):
        """Test claim with old claim date."""
        old_date = date.today() - timedelta(days=365)
        valid_claim_data["treatment_details"].admission_date = old_date - timedelta(days=5)
        valid_claim_data["treatment_details"].discharge_date = old_date - timedelta(days=2)
        valid_claim_data["claim_date"] = old_date
        
        claim = ClaimDetails(**valid_claim_data)
        assert claim.claim_date == old_date
    
    def test_claim_date_equals_today(self, valid_claim_data):
        """Test claim with today's date."""
        valid_claim_data["claim_date"] = date.today()
        valid_claim_data["treatment_details"].admission_date = date.today()
        valid_claim_data["treatment_details"].discharge_date = date.today()
        
        claim = ClaimDetails(**valid_claim_data)
        assert claim.claim_date == date.today()
    
    def test_long_hospital_stay(self, valid_claim_data):
        """Test claim with very long hospital stay."""
        admission = date.today() - timedelta(days=365)
        discharge = date.today() - timedelta(days=1)
        valid_claim_data["treatment_details"].admission_date = admission
        valid_claim_data["treatment_details"].discharge_date = discharge
        valid_claim_data["claim_date"] = date.today()
        
        claim = ClaimDetails(**valid_claim_data)
        duration = claim.get_treatment_duration_days()
        assert duration == 364
