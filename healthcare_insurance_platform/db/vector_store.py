"""Vector database configuration for policy document storage and retrieval."""

from typing import List, Optional

import chromadb
from chromadb.utils import embedding_functions

from healthcare_insurance_platform.core.config import get_settings
from healthcare_insurance_platform.core.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Vector store for policy documents using ChromaDB."""

    def __init__(self):
        """Initialize vector store with embeddings."""
        self.settings = get_settings()
        # Use ChromaDB's built-in embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self._client: Optional[chromadb.Client] = None
        self._collection: Optional[chromadb.Collection] = None

    def initialize(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            # Create ChromaDB client with persistent storage
            self._client = chromadb.PersistentClient(
                path=self.settings.chroma_persist_directory,
            )

            # Create or get collection
            self._collection = self._client.get_or_create_collection(
                name=self.settings.chroma_collection_name,
                embedding_function=self.embedding_function,
            )

            logger.info(
                "Vector store initialized",
                collection=self.settings.chroma_collection_name,
            )
        except Exception as e:
            logger.error("Failed to initialize vector store", error=str(e))
            raise

    async def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add documents to the vector store.
        
        Args:
            texts: List of text chunks to add
            metadatas: Optional metadata for each text chunk
            ids: Optional IDs for each text chunk
            
        Returns:
            List of document IDs
            
        Raises:
            RuntimeError: If vector store not initialized
        """
        if not self._collection:
            raise RuntimeError("Vector store not initialized")

        try:
            # Generate IDs if not provided
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in texts]
            
            # Add documents to collection
            self._collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids,
            )
            
            logger.info("Documents added to vector store", count=len(texts))
            return ids
        except Exception as e:
            logger.error("Failed to add documents", error=str(e))
            raise

    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[dict] = None,
    ) -> List[tuple[str, dict, float]]:
        """Search for similar documents using semantic search.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of tuples (content, metadata, score) for matching documents
            
        Raises:
            RuntimeError: If vector store not initialized
        """
        if not self._collection:
            raise RuntimeError("Vector store not initialized")

        try:
            # Query the collection
            results = self._collection.query(
                query_texts=[query],
                n_results=k,
                where=filter,
            )
            
            # Format results as list of tuples
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    content = results['documents'][0][i]
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    # ChromaDB returns distances, convert to similarity score
                    distance = results['distances'][0][i] if results['distances'] else 0.0
                    formatted_results.append((content, metadata, distance))
            
            logger.debug("Similarity search completed", query=query, results=len(formatted_results))
            return formatted_results
        except Exception as e:
            logger.error("Similarity search failed", error=str(e))
            raise

    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents from the vector store.
        
        Args:
            ids: List of document IDs to delete
            
        Raises:
            RuntimeError: If vector store not initialized
        """
        if not self._collection:
            raise RuntimeError("Vector store not initialized")

        try:
            self._collection.delete(ids=ids)
            logger.info("Documents deleted from vector store", count=len(ids))
        except Exception as e:
            logger.error("Failed to delete documents", error=str(e))
            raise

    def close(self) -> None:
        """Close vector store connections."""
        if self._client:
            # ChromaDB client doesn't have explicit close method
            self._client = None
            self._collection = None
            logger.info("Vector store connections closed")


# Global vector store instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        _vector_store.initialize()
    return _vector_store


def close_vector_store() -> None:
    """Close global vector store instance."""
    global _vector_store
    if _vector_store:
        _vector_store.close()
        _vector_store = None
