"""Knowledge Base service for policy document management."""

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from healthcare_insurance_platform.core.errors import ValidationError
from healthcare_insurance_platform.core.logging import get_logger
from healthcare_insurance_platform.models.policy import (
    DocumentRequirement,
    ParsedClause,
    PolicyDocument,
    WaitingPeriod,
)
from healthcare_insurance_platform.services.base import BaseService
from healthcare_insurance_platform.utils.document_parser import (
    PolicyInformationExtractor,
    get_parser,
)

logger = get_logger(__name__)


class DocumentValidationError(ValidationError):
    """Raised when document validation fails."""
    pass


class KnowledgeBaseService(BaseService):
    """
    Service for managing policy documents in the knowledge base.
    
    Handles document ingestion, parsing, validation, storage, and versioning.
    Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5
    """
    
    def __init__(self, db_session: Optional[AsyncSession] = None, *args, **kwargs):
        """Initialize Knowledge Base service."""
        super().__init__(*args, **kwargs)
        self.extractor = PolicyInformationExtractor()
        self.db_session = db_session
        self._version_service = None
    
    async def ingest_policy_document(
        self,
        file_path: Path,
        provider_id: str,
        policy_name: str,
        policy_type: str,
        version: str,
        effective_date: date,
        metadata: Optional[Dict] = None,
        previous_policy: Optional[PolicyDocument] = None,
        created_by: Optional[str] = None,
    ) -> PolicyDocument:
        """
        Ingest a policy document into the knowledge base.
        
        This method:
        1. Parses the document (PDF or text)
        2. Extracts key policy information
        3. Validates the document has required fields
        4. Creates a PolicyDocument instance
        5. Stores it in the knowledge base
        6. Creates version history entry
        
        Args:
            file_path: Path to the policy document file
            provider_id: Insurance company identifier
            policy_name: Name of the policy
            policy_type: Type of policy (individual, family, senior_citizen)
            version: Policy version
            effective_date: Policy effective date
            metadata: Optional additional metadata
            previous_policy: Previous version of the policy (for version tracking)
            created_by: User who created this version
            
        Returns:
            PolicyDocument instance
            
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file format is not supported
            DocumentValidationError: If document validation fails
            
        Requirements: 12.1, 12.2, 12.3, 12.5
        """
        self._log_operation(
            "ingest_policy_document",
            file_path=str(file_path),
            provider_id=provider_id,
            policy_name=policy_name,
        )
        
        try:
            # Step 1: Parse the document
            full_text = await self._parse_document(file_path)
            
            # Step 2: Extract key policy information
            extracted_info = await self._extract_policy_information(full_text)
            
            # Step 3: Validate extracted information
            self._validate_extracted_information(extracted_info, policy_name)
            
            # Step 4: Create PolicyDocument instance
            policy_document = self._create_policy_document(
                policy_id=str(uuid.uuid4()),
                provider_id=provider_id,
                policy_name=policy_name,
                policy_type=policy_type,
                version=version,
                effective_date=effective_date,
                full_text=full_text,
                extracted_info=extracted_info,
            )
            
            # Step 5: Store in knowledge base (vector store)
            if self.vector_store:
                await self._store_in_vector_db(policy_document)
            
            # Step 6: Create version history entry
            if self.db_session:
                version_service = await self._get_version_service()
                await version_service.create_version(
                    policy_document=policy_document,
                    previous_version=previous_policy,
                    created_by=created_by,
                )
            
            logger.info(
                f"Successfully ingested policy document: {policy_name}",
                policy_id=policy_document.policy_id,
            )
            
            return policy_document
            
        except Exception as e:
            self._log_error("ingest_policy_document", e, file_path=str(file_path))
            raise
    
    async def _parse_document(self, file_path: Path) -> str:
        """
        Parse document and extract text content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text content
            
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file format is not supported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")
        
        parser = get_parser(file_path)
        text_content = parser.parse(file_path)
        
        if not text_content or len(text_content.strip()) < 100:
            raise DocumentValidationError(
                "Document is too short or empty. "
                "Policy documents must contain substantial content."
            )
        
        return text_content
    
    async def _extract_policy_information(self, text: str) -> Dict:
        """
        Extract key policy information from document text.
        
        Args:
            text: Policy document text
            
        Returns:
            Dictionary containing extracted information
        """
        return {
            'coverage_amount': self.extractor.extract_coverage_amount(text),
            'premium': self.extractor.extract_premium(text),
            'waiting_periods': self.extractor.extract_waiting_periods(text),
            'exclusions': self.extractor.extract_exclusions(text),
            'inclusions': self.extractor.extract_inclusions(text),
        }
    
    def _validate_extracted_information(
        self,
        extracted_info: Dict,
        policy_name: str,
    ) -> None:
        """
        Validate that extracted information contains required fields.
        
        Args:
            extracted_info: Extracted policy information
            policy_name: Name of the policy (for error messages)
            
        Raises:
            DocumentValidationError: If required information is missing
            
        Requirements: 12.5
        """
        validation_errors = []
        
        # Check coverage amount
        if not extracted_info.get('coverage_amount'):
            validation_errors.append("Coverage amount not found in document")
        elif extracted_info['coverage_amount'] <= 0:
            validation_errors.append("Coverage amount must be positive")
        
        # Check premium
        if not extracted_info.get('premium'):
            validation_errors.append("Premium amount not found in document")
        elif extracted_info['premium'] <= 0:
            validation_errors.append("Premium amount must be positive")
        
        # Check exclusions
        if not extracted_info.get('exclusions'):
            validation_errors.append("No exclusions found in document")
        elif len(extracted_info['exclusions']) == 0:
            validation_errors.append("Exclusions list is empty")
        
        # Check inclusions
        if not extracted_info.get('inclusions'):
            validation_errors.append("No inclusions/coverage found in document")
        elif len(extracted_info['inclusions']) == 0:
            validation_errors.append("Inclusions list is empty")
        
        # Check waiting periods
        if not extracted_info.get('waiting_periods'):
            validation_errors.append("Waiting period information not found")
        
        if validation_errors:
            error_message = (
                f"Document validation failed for policy '{policy_name}'. "
                f"Missing required information:\n" +
                "\n".join(f"  - {error}" for error in validation_errors)
            )
            raise DocumentValidationError(error_message)
    
    def _create_policy_document(
        self,
        policy_id: str,
        provider_id: str,
        policy_name: str,
        policy_type: str,
        version: str,
        effective_date: date,
        full_text: str,
        extracted_info: Dict,
    ) -> PolicyDocument:
        """
        Create a PolicyDocument instance from extracted information.
        
        Args:
            policy_id: Unique policy identifier
            provider_id: Insurance company identifier
            policy_name: Name of the policy
            policy_type: Type of policy
            version: Policy version
            effective_date: Policy effective date
            full_text: Complete policy document text
            extracted_info: Extracted policy information
            
        Returns:
            PolicyDocument instance
            
        Requirements: 12.2
        """
        # Create waiting period object
        waiting_periods_data = extracted_info['waiting_periods']
        waiting_periods = WaitingPeriod(
            general=waiting_periods_data.get('general', 30),
            pre_existing=waiting_periods_data.get('pre_existing', 730),
            specific_conditions=[],
        )
        
        # Create document requirements (default structure)
        document_requirements = [
            DocumentRequirement(
                claim_type="hospitalization",
                documents=[
                    "Hospital discharge summary",
                    "Medical bills and receipts",
                    "Diagnostic reports",
                    "Doctor's prescription",
                ]
            ),
            DocumentRequirement(
                claim_type="surgery",
                documents=[
                    "Hospital discharge summary",
                    "Surgery reports",
                    "Medical bills and receipts",
                    "Anesthesia reports",
                    "Doctor's prescription",
                ]
            ),
        ]
        
        # Create parsed clauses (basic structure)
        parsed_clauses = [
            ParsedClause(
                clause_type="coverage",
                text=f"Coverage amount: {extracted_info['coverage_amount']}",
                importance="critical",
            ),
            ParsedClause(
                clause_type="premium",
                text=f"Premium: {extracted_info['premium']}",
                importance="critical",
            ),
            ParsedClause(
                clause_type="waiting_period",
                text=f"General waiting period: {waiting_periods.general} days, "
                     f"Pre-existing: {waiting_periods.pre_existing} days",
                importance="high",
            ),
        ]
        
        # Add exclusion clauses
        for exclusion in extracted_info['exclusions'][:5]:  # Top 5
            parsed_clauses.append(
                ParsedClause(
                    clause_type="exclusion",
                    text=exclusion,
                    importance="high",
                )
            )
        
        # Add inclusion clauses
        for inclusion in extracted_info['inclusions'][:5]:  # Top 5
            parsed_clauses.append(
                ParsedClause(
                    clause_type="inclusion",
                    text=inclusion,
                    importance="medium",
                )
            )
        
        # Create PolicyDocument
        policy_document = PolicyDocument(
            policy_id=policy_id,
            provider_id=provider_id,
            policy_name=policy_name,
            policy_type=policy_type,
            version=version,
            effective_date=effective_date,
            coverage_amount=extracted_info['coverage_amount'],
            premium=extracted_info['premium'],
            waiting_periods=waiting_periods,
            inclusions=extracted_info['inclusions'],
            exclusions=extracted_info['exclusions'],
            ped_policy="Pre-existing diseases covered after waiting period",
            claim_process="Submit claim with required documents within 30 days",
            document_requirements=document_requirements,
            full_text=full_text,
            parsed_clauses=parsed_clauses,
            last_updated=datetime.now(timezone.utc),
        )
        
        return policy_document
    
    async def _store_in_vector_db(self, policy_document: PolicyDocument) -> None:
        """
        Store policy document in vector database for semantic search.
        
        This method creates optimized chunks from the policy document and
        stores them with rich metadata for efficient retrieval.
        
        Args:
            policy_document: Policy document to store
        """
        if not self.vector_store:
            logger.warning("Vector store not configured, skipping vector storage")
            return
        
        # Create document chunks for vector storage with better organization
        chunks = []
        
        # Chunk 1: Policy overview
        chunks.append(
            f"Policy: {policy_document.policy_name}\n"
            f"Provider: {policy_document.provider_id}\n"
            f"Type: {policy_document.policy_type}\n"
            f"Coverage Amount: Rs. {policy_document.coverage_amount:,.0f}\n"
            f"Annual Premium: Rs. {policy_document.premium:,.0f}\n"
            f"Waiting Period (General): {policy_document.waiting_periods.general} days\n"
            f"Waiting Period (Pre-existing): {policy_document.waiting_periods.pre_existing} days"
        )
        
        # Chunk 2: Inclusions (what's covered)
        if policy_document.inclusions:
            inclusion_chunks = self._create_chunks_from_list(
                items=policy_document.inclusions,
                prefix=f"Coverage and Inclusions for {policy_document.policy_name}",
                max_items_per_chunk=10,
            )
            chunks.extend(inclusion_chunks)
        
        # Chunk 3: Exclusions (what's not covered)
        if policy_document.exclusions:
            exclusion_chunks = self._create_chunks_from_list(
                items=policy_document.exclusions,
                prefix=f"Exclusions and Limitations for {policy_document.policy_name}",
                max_items_per_chunk=10,
            )
            chunks.extend(exclusion_chunks)
        
        # Chunk 4: Parsed clauses by type
        if policy_document.parsed_clauses:
            clause_groups = {}
            for clause in policy_document.parsed_clauses:
                if clause.clause_type not in clause_groups:
                    clause_groups[clause.clause_type] = []
                clause_groups[clause.clause_type].append(clause.text)
            
            for clause_type, texts in clause_groups.items():
                chunk_text = (
                    f"{clause_type.replace('_', ' ').title()} clauses for "
                    f"{policy_document.policy_name}:\n" +
                    "\n".join(f"- {text}" for text in texts)
                )
                chunks.append(chunk_text)
        
        # Chunk 5: PED policy
        if policy_document.ped_policy:
            chunks.append(
                f"Pre-existing Disease Policy for {policy_document.policy_name}:\n"
                f"{policy_document.ped_policy}"
            )
        
        # Chunk 6: Claim process
        if policy_document.claim_process:
            chunks.append(
                f"Claim Process for {policy_document.policy_name}:\n"
                f"{policy_document.claim_process}"
            )
        
        # Store chunks in vector database with rich metadata
        metadata = {
            'policy_id': policy_document.policy_id,
            'policy_name': policy_document.policy_name,
            'provider_id': policy_document.provider_id,
            'policy_type': policy_document.policy_type,
            'coverage_amount': policy_document.coverage_amount,
            'premium': policy_document.premium,
            'version': policy_document.version,
        }
        
        await self.vector_store.add_documents(
            texts=chunks,
            metadatas=[metadata] * len(chunks),
            ids=[f"{policy_document.policy_id}_{i}" for i in range(len(chunks))],
        )
        
        logger.info(
            f"Stored policy document in vector database: {policy_document.policy_name}",
            chunks_count=len(chunks),
        )
    
    def _create_chunks_from_list(
        self,
        items: List[str],
        prefix: str,
        max_items_per_chunk: int = 10,
    ) -> List[str]:
        """
        Create text chunks from a list of items.
        
        This helper method splits long lists into multiple chunks to avoid
        exceeding token limits and improve retrieval precision.
        
        Args:
            items: List of items to chunk
            prefix: Prefix text for each chunk
            max_items_per_chunk: Maximum items per chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        
        for i in range(0, len(items), max_items_per_chunk):
            chunk_items = items[i:i + max_items_per_chunk]
            chunk_text = prefix + ":\n" + "\n".join(f"- {item}" for item in chunk_items)
            chunks.append(chunk_text)
        
        return chunks
    
    def validate_document_before_ingestion(
        self,
        file_path: Path,
    ) -> Dict[str, any]:
        """
        Validate a document before ingestion without actually ingesting it.
        
        This is useful for pre-flight checks to give users immediate feedback
        about whether their document is suitable for ingestion.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with validation results:
                - valid: bool
                - errors: List[str]
                - warnings: List[str]
                - extracted_info: Dict (if parsing succeeded)
                
        Requirements: 12.5
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'extracted_info': None,
        }
        
        try:
            # Check file exists
            if not file_path.exists():
                result['errors'].append(f"File not found: {file_path}")
                return result
            
            # Check file format
            if file_path.suffix.lower() not in ['.txt', '.pdf']:
                result['errors'].append(
                    f"Unsupported file format: {file_path.suffix}. "
                    f"Supported formats: .txt, .pdf"
                )
                return result
            
            # Parse document
            parser = get_parser(file_path)
            text_content = parser.parse(file_path)
            
            if not text_content or len(text_content.strip()) < 100:
                result['errors'].append(
                    "Document is too short or empty. "
                    "Policy documents must contain substantial content."
                )
                return result
            
            # Extract information
            extracted_info = {
                'coverage_amount': self.extractor.extract_coverage_amount(text_content),
                'premium': self.extractor.extract_premium(text_content),
                'waiting_periods': self.extractor.extract_waiting_periods(text_content),
                'exclusions': self.extractor.extract_exclusions(text_content),
                'inclusions': self.extractor.extract_inclusions(text_content),
            }
            
            result['extracted_info'] = extracted_info
            
            # Validate extracted information
            if not extracted_info.get('coverage_amount'):
                result['errors'].append("Coverage amount not found in document")
            
            if not extracted_info.get('premium'):
                result['errors'].append("Premium amount not found in document")
            
            if not extracted_info.get('exclusions') or len(extracted_info['exclusions']) == 0:
                result['errors'].append("No exclusions found in document")
            
            if not extracted_info.get('inclusions') or len(extracted_info['inclusions']) == 0:
                result['errors'].append("No inclusions/coverage found in document")
            
            # Add warnings for potentially missing information
            if len(extracted_info.get('exclusions', [])) < 3:
                result['warnings'].append(
                    "Only a few exclusions found. Document may be incomplete."
                )
            
            if len(extracted_info.get('inclusions', [])) < 3:
                result['warnings'].append(
                    "Only a few inclusions found. Document may be incomplete."
                )
            
            # Set valid flag
            result['valid'] = len(result['errors']) == 0
            
        except Exception as e:
            result['errors'].append(f"Error during validation: {str(e)}")
        
        return result


    async def search_policies(
        self,
        query: str,
        filters: Optional[Dict] = None,
        k: int = 5,
    ) -> List[Dict]:
        """
        Search for policies using semantic search.
        
        This method performs semantic search over policy documents to find
        the most relevant policies based on the query text.
        
        Args:
            query: Search query (natural language or keywords)
            filters: Optional filters for policy metadata
                - provider_id: Filter by insurance provider
                - policy_type: Filter by policy type (individual, family, etc.)
                - min_coverage: Minimum coverage amount
                - max_premium: Maximum premium amount
            k: Number of results to return (default: 5)
            
        Returns:
            List of dictionaries containing:
                - policy_id: Policy identifier
                - policy_name: Policy name
                - provider_id: Provider identifier
                - content: Relevant text excerpt
                - score: Relevance score (lower is better)
                - metadata: Additional policy metadata
                
        Requirements: 1.1
        """
        self._log_operation(
            "search_policies",
            query=query,
            filters=filters,
            k=k,
        )
        
        if not self.vector_store:
            logger.warning("Vector store not configured, cannot perform semantic search")
            return []
        
        try:
            # Build metadata filter for vector store
            vector_filter = {}
            if filters:
                if 'provider_id' in filters:
                    vector_filter['provider_id'] = filters['provider_id']
                if 'policy_type' in filters:
                    vector_filter['policy_type'] = filters['policy_type']
            
            # Perform semantic search
            results = await self.vector_store.similarity_search(
                query=query,
                k=k * 2,  # Get more results to filter
                filter=vector_filter if vector_filter else None,
            )
            
            # Process and deduplicate results by policy_id
            seen_policies = set()
            processed_results = []
            
            for content, metadata, score in results:
                policy_id = metadata.get('policy_id')
                
                # Skip if we've already seen this policy
                if policy_id in seen_policies:
                    continue
                
                # Apply additional filters
                if filters:
                    # Filter by coverage amount
                    if 'min_coverage' in filters:
                        # Note: We'd need to store coverage in metadata for this
                        pass
                    
                    # Filter by premium
                    if 'max_premium' in filters:
                        # Note: We'd need to store premium in metadata for this
                        pass
                
                seen_policies.add(policy_id)
                processed_results.append({
                    'policy_id': policy_id,
                    'policy_name': metadata.get('policy_name', 'Unknown'),
                    'provider_id': metadata.get('provider_id', 'Unknown'),
                    'policy_type': metadata.get('policy_type', 'Unknown'),
                    'content': content,
                    'score': score,
                    'metadata': metadata,
                })
                
                # Stop when we have enough unique policies
                if len(processed_results) >= k:
                    break
            
            logger.info(
                f"Semantic search completed",
                query=query,
                results_count=len(processed_results),
            )
            
            return processed_results
            
        except Exception as e:
            self._log_error("search_policies", e, query=query)
            raise


    async def retrieve_policy_clause(
        self,
        policy_id: str,
        clause_type: str,
    ) -> Optional[str]:
        """
        Retrieve a specific clause from a policy document.
        
        This method searches for a specific type of clause (e.g., coverage,
        exclusion, waiting_period) within a policy document.
        
        Args:
            policy_id: Policy identifier
            clause_type: Type of clause to retrieve
                (coverage, exclusion, inclusion, waiting_period, claim_process)
                
        Returns:
            Clause text if found, None otherwise
            
        Requirements: 1.1
        """
        self._log_operation(
            "retrieve_policy_clause",
            policy_id=policy_id,
            clause_type=clause_type,
        )
        
        if not self.vector_store:
            logger.warning("Vector store not configured")
            return None
        
        try:
            # Search for the specific clause type within the policy
            query = f"{clause_type} for policy {policy_id}"
            
            results = await self.vector_store.similarity_search(
                query=query,
                k=3,
                filter={'policy_id': policy_id},
            )
            
            if not results:
                logger.info(
                    f"No clause found",
                    policy_id=policy_id,
                    clause_type=clause_type,
                )
                return None
            
            # Return the most relevant result
            content, metadata, score = results[0]
            
            logger.info(
                f"Retrieved policy clause",
                policy_id=policy_id,
                clause_type=clause_type,
                score=score,
            )
            
            return content
            
        except Exception as e:
            self._log_error(
                "retrieve_policy_clause",
                e,
                policy_id=policy_id,
                clause_type=clause_type,
            )
            raise
    
    async def _get_version_service(self):
        """Get or create policy versioning service instance."""
        if self._version_service is None:
            from healthcare_insurance_platform.services.policy_versioning import (
                PolicyVersioningService,
            )
            self._version_service = PolicyVersioningService(
                db_session=self.db_session,
                vector_store=self.vector_store,
            )
        return self._version_service
    
    async def get_policy_version_history(self, policy_id: str):
        """
        Get version history for a policy.
        
        Args:
            policy_id: Policy identifier
            
        Returns:
            PolicyVersionHistory
            
        Requirements: 12.3
        """
        version_service = await self._get_version_service()
        return await version_service.get_version_history(policy_id)
    
    async def compare_policy_versions(
        self,
        policy_id: str,
        old_version: str,
        new_version: str,
    ):
        """
        Compare two versions of a policy.
        
        Args:
            policy_id: Policy identifier
            old_version: Old version number
            new_version: New version number
            
        Returns:
            VersionComparison
            
        Requirements: 12.4
        """
        version_service = await self._get_version_service()
        return await version_service.compare_versions(
            policy_id=policy_id,
            old_version_number=old_version,
            new_version_number=new_version,
        )
    
    async def get_affected_analyses(
        self,
        policy_id: str,
        user_id: Optional[str] = None,
    ):
        """
        Get analyses affected by policy updates.
        
        Args:
            policy_id: Policy identifier
            user_id: Optional user ID filter
            
        Returns:
            List of AffectedAnalysis
            
        Requirements: 12.4
        """
        version_service = await self._get_version_service()
        return await version_service.get_affected_analyses(
            policy_id=policy_id,
            user_id=user_id,
        )
