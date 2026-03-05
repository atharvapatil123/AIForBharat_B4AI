"""Simple integration test for vector store without full app dependencies."""

import pytest
from unittest.mock import AsyncMock, MagicMock


def test_vector_store_interface():
    """Test that VectorStore has the required interface."""
    # Import locally to avoid module-level chromadb import issues
    try:
        from healthcare_insurance_platform.db.vector_store import VectorStore
        
        # Create instance
        store = VectorStore()
        
        # Verify required methods exist
        assert hasattr(store, 'initialize')
        assert hasattr(store, 'add_documents')
        assert hasattr(store, 'similarity_search')
        assert hasattr(store, 'delete_documents')
        assert hasattr(store, 'close')
        
        # Verify attributes
        assert hasattr(store, 'settings')
        assert hasattr(store, 'embedding_function')
        
        print("✓ VectorStore interface is correct")
        
    except ImportError as e:
        pytest.skip(f"ChromaDB not compatible with current Python version: {e}")


def test_knowledge_base_search_methods():
    """Test that KnowledgeBase has semantic search methods."""
    from healthcare_insurance_platform.services.knowledge_base import KnowledgeBaseService
    
    # Create instance
    service = KnowledgeBaseService()
    
    # Verify semantic search methods exist
    assert hasattr(service, 'search_policies')
    assert hasattr(service, 'retrieve_policy_clause')
    assert hasattr(service, '_create_chunks_from_list')
    
    # Verify method signatures
    import inspect
    
    search_sig = inspect.signature(service.search_policies)
    assert 'query' in search_sig.parameters
    assert 'filters' in search_sig.parameters
    assert 'k' in search_sig.parameters
    
    retrieve_sig = inspect.signature(service.retrieve_policy_clause)
    assert 'policy_id' in retrieve_sig.parameters
    assert 'clause_type' in retrieve_sig.parameters
    
    print("✓ KnowledgeBase semantic search methods are correct")


@pytest.mark.asyncio
async def test_search_policies_without_vector_store():
    """Test search_policies returns empty list when vector store not configured."""
    from healthcare_insurance_platform.services.knowledge_base import KnowledgeBaseService
    
    service = KnowledgeBaseService(vector_store=None)
    
    results = await service.search_policies(
        query="test query",
        k=5,
    )
    
    assert results == []
    print("✓ search_policies handles missing vector store correctly")


@pytest.mark.asyncio
async def test_retrieve_clause_without_vector_store():
    """Test retrieve_policy_clause returns None when vector store not configured."""
    from healthcare_insurance_platform.services.knowledge_base import KnowledgeBaseService
    
    service = KnowledgeBaseService(vector_store=None)
    
    result = await service.retrieve_policy_clause(
        policy_id="test_policy",
        clause_type="exclusion",
    )
    
    assert result is None
    print("✓ retrieve_policy_clause handles missing vector store correctly")


def test_create_chunks_from_list():
    """Test chunk creation helper method."""
    from healthcare_insurance_platform.services.knowledge_base import KnowledgeBaseService
    
    service = KnowledgeBaseService()
    
    # Test with small list (single chunk)
    items = ["Item 1", "Item 2", "Item 3"]
    chunks = service._create_chunks_from_list(
        items=items,
        prefix="Test Items",
        max_items_per_chunk=10,
    )
    
    assert len(chunks) == 1
    assert "Test Items" in chunks[0]
    assert "Item 1" in chunks[0]
    
    # Test with large list (multiple chunks)
    items = [f"Item {i}" for i in range(25)]
    chunks = service._create_chunks_from_list(
        items=items,
        prefix="Test Items",
        max_items_per_chunk=10,
    )
    
    assert len(chunks) == 3  # 10 + 10 + 5
    assert all("Test Items" in chunk for chunk in chunks)
    
    # Test with empty list
    chunks = service._create_chunks_from_list(
        items=[],
        prefix="Test Items",
        max_items_per_chunk=10,
    )
    
    assert len(chunks) == 0
    
    print("✓ _create_chunks_from_list works correctly")


if __name__ == "__main__":
    # Run tests directly
    test_vector_store_interface()
    test_knowledge_base_search_methods()
    
    import asyncio
    asyncio.run(test_search_policies_without_vector_store())
    asyncio.run(test_retrieve_clause_without_vector_store())
    
    test_create_chunks_from_list()
    
    print("\n✅ All simple integration tests passed!")
