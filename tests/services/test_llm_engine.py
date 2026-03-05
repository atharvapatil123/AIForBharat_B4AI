"""Unit tests for LLM orchestration engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from healthcare_insurance_platform.services.llm_engine import (
    Citation,
    ContextBundle,
    ContextDocument,
    EnhancedLLMResponse,
    LLMEngine,
)
from healthcare_insurance_platform.services.llm_client import (
    LLMResponse,
    PromptTemplate,
)


class TestContextDocument:
    """Tests for ContextDocument model."""
    
    def test_create_context_document(self):
        """Test creating a context document."""
        doc = ContextDocument(
            document_id="doc1",
            content="Test content",
            relevance_score=0.85,
            metadata={"source": "policy.pdf", "page": 1},
        )
        
        assert doc.document_id == "doc1"
        assert doc.content == "Test content"
        assert doc.relevance_score == 0.85
        assert doc.metadata["source"] == "policy.pdf"
    
    def test_relevance_score_validation(self):
        """Test relevance score must be between 0 and 1."""
        with pytest.raises(ValueError):
            ContextDocument(
                document_id="doc1",
                content="Content",
                relevance_score=1.5,  # Invalid
            )


class TestContextBundle:
    """Tests for ContextBundle."""
    
    def test_empty_context_bundle(self):
        """Test empty context bundle."""
        bundle = ContextBundle(documents=[], query="test query")
        
        assert len(bundle.documents) == 0
        assert bundle.query == "test query"
        assert bundle.get_context_text() == ""
    
    def test_get_context_text(self):
        """Test getting formatted context text."""
        docs = [
            ContextDocument(
                document_id="doc1",
                content="First document content",
                relevance_score=0.9,
            ),
            ContextDocument(
                document_id="doc2",
                content="Second document content",
                relevance_score=0.7,
            ),
        ]
        
        bundle = ContextBundle(documents=docs, query="test")
        context_text = bundle.get_context_text()
        
        assert "doc1" in context_text
        assert "doc2" in context_text
        assert "First document content" in context_text
    
    def test_get_context_text_sorted_by_relevance(self):
        """Test context text is sorted by relevance."""
        docs = [
            ContextDocument(
                document_id="doc1",
                content="Low relevance",
                relevance_score=0.5,
            ),
            ContextDocument(
                document_id="doc2",
                content="High relevance",
                relevance_score=0.9,
            ),
        ]
        
        bundle = ContextBundle(documents=docs, query="test")
        context_text = bundle.get_context_text()
        
        # High relevance should come first
        high_pos = context_text.find("High relevance")
        low_pos = context_text.find("Low relevance")
        assert high_pos < low_pos
    
    def test_get_context_text_with_token_limit(self):
        """Test context text respects token limit."""
        docs = [
            ContextDocument(
                document_id=f"doc{i}",
                content="x" * 1000,  # Large content
                relevance_score=0.9 - (i * 0.1),
            )
            for i in range(5)
        ]
        
        bundle = ContextBundle(documents=docs, query="test")
        context_text = bundle.get_context_text(max_tokens=500)
        
        # Should be truncated
        assert len(context_text) < sum(len(d.content) for d in docs)


class TestLLMEngine:
    """Tests for LLMEngine."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client."""
        client = MagicMock()
        client.register_template = MagicMock()
        client.get_template = MagicMock()
        return client
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store."""
        store = AsyncMock()
        return store
    
    def test_engine_initialization(self, mock_llm_client):
        """Test LLM engine initialization."""
        engine = LLMEngine(llm_client=mock_llm_client)
        
        assert engine.llm_client == mock_llm_client
        # Should register default templates
        assert mock_llm_client.register_template.called
    
    def test_register_custom_template(self, mock_llm_client):
        """Test registering custom template."""
        engine = LLMEngine(llm_client=mock_llm_client)
        
        template = PromptTemplate(
            name="custom",
            system_message="System",
            user_template="User {var}",
            variables=["var"],
        )
        
        engine.register_template(template)
        mock_llm_client.register_template.assert_called_with(template)
    
    @pytest.mark.asyncio
    async def test_assemble_context_no_vector_store(self, mock_llm_client):
        """Test context assembly without vector store."""
        engine = LLMEngine(llm_client=mock_llm_client, vector_store=None)
        
        bundle = await engine.assemble_context("test query")
        
        assert len(bundle.documents) == 0
        assert bundle.query == "test query"
    
    @pytest.mark.asyncio
    async def test_assemble_context_with_results(self, mock_llm_client, mock_vector_store):
        """Test context assembly with search results."""
        # Mock search results
        mock_vector_store.search = AsyncMock(return_value=[
            {
                'id': 'doc1',
                'content': 'Document 1 content',
                'score': 0.9,
                'metadata': {'source': 'policy1.pdf'},
            },
            {
                'id': 'doc2',
                'content': 'Document 2 content',
                'score': 0.7,
                'metadata': {'source': 'policy2.pdf'},
            },
        ])
        
        engine = LLMEngine(
            llm_client=mock_llm_client,
            vector_store=mock_vector_store,
        )
        
        bundle = await engine.assemble_context("test query", max_documents=5)
        
        assert len(bundle.documents) == 2
        assert bundle.documents[0].document_id == 'doc1'
        assert bundle.documents[0].relevance_score == 0.9
        mock_vector_store.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assemble_context_filters_low_relevance(
        self,
        mock_llm_client,
        mock_vector_store,
    ):
        """Test context assembly filters low relevance results."""
        mock_vector_store.search = AsyncMock(return_value=[
            {'id': 'doc1', 'content': 'High relevance', 'score': 0.9},
            {'id': 'doc2', 'content': 'Low relevance', 'score': 0.3},
        ])
        
        engine = LLMEngine(
            llm_client=mock_llm_client,
            vector_store=mock_vector_store,
        )
        
        bundle = await engine.assemble_context(
            "test query",
            min_relevance=0.5,
        )
        
        # Only high relevance document should be included
        assert len(bundle.documents) == 1
        assert bundle.documents[0].document_id == 'doc1'
    
    @pytest.mark.asyncio
    async def test_generate_response_without_context(self, mock_llm_client):
        """Test generating response without context."""
        mock_llm_client.generate = AsyncMock(return_value=LLMResponse(
            content="Generated response",
            model="gpt-4",
            provider="openai",
        ))
        
        engine = LLMEngine(llm_client=mock_llm_client)
        
        response = await engine.generate_response("Test prompt")
        
        assert isinstance(response, EnhancedLLMResponse)
        assert response.content == "Generated response"
        assert response.model == "gpt-4"
        mock_llm_client.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_with_context(self, mock_llm_client):
        """Test generating response with context."""
        mock_llm_client.generate = AsyncMock(return_value=LLMResponse(
            content="Response with context [Document doc1]",
            model="gpt-4",
            provider="openai",
        ))
        
        engine = LLMEngine(llm_client=mock_llm_client)
        
        context = ContextBundle(
            documents=[
                ContextDocument(
                    document_id="doc1",
                    content="Context content",
                    relevance_score=0.9,
                ),
            ],
            query="test",
        )
        
        response = await engine.generate_response(
            "Test prompt",
            context=context,
        )
        
        assert "Response with context" in response.content
        # Should extract citation
        assert len(response.citations) > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_with_system_message(self, mock_llm_client):
        """Test generating response with system message."""
        mock_llm_client.generate = AsyncMock(return_value=LLMResponse(
            content="Response",
            model="gpt-4",
            provider="openai",
        ))
        
        engine = LLMEngine(llm_client=mock_llm_client)
        
        await engine.generate_response(
            "User prompt",
            system_message="System instructions",
        )
        
        # Verify system message was passed
        call_kwargs = mock_llm_client.generate.call_args[1]
        assert call_kwargs['system_message'] == "System instructions"
    
    @pytest.mark.asyncio
    async def test_generate_from_template(self, mock_llm_client):
        """Test generating from template."""
        template = PromptTemplate(
            name="test_template",
            system_message="System",
            user_template="Hello {name}",
            variables=["name"],
        )
        
        mock_llm_client.get_template = MagicMock(return_value=template)
        mock_llm_client.generate = AsyncMock(return_value=LLMResponse(
            content="Template response",
            model="gpt-4",
            provider="openai",
        ))
        
        engine = LLMEngine(llm_client=mock_llm_client)
        
        response = await engine.generate_from_template(
            "test_template",
            name="Alice",
        )
        
        assert response.content == "Template response"
        mock_llm_client.get_template.assert_called_with("test_template")
    
    def test_extract_citations(self, mock_llm_client):
        """Test citation extraction from response."""
        engine = LLMEngine(llm_client=mock_llm_client)
        
        response_text = (
            "According to [Document doc1], the policy covers X. "
            "Also, [Document doc2] states that Y is excluded."
        )
        
        context_docs = [
            ContextDocument(
                document_id="doc1",
                content="Policy content about X",
                relevance_score=0.9,
            ),
            ContextDocument(
                document_id="doc2",
                content="Policy content about Y",
                relevance_score=0.8,
            ),
        ]
        
        citations = engine._extract_citations(response_text, context_docs)
        
        assert len(citations) == 2
        assert any(c.document_id == "doc1" for c in citations)
        assert any(c.document_id == "doc2" for c in citations)
    
    def test_extract_citations_no_matches(self, mock_llm_client):
        """Test citation extraction with no matches."""
        engine = LLMEngine(llm_client=mock_llm_client)
        
        response_text = "Response without citations"
        context_docs = []
        
        citations = engine._extract_citations(response_text, context_docs)
        
        assert len(citations) == 0
    
    @pytest.mark.asyncio
    async def test_generate_with_retry_fallback_success(self, mock_llm_client):
        """Test fallback generation on success."""
        mock_llm_client.generate = AsyncMock(return_value=LLMResponse(
            content="Success response",
            model="gpt-4",
            provider="openai",
        ))
        
        engine = LLMEngine(llm_client=mock_llm_client)
        
        response = await engine.generate_with_retry_fallback(
            "Test prompt",
            fallback_response="Fallback text",
        )
        
        assert response.content == "Success response"
        assert response.model == "gpt-4"
    
    @pytest.mark.asyncio
    async def test_generate_with_retry_fallback_failure(self, mock_llm_client):
        """Test fallback generation on failure."""
        mock_llm_client.generate = AsyncMock(side_effect=Exception("API Error"))
        
        engine = LLMEngine(llm_client=mock_llm_client)
        
        response = await engine.generate_with_retry_fallback(
            "Test prompt",
            fallback_response="Fallback text",
        )
        
        assert response.content == "Fallback text"
        assert response.model == "fallback"
        assert response.confidence_score == 0.0
    
    @pytest.mark.asyncio
    async def test_generate_with_retry_fallback_no_fallback(self, mock_llm_client):
        """Test fallback generation without fallback text."""
        mock_llm_client.generate = AsyncMock(side_effect=Exception("API Error"))
        
        engine = LLMEngine(llm_client=mock_llm_client)
        
        with pytest.raises(Exception, match="API Error"):
            await engine.generate_with_retry_fallback("Test prompt")
    
    @pytest.mark.asyncio
    async def test_assemble_context_error_handling(
        self,
        mock_llm_client,
        mock_vector_store,
    ):
        """Test context assembly handles errors gracefully."""
        mock_vector_store.search = AsyncMock(side_effect=Exception("Search failed"))
        
        engine = LLMEngine(
            llm_client=mock_llm_client,
            vector_store=mock_vector_store,
        )
        
        # Should return empty context instead of raising
        bundle = await engine.assemble_context("test query")
        
        assert len(bundle.documents) == 0
        assert bundle.query == "test query"
