"""Unit tests for Knowledge Base semantic search functionality."""

import pytest
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from healthcare_insurance_platform.services.knowledge_base import KnowledgeBaseService
from healthcare_insurance_platform.models.policy import PolicyDocument


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store for testing."""
    mock = AsyncMock()
    mock.add_documents = AsyncMock(return_value=["id1", "id2", "id3"])
    mock.similarity_search = AsyncMock()
    return mock


@pytest.fixture
def knowledge_base_service_with_vector_store(mock_vector_store):
    """Create a KnowledgeBaseService with mock vector store."""
    return KnowledgeBaseService(vector_store=mock_vector_store)


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


class TestSemanticSearch:
    """Test semantic search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_policies_basic(
        self,
        knowledge_base_service_with_vector_store,
        mock_vector_store,
    ):
        """Test basic policy search."""
        # Setup mock response
        mock_vector_store.similarity_search.return_value = [
            (
                "Policy: Health Plus\nProvider: ABC Insurance\nCoverage: 500000",
                {
                    'policy_id': 'policy1',
                    'policy_name': 'Health Plus',
                    'provider_id': 'ABC_INS',
                    'policy_type': 'individual',
                },
                0.85,
            ),
            (
                "Policy: Family Care\nProvider: XYZ Insurance\nCoverage: 1000000",
                {
                    'policy_id': 'policy2',
                    'policy_name': 'Family Care',
                    'provider_id': 'XYZ_INS',
                    'policy_type': 'family',
                },
                0.75,
            ),
        ]
        
        # Execute search
        results = await knowledge_base_service_with_vector_store.search_policies(
            query="health insurance with good coverage",
            k=5,
        )
        
        # Verify results
        assert len(results) == 2
        assert results[0]['policy_id'] == 'policy1'
        assert results[0]['policy_name'] == 'Health Plus'
        assert results[0]['score'] == 0.85
        assert results[1]['policy_id'] == 'policy2'
        
        # Verify vector store was called correctly
        mock_vector_store.similarity_search.assert_called_once()
        call_args = mock_vector_store.similarity_search.call_args
        assert call_args[1]['query'] == "health insurance with good coverage"
        assert call_args[1]['k'] == 10  # k * 2 for filtering
    
    @pytest.mark.asyncio
    async def test_search_policies_with_provider_filter(
        self,
        knowledge_base_service_with_vector_store,
        mock_vector_store,
    ):
        """Test policy search with provider filter."""
        mock_vector_store.similarity_search.return_value = [
            (
                "Policy: Health Plus\nProvider: ABC Insurance",
                {
                    'policy_id': 'policy1',
                    'policy_name': 'Health Plus',
                    'provider_id': 'ABC_INS',
                    'policy_type': 'individual',
                },
                0.85,
            ),
        ]
        
        # Execute search with filter
        results = await knowledge_base_service_with_vector_store.search_policies(
            query="health insurance",
            filters={'provider_id': 'ABC_INS'},
            k=5,
        )
        
        # Verify filter was applied
        call_args = mock_vector_store.similarity_search.call_args
        assert call_args[1]['filter'] == {'provider_id': 'ABC_INS'}
        assert len(results) == 1
        assert results[0]['provider_id'] == 'ABC_INS'
    
    @pytest.mark.asyncio
    async def test_search_policies_with_policy_type_filter(
        self,
        knowledge_base_service_with_vector_store,
        mock_vector_store,
    ):
        """Test policy search with policy type filter."""
        mock_vector_store.similarity_search.return_value = [
            (
                "Policy: Family Care",
                {
                    'policy_id': 'policy2',
                    'policy_name': 'Family Care',
                    'provider_id': 'XYZ_INS',
                    'policy_type': 'family',
                },
                0.75,
            ),
        ]
        
        # Execute search with filter
        results = await knowledge_base_service_with_vector_store.search_policies(
            query="insurance",
            filters={'policy_type': 'family'},
            k=5,
        )
        
        # Verify filter was applied
        call_args = mock_vector_store.similarity_search.call_args
        assert call_args[1]['filter'] == {'policy_type': 'family'}
        assert len(results) == 1
        assert results[0]['policy_type'] == 'family'
    
    @pytest.mark.asyncio
    async def test_search_policies_deduplication(
        self,
        knowledge_base_service_with_vector_store,
        mock_vector_store,
    ):
        """Test that duplicate policies are removed from results."""
        # Setup mock response with duplicate policy_id
        mock_vector_store.similarity_search.return_value = [
            (
                "Policy overview",
                {'policy_id': 'policy1', 'policy_name': 'Health Plus', 'provider_id': 'ABC', 'policy_type': 'individual'},
                0.85,
            ),
            (
                "Policy exclusions",
                {'policy_id': 'policy1', 'policy_name': 'Health Plus', 'provider_id': 'ABC', 'policy_type': 'individual'},
                0.80,
            ),
            (
                "Different policy",
                {'policy_id': 'policy2', 'policy_name': 'Family Care', 'provider_id': 'XYZ', 'policy_type': 'family'},
                0.75,
            ),
        ]
        
        # Execute search
        results = await knowledge_base_service_with_vector_store.search_policies(
            query="health insurance",
            k=5,
        )
        
        # Verify deduplication - should only have 2 unique policies
        assert len(results) == 2
        assert results[0]['policy_id'] == 'policy1'
        assert results[1]['policy_id'] == 'policy2'
    
    @pytest.mark.asyncio
    async def test_search_policies_no_vector_store(self):
        """Test search when vector store is not configured."""
        service = KnowledgeBaseService(vector_store=None)
        
        results = await service.search_policies(
            query="health insurance",
            k=5,
        )
        
        # Should return empty list when vector store not configured
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_policies_empty_results(
        self,
        knowledge_base_service_with_vector_store,
        mock_vector_store,
    ):
        """Test search with no matching results."""
        mock_vector_store.similarity_search.return_value = []
        
        results = await knowledge_base_service_with_vector_store.search_policies(
            query="nonexistent policy",
            k=5,
        )
        
        assert results == []


class TestRetrievePolicyClause:
    """Test policy clause retrieval functionality."""
    
    @pytest.mark.asyncio
    async def test_retrieve_policy_clause_success(
        self,
        knowledge_base_service_with_vector_store,
        mock_vector_store,
    ):
        """Test successful retrieval of a policy clause."""
        mock_vector_store.similarity_search.return_value = [
            (
                "Exclusions: Cosmetic surgery, Dental treatment, Infertility treatment",
                {'policy_id': 'policy1', 'policy_name': 'Health Plus'},
                0.90,
            ),
        ]
        
        clause = await knowledge_base_service_with_vector_store.retrieve_policy_clause(
            policy_id='policy1',
            clause_type='exclusion',
        )
        
        assert clause is not None
        assert "Exclusions" in clause
        assert "Cosmetic surgery" in clause
        
        # Verify correct search parameters
        call_args = mock_vector_store.similarity_search.call_args
        assert 'exclusion' in call_args[1]['query']
        assert call_args[1]['filter'] == {'policy_id': 'policy1'}
        assert call_args[1]['k'] == 3
    
    @pytest.mark.asyncio
    async def test_retrieve_policy_clause_not_found(
        self,
        knowledge_base_service_with_vector_store,
        mock_vector_store,
    ):
        """Test retrieval when clause is not found."""
        mock_vector_store.similarity_search.return_value = []
        
        clause = await knowledge_base_service_with_vector_store.retrieve_policy_clause(
            policy_id='policy1',
            clause_type='coverage',
        )
        
        assert clause is None
    
    @pytest.mark.asyncio
    async def test_retrieve_policy_clause_no_vector_store(self):
        """Test clause retrieval when vector store is not configured."""
        service = KnowledgeBaseService(vector_store=None)
        
        clause = await service.retrieve_policy_clause(
            policy_id='policy1',
            clause_type='exclusion',
        )
        
        assert clause is None


class TestVectorStoreIntegration:
    """Test integration with vector store during document ingestion."""
    
    @pytest.mark.asyncio
    async def test_ingest_creates_multiple_chunks(
        self,
        sample_text_file,
        mock_vector_store,
    ):
        """Test that document ingestion creates multiple chunks."""
        service = KnowledgeBaseService(vector_store=mock_vector_store)
        
        await service.ingest_policy_document(
            file_path=sample_text_file,
            provider_id="ABC_INS",
            policy_name="Comprehensive Health Cover",
            policy_type="individual",
            version="1.0",
            effective_date=date(2024, 1, 1),
        )
        
        # Verify add_documents was called
        mock_vector_store.add_documents.assert_called_once()
        
        # Get the call arguments
        call_args = mock_vector_store.add_documents.call_args
        texts = call_args[1]['texts']
        metadatas = call_args[1]['metadatas']
        ids = call_args[1]['ids']
        
        # Verify multiple chunks were created
        assert len(texts) > 1
        
        # Verify metadata is consistent
        assert all(m['policy_name'] == 'Comprehensive Health Cover' for m in metadatas)
        assert all(m['provider_id'] == 'ABC_INS' for m in metadatas)
        
        # Verify IDs are unique
        assert len(ids) == len(set(ids))
    
    @pytest.mark.asyncio
    async def test_ingest_chunks_contain_relevant_info(
        self,
        sample_text_file,
        mock_vector_store,
    ):
        """Test that chunks contain relevant policy information."""
        service = KnowledgeBaseService(vector_store=mock_vector_store)
        
        await service.ingest_policy_document(
            file_path=sample_text_file,
            provider_id="ABC_INS",
            policy_name="Comprehensive Health Cover",
            policy_type="individual",
            version="1.0",
            effective_date=date(2024, 1, 1),
        )
        
        # Get the chunks
        call_args = mock_vector_store.add_documents.call_args
        texts = call_args[1]['texts']
        
        # Combine all chunks to verify content
        all_text = " ".join(texts).lower()
        
        # Verify key information is present
        assert "comprehensive health cover" in all_text
        assert "coverage" in all_text or "insured" in all_text
        assert "premium" in all_text
        assert "exclusion" in all_text or "not covered" in all_text
        assert "inclusion" in all_text or "covered" in all_text
    
    @pytest.mark.asyncio
    async def test_ingest_metadata_includes_key_fields(
        self,
        sample_text_file,
        mock_vector_store,
    ):
        """Test that metadata includes all key fields for filtering."""
        service = KnowledgeBaseService(vector_store=mock_vector_store)
        
        await service.ingest_policy_document(
            file_path=sample_text_file,
            provider_id="ABC_INS",
            policy_name="Comprehensive Health Cover",
            policy_type="individual",
            version="1.0",
            effective_date=date(2024, 1, 1),
        )
        
        # Get the metadata
        call_args = mock_vector_store.add_documents.call_args
        metadatas = call_args[1]['metadatas']
        
        # Verify all metadata entries have required fields
        for metadata in metadatas:
            assert 'policy_id' in metadata
            assert 'policy_name' in metadata
            assert 'provider_id' in metadata
            assert 'policy_type' in metadata
            assert 'coverage_amount' in metadata
            assert 'premium' in metadata
            assert 'version' in metadata


class TestChunkCreation:
    """Test chunk creation helper methods."""
    
    def test_create_chunks_from_list_single_chunk(
        self,
        knowledge_base_service_with_vector_store,
    ):
        """Test creating chunks from a small list."""
        items = ["Item 1", "Item 2", "Item 3"]
        chunks = knowledge_base_service_with_vector_store._create_chunks_from_list(
            items=items,
            prefix="Test Items",
            max_items_per_chunk=10,
        )
        
        assert len(chunks) == 1
        assert "Test Items" in chunks[0]
        assert "Item 1" in chunks[0]
        assert "Item 2" in chunks[0]
        assert "Item 3" in chunks[0]
    
    def test_create_chunks_from_list_multiple_chunks(
        self,
        knowledge_base_service_with_vector_store,
    ):
        """Test creating multiple chunks from a large list."""
        items = [f"Item {i}" for i in range(25)]
        chunks = knowledge_base_service_with_vector_store._create_chunks_from_list(
            items=items,
            prefix="Test Items",
            max_items_per_chunk=10,
        )
        
        # Should create 3 chunks (10 + 10 + 5)
        assert len(chunks) == 3
        
        # Verify all chunks have the prefix
        assert all("Test Items" in chunk for chunk in chunks)
        
        # Verify items are distributed correctly
        assert "Item 0" in chunks[0]
        assert "Item 9" in chunks[0]
        assert "Item 10" in chunks[1]
        assert "Item 19" in chunks[1]
        assert "Item 20" in chunks[2]
        assert "Item 24" in chunks[2]
    
    def test_create_chunks_from_empty_list(
        self,
        knowledge_base_service_with_vector_store,
    ):
        """Test creating chunks from an empty list."""
        chunks = knowledge_base_service_with_vector_store._create_chunks_from_list(
            items=[],
            prefix="Test Items",
            max_items_per_chunk=10,
        )
        
        assert len(chunks) == 0


class TestErrorHandling:
    """Test error handling in semantic search."""
    
    @pytest.mark.asyncio
    async def test_search_policies_vector_store_error(
        self,
        knowledge_base_service_with_vector_store,
        mock_vector_store,
    ):
        """Test handling of vector store errors during search."""
        mock_vector_store.similarity_search.side_effect = Exception("Vector store error")
        
        with pytest.raises(Exception, match="Vector store error"):
            await knowledge_base_service_with_vector_store.search_policies(
                query="health insurance",
                k=5,
            )
    
    @pytest.mark.asyncio
    async def test_retrieve_clause_vector_store_error(
        self,
        knowledge_base_service_with_vector_store,
        mock_vector_store,
    ):
        """Test handling of vector store errors during clause retrieval."""
        mock_vector_store.similarity_search.side_effect = Exception("Vector store error")
        
        with pytest.raises(Exception, match="Vector store error"):
            await knowledge_base_service_with_vector_store.retrieve_policy_clause(
                policy_id='policy1',
                clause_type='exclusion',
            )
