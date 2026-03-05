"""LLM Orchestration Engine for managing prompts, context, and responses."""

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from healthcare_insurance_platform.core.logging import get_logger
from healthcare_insurance_platform.services.base import BaseService
from healthcare_insurance_platform.services.llm_client import (
    LLMClient,
    LLMProvider,
    LLMResponse,
    PromptTemplate,
)


class ContextDocument(BaseModel):
    """Document retrieved from knowledge base for context."""
    
    document_id: str = Field(description="Unique document identifier")
    content: str = Field(description="Document content or excerpt")
    relevance_score: float = Field(
        description="Relevance score (0-1)",
        ge=0.0,
        le=1.0,
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (source, page, etc.)"
    )


class ContextBundle(BaseModel):
    """Bundle of context documents for LLM prompt."""
    
    documents: List[ContextDocument] = Field(
        default_factory=list,
        description="Retrieved documents"
    )
    total_tokens: int = Field(
        default=0,
        description="Estimated total tokens in context"
    )
    query: str = Field(description="Original query")
    
    def get_context_text(self, max_tokens: Optional[int] = None) -> str:
        """Get formatted context text for prompt.
        
        Args:
            max_tokens: Maximum tokens to include (truncates if needed)
            
        Returns:
            Formatted context string
        """
        if not self.documents:
            return ""
        
        context_parts = []
        current_tokens = 0
        
        # Sort by relevance score (highest first)
        sorted_docs = sorted(
            self.documents,
            key=lambda d: d.relevance_score,
            reverse=True,
        )
        
        for doc in sorted_docs:
            doc_text = f"[Document {doc.document_id}]\n{doc.content}\n"
            doc_tokens = len(doc_text) // 4  # Rough estimate
            
            if max_tokens and (current_tokens + doc_tokens) > max_tokens:
                break
            
            context_parts.append(doc_text)
            current_tokens += doc_tokens
        
        return "\n".join(context_parts)


class Citation(BaseModel):
    """Citation linking response to source document."""
    
    document_id: str = Field(description="Source document ID")
    excerpt: str = Field(description="Relevant excerpt from document")
    relevance: str = Field(description="Why this source is relevant")


class EnhancedLLMResponse(BaseModel):
    """LLM response with citations and explanations."""
    
    content: str = Field(description="Generated response text")
    explanation: Optional[str] = Field(
        default=None,
        description="Explanation of reasoning"
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="Source citations"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        description="Confidence level (0-1)"
    )
    model: str = Field(description="Model used")
    provider: str = Field(description="Provider used")
    tokens_used: Optional[int] = Field(
        default=None,
        description="Tokens consumed"
    )


class LLMEngine(BaseService):
    """LLM Orchestration Engine.
    
    Manages:
    - Prompt template registration and management
    - Context assembly from knowledge base
    - LLM response generation with retry logic
    - Citation tracking and explanation generation
    - Multi-step reasoning workflows
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        db=None,
        vector_store=None,
    ):
        """Initialize LLM engine.
        
        Args:
            llm_client: LLM client instance (creates default if None)
            db: Database session
            vector_store: Vector store for document retrieval
        """
        super().__init__(db=db, vector_store=vector_store)
        self.llm_client = llm_client or LLMClient()
        self._register_default_templates()
    
    def _register_default_templates(self) -> None:
        """Register default prompt templates."""
        
        # Policy comparison template
        policy_comparison_template = PromptTemplate(
            name="policy_comparison",
            system_message=(
                "You are an expert insurance advisor helping users compare health insurance policies. "
                "Provide clear, unbiased comparisons focusing on coverage, costs, and suitability. "
                "Always cite specific policy clauses to support your analysis."
            ),
            user_template=(
                "Compare the following insurance policies for a user with this profile:\n\n"
                "User Profile:\n{user_profile}\n\n"
                "Policies to Compare:\n{policies}\n\n"
                "Provide a detailed comparison highlighting key differences, pros and cons for each policy, "
                "and recommendations based on the user's profile. Include specific policy clause citations."
            ),
            variables=["user_profile", "policies"],
        )
        
        # Claim prediction template
        claim_prediction_template = PromptTemplate(
            name="claim_prediction",
            system_message=(
                "You are an expert insurance claims analyst. Analyze claim scenarios against policy terms "
                "and provide accurate acceptance probability predictions with detailed reasoning. "
                "Always cite specific policy clauses."
            ),
            user_template=(
                "Analyze this insurance claim:\n\n"
                "Claim Details:\n{claim_details}\n\n"
                "Policy Terms:\n{policy_terms}\n\n"
                "Provide:\n"
                "1. Acceptance probability (0-1)\n"
                "2. Supporting factors with policy clause citations\n"
                "3. Contradicting factors with policy clause citations\n"
                "4. Overall reasoning and recommendation"
            ),
            variables=["claim_details", "policy_terms"],
        )
        
        # Policy explanation template
        policy_explanation_template = PromptTemplate(
            name="policy_explanation",
            system_message=(
                "You are an expert at explaining complex insurance policies in simple, clear language. "
                "Break down technical jargon and legal terms into everyday language that anyone can understand. "
                "Highlight important clauses, especially exclusions and limitations."
            ),
            user_template=(
                "Explain this insurance policy in simple terms:\n\n"
                "{policy_content}\n\n"
                "Focus on:\n"
                "1. What is covered (inclusions)\n"
                "2. What is NOT covered (exclusions)\n"
                "3. Waiting periods and limitations\n"
                "4. Hidden clauses or important fine print\n"
                "5. Key terms explained in simple language"
            ),
            variables=["policy_content"],
        )
        
        # Medical summary template
        medical_summary_template = PromptTemplate(
            name="medical_summary",
            system_message=(
                "You are a medical professional creating concise summaries of patient medical history. "
                "Focus on clinically relevant information, highlight abnormalities, and organize chronologically. "
                "Use medical terminology appropriately but ensure clarity."
            ),
            user_template=(
                "Summarize this patient's medical history:\n\n"
                "{medical_records}\n\n"
                "Provide:\n"
                "1. Chronological timeline of key events\n"
                "2. Current active conditions\n"
                "3. Current medications and allergies\n"
                "4. Abnormal test results and trends\n"
                "5. Risk factors and clinical considerations"
            ),
            variables=["medical_records"],
        )
        
        # Register all templates
        for template in [
            policy_comparison_template,
            claim_prediction_template,
            policy_explanation_template,
            medical_summary_template,
        ]:
            self.llm_client.register_template(template)
        
        self.logger.info("Default prompt templates registered")
    
    def register_template(self, template: PromptTemplate) -> None:
        """Register a custom prompt template.
        
        Args:
            template: Template to register
        """
        self.llm_client.register_template(template)
        self.logger.info(f"Custom template registered: {template.name}")
    
    async def assemble_context(
        self,
        query: str,
        max_documents: int = 5,
        min_relevance: float = 0.5,
    ) -> ContextBundle:
        """Assemble context from knowledge base for a query.
        
        Args:
            query: Search query
            max_documents: Maximum documents to retrieve
            min_relevance: Minimum relevance score threshold
            
        Returns:
            Context bundle with relevant documents
        """
        if not self.vector_store:
            self.logger.warning("No vector store available for context assembly")
            return ContextBundle(documents=[], query=query)
        
        try:
            # Search vector store for relevant documents
            results = await self.vector_store.search(
                query=query,
                limit=max_documents,
            )
            
            # Convert to context documents
            documents = []
            total_tokens = 0
            
            for result in results:
                # Filter by relevance threshold
                if result.get('score', 0) < min_relevance:
                    continue
                
                content = result.get('content', '')
                doc = ContextDocument(
                    document_id=result.get('id', 'unknown'),
                    content=content,
                    relevance_score=result.get('score', 0.0),
                    metadata=result.get('metadata', {}),
                )
                
                documents.append(doc)
                total_tokens += len(content) // 4  # Rough estimate
            
            self.logger.info(
                "Context assembled",
                query=query,
                documents_found=len(documents),
                total_tokens=total_tokens,
            )
            
            return ContextBundle(
                documents=documents,
                total_tokens=total_tokens,
                query=query,
            )
        
        except Exception as e:
            self.logger.error(
                "Failed to assemble context",
                query=query,
                error=str(e),
            )
            # Return empty context rather than failing
            return ContextBundle(documents=[], query=query)
    
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        context: Optional[ContextBundle] = None,
        include_explanation: bool = True,
        **kwargs,
    ) -> EnhancedLLMResponse:
        """Generate LLM response with context and citations.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            context: Optional context bundle to include
            include_explanation: Whether to request explanation
            **kwargs: Additional LLM parameters
            
        Returns:
            Enhanced response with citations
        """
        # Augment prompt with context if provided
        if context and context.documents:
            context_text = context.get_context_text(max_tokens=4000)
            augmented_prompt = (
                f"Context Information:\n{context_text}\n\n"
                f"User Query:\n{prompt}\n\n"
                "Please provide a response based on the context above. "
                "Cite specific documents using [Document ID] format."
            )
        else:
            augmented_prompt = prompt
        
        # Add explanation request if needed
        if include_explanation:
            augmented_prompt += (
                "\n\nPlease also explain your reasoning and cite sources."
            )
        
        # Generate response
        llm_response = await self.llm_client.generate(
            prompt=augmented_prompt,
            system_message=system_message,
            **kwargs,
        )
        
        # Extract citations from response
        citations = self._extract_citations(
            llm_response.content,
            context.documents if context else [],
        )
        
        return EnhancedLLMResponse(
            content=llm_response.content,
            explanation=None,  # Could parse from response if structured
            citations=citations,
            confidence_score=llm_response.confidence_score,
            model=llm_response.model,
            provider=llm_response.provider,
            tokens_used=llm_response.tokens_used,
        )
    
    async def generate_from_template(
        self,
        template_name: str,
        context: Optional[ContextBundle] = None,
        **variables,
    ) -> EnhancedLLMResponse:
        """Generate response using a registered template.
        
        Args:
            template_name: Name of template to use
            context: Optional context bundle
            **variables: Template variables
            
        Returns:
            Enhanced response with citations
        """
        # Get template
        template = self.llm_client.get_template(template_name)
        
        # Format template
        system_message, user_message = template.format(**variables)
        
        # Generate response
        return await self.generate_response(
            prompt=user_message,
            system_message=system_message,
            context=context,
        )
    
    def _extract_citations(
        self,
        response_text: str,
        context_documents: List[ContextDocument],
    ) -> List[Citation]:
        """Extract citations from response text.
        
        Args:
            response_text: Generated response
            context_documents: Context documents that were provided
            
        Returns:
            List of citations found
        """
        citations = []
        
        # Simple citation extraction: look for [Document ID] patterns
        import re
        pattern = r'\[Document ([^\]]+)\]'
        matches = re.findall(pattern, response_text)
        
        # Create citations for referenced documents
        for doc_id in set(matches):
            # Find the document in context
            doc = next(
                (d for d in context_documents if d.document_id == doc_id),
                None,
            )
            
            if doc:
                citations.append(
                    Citation(
                        document_id=doc_id,
                        excerpt=doc.content[:200] + "...",  # First 200 chars
                        relevance="Referenced in response",
                    )
                )
        
        return citations
    
    async def generate_with_retry_fallback(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        fallback_response: Optional[str] = None,
        **kwargs,
    ) -> EnhancedLLMResponse:
        """Generate response with fallback on failure.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            fallback_response: Fallback text if generation fails
            **kwargs: Additional LLM parameters
            
        Returns:
            Enhanced response (generated or fallback)
        """
        try:
            return await self.generate_response(
                prompt=prompt,
                system_message=system_message,
                **kwargs,
            )
        except Exception as e:
            self.logger.error(
                "LLM generation failed, using fallback",
                error=str(e),
            )
            
            if fallback_response:
                return EnhancedLLMResponse(
                    content=fallback_response,
                    explanation="Fallback response due to generation error",
                    citations=[],
                    confidence_score=0.0,
                    model="fallback",
                    provider="fallback",
                )
            else:
                raise
