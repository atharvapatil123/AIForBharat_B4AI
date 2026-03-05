"""Unit tests for Knowledge Base service."""

import pytest
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from healthcare_insurance_platform.services.knowledge_base import (
    KnowledgeBaseService,
    DocumentValidationError,
)
from healthcare_insurance_platform.models.policy import PolicyDocument


@pytest.fixture
def knowledge_base_service():
    """Create a KnowledgeBaseService instance for testing."""
    return KnowledgeBaseService()


@pytest.fixture
def sample_policy_text():
    """Sample policy document text for testing."""
    return """
    Health Insurance Policy
    
    Policy Name: Comprehensive Health Cover
    Provider: ABC Insurance Company
    
    Coverage Details:
    Sum Insured: Rs. 5,00,000
    Annual Premium: Rs. 15,000
    
    Waiting Periods:
    Initial waiting period: 30 days
    Pre-existing disease waiting period: 2 years
    
    What is Covered:
    - Hospitalization expenses
    - Surgery costs
    - Diagnostic tests
    - Ambulance charges
    - Room rent up to Rs. 5,000 per day
    - ICU charges
    
    Exclusions:
    - Cosmetic surgery
    - Dental treatment (unless due to accident)
    - Infertility treatment
    - War injuries
    - Self-inflicted injuries
    - Substance abuse treatment
    - Experimental treatments
    """


@pytest.fixture
def sample_text_file(tmp_path, sample_policy_text):
    """Create a sample text file for testing."""
    file_path = tmp_path / "sample_policy.txt"
    file_path.write_text(sample_policy_text)
    return file_path


class TestDocumentParsing:
    """Test document parsing functionality."""
    
    def test_parse_text_file(self, knowledge_base_service, sample_text_file):
        """Test parsing a text file."""
        from healthcare_insurance_platform.utils.document_parser import TextFileParser
        
        parser = TextFileParser()
        content = parser.parse(sample_text_file)
        
        assert content is not None
        assert len(content) > 0
        assert "Health Insurance Policy" in content
        assert "Rs. 5,00,000" in content
    
    def test_parse_nonexistent_file(self, knowledge_base_service):
        """Test parsing a file that doesn't exist."""
        from healthcare_insurance_platform.utils.document_parser import TextFileParser
        
        parser = TextFileParser()
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.txt"))
    
    def test_unsupported_file_format(self, knowledge_base_service, tmp_path):
        """Test handling of unsupported file formats."""
        from healthcare_insurance_platform.utils.document_parser import get_parser
        
        unsupported_file = tmp_path / "document.docx"
        unsupported_file.write_text("content")
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            get_parser(unsupported_file)


class TestPolicyInformationExtraction:
    """Test policy information extraction."""
    
    def test_extract_coverage_amount(self, knowledge_base_service, sample_policy_text):
        """Test extracting coverage amount from policy text."""
        coverage = knowledge_base_service.extractor.extract_coverage_amount(
            sample_policy_text
        )
        
        assert coverage is not None
        assert coverage == 500000.0
    
    def test_extract_premium(self, knowledge_base_service, sample_policy_text):
        """Test extracting premium from policy text."""
        premium = knowledge_base_service.extractor.extract_premium(sample_policy_text)
        
        assert premium is not None
        assert premium == 15000.0
    
    def test_extract_waiting_periods(self, knowledge_base_service, sample_policy_text):
        """Test extracting waiting periods from policy text."""
        waiting_periods = knowledge_base_service.extractor.extract_waiting_periods(
            sample_policy_text
        )
        
        assert waiting_periods is not None
        assert 'general' in waiting_periods
        assert 'pre_existing' in waiting_periods
        assert waiting_periods['general'] == 30
        assert waiting_periods['pre_existing'] == 730  # 2 years in days
    
    def test_extract_exclusions(self, knowledge_base_service, sample_policy_text):
        """Test extracting exclusions from policy text."""
        exclusions = knowledge_base_service.extractor.extract_exclusions(
            sample_policy_text
        )
        
        assert exclusions is not None
        assert len(exclusions) > 0
        # Check for some expected exclusions
        exclusion_text = " ".join(exclusions).lower()
        assert any(term in exclusion_text for term in ['cosmetic', 'dental', 'infertility'])
    
    def test_extract_inclusions(self, knowledge_base_service, sample_policy_text):
        """Test extracting inclusions from policy text."""
        inclusions = knowledge_base_service.extractor.extract_inclusions(
            sample_policy_text
        )
        
        assert inclusions is not None
        assert len(inclusions) > 0
        # Check for some expected inclusions
        inclusion_text = " ".join(inclusions).lower()
        assert any(term in inclusion_text for term in ['hospitalization', 'surgery', 'diagnostic'])


class TestDocumentValidation:
    """Test document validation functionality."""
    
    def test_validate_complete_document(self, knowledge_base_service, sample_text_file):
        """Test validation of a complete document."""
        result = knowledge_base_service.validate_document_before_ingestion(
            sample_text_file
        )
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert result['extracted_info'] is not None
        assert result['extracted_info']['coverage_amount'] == 500000.0
        assert result['extracted_info']['premium'] == 15000.0
    
    def test_validate_nonexistent_file(self, knowledge_base_service):
        """Test validation of a file that doesn't exist."""
        result = knowledge_base_service.validate_document_before_ingestion(
            Path("/nonexistent/file.txt")
        )
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert any("not found" in error.lower() for error in result['errors'])
    
    def test_validate_unsupported_format(self, knowledge_base_service, tmp_path):
        """Test validation of unsupported file format."""
        unsupported_file = tmp_path / "document.docx"
        unsupported_file.write_text("content")
        
        result = knowledge_base_service.validate_document_before_ingestion(
            unsupported_file
        )
        
        assert result['valid'] is False
        assert any("unsupported" in error.lower() for error in result['errors'])
    
    def test_validate_empty_document(self, knowledge_base_service, tmp_path):
        """Test validation of an empty document."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        
        result = knowledge_base_service.validate_document_before_ingestion(empty_file)
        
        assert result['valid'] is False
        assert any("too short" in error.lower() or "empty" in error.lower() 
                  for error in result['errors'])
    
    def test_validate_incomplete_document(self, knowledge_base_service, tmp_path):
        """Test validation of a document missing required information."""
        incomplete_text = """
        Health Insurance Policy
        
        This is a basic policy document without key information.
        """
        
        incomplete_file = tmp_path / "incomplete.txt"
        incomplete_file.write_text(incomplete_text)
        
        result = knowledge_base_service.validate_document_before_ingestion(
            incomplete_file
        )
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
        # Should have errors about missing coverage, premium, etc.


@pytest.mark.asyncio
class TestDocumentIngestion:
    """Test document ingestion functionality."""
    
    async def test_ingest_valid_document(
        self,
        knowledge_base_service,
        sample_text_file,
    ):
        """Test ingesting a valid policy document."""
        policy_document = await knowledge_base_service.ingest_policy_document(
            file_path=sample_text_file,
            provider_id="ABC_INS",
            policy_name="Comprehensive Health Cover",
            policy_type="individual",
            version="1.0",
            effective_date=date(2024, 1, 1),
        )
        
        assert policy_document is not None
        assert isinstance(policy_document, PolicyDocument)
        assert policy_document.policy_name == "Comprehensive Health Cover"
        assert policy_document.provider_id == "ABC_INS"
        assert policy_document.coverage_amount == 500000.0
        assert policy_document.premium == 15000.0
        assert len(policy_document.inclusions) > 0
        assert len(policy_document.exclusions) > 0
        assert len(policy_document.parsed_clauses) > 0
    
    async def test_ingest_nonexistent_file(self, knowledge_base_service):
        """Test ingesting a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            await knowledge_base_service.ingest_policy_document(
                file_path=Path("/nonexistent/file.txt"),
                provider_id="ABC_INS",
                policy_name="Test Policy",
                policy_type="individual",
                version="1.0",
                effective_date=date(2024, 1, 1),
            )
    
    async def test_ingest_invalid_document(self, knowledge_base_service, tmp_path):
        """Test ingesting a document with missing required information."""
        invalid_text = "This is not a valid policy document."
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text(invalid_text)
        
        with pytest.raises(DocumentValidationError):
            await knowledge_base_service.ingest_policy_document(
                file_path=invalid_file,
                provider_id="ABC_INS",
                policy_name="Invalid Policy",
                policy_type="individual",
                version="1.0",
                effective_date=date(2024, 1, 1),
            )
    
    async def test_ingest_with_vector_store(
        self,
        sample_text_file,
    ):
        """Test ingesting a document with vector store integration."""
        # Create mock vector store
        mock_vector_store = AsyncMock()
        mock_vector_store.add_documents = AsyncMock()
        
        service = KnowledgeBaseService(vector_store=mock_vector_store)
        
        policy_document = await service.ingest_policy_document(
            file_path=sample_text_file,
            provider_id="ABC_INS",
            policy_name="Comprehensive Health Cover",
            policy_type="individual",
            version="1.0",
            effective_date=date(2024, 1, 1),
        )
        
        assert policy_document is not None
        # Verify vector store was called
        mock_vector_store.add_documents.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_extract_coverage_with_different_formats(self, knowledge_base_service):
        """Test extracting coverage amount with different text formats."""
        test_cases = [
            ("Sum Insured: Rs. 5,00,000", 500000.0),
            ("Coverage: ₹500000", 500000.0),
            ("Insured Amount: Rs. 10,00,000", 1000000.0),
        ]
        
        for text, expected in test_cases:
            result = knowledge_base_service.extractor.extract_coverage_amount(text)
            assert result == expected, f"Failed for text: {text}"
    
    def test_extract_premium_with_different_formats(self, knowledge_base_service):
        """Test extracting premium with different text formats."""
        test_cases = [
            ("Premium: Rs. 15,000", 15000.0),
            ("Annual Premium: ₹15000", 15000.0),
            ("Premium Amount: Rs. 20,000", 20000.0),
        ]
        
        for text, expected in test_cases:
            result = knowledge_base_service.extractor.extract_premium(text)
            assert result == expected, f"Failed for text: {text}"
    
    def test_extract_waiting_period_in_months(self, knowledge_base_service):
        """Test extracting waiting periods specified in months."""
        text = "Pre-existing disease waiting period: 24 months"
        result = knowledge_base_service.extractor.extract_waiting_periods(text)
        
        assert result['pre_existing'] == 720  # 24 months * 30 days
    
    def test_extract_waiting_period_in_years(self, knowledge_base_service):
        """Test extracting waiting periods specified in years."""
        text = "Pre-existing disease waiting period: 2 years"
        result = knowledge_base_service.extractor.extract_waiting_periods(text)
        
        assert result['pre_existing'] == 730  # 2 years * 365 days
    
    @pytest.mark.asyncio
    async def test_ingest_document_with_special_characters(
        self,
        knowledge_base_service,
        tmp_path,
    ):
        """Test ingesting a document with special characters."""
        text_with_special_chars = """
        Health Insurance Policy
        
        Sum Insured: Rs. 5,00,000
        Premium: Rs. 15,000
        
        Coverage:
        - Hospitalization (including ICU)
        - Surgery & post-operative care
        - Diagnostic tests [X-ray, MRI, CT scan]
        
        Exclusions:
        - Cosmetic surgery
        - Dental treatment
        - War & nuclear risks
        """
        
        file_path = tmp_path / "special_chars.txt"
        file_path.write_text(text_with_special_chars)
        
        policy_document = await knowledge_base_service.ingest_policy_document(
            file_path=file_path,
            provider_id="ABC_INS",
            policy_name="Special Chars Policy",
            policy_type="individual",
            version="1.0",
            effective_date=date(2024, 1, 1),
        )
        
        assert policy_document is not None
        assert len(policy_document.inclusions) > 0
        assert len(policy_document.exclusions) > 0
