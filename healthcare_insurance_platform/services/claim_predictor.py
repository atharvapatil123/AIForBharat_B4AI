"""Claim Predictor service for analyzing claims against policy terms."""

from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Tuple
import uuid

from healthcare_insurance_platform.core.logging import get_logger
from healthcare_insurance_platform.models.claim import ClaimDetails
from healthcare_insurance_platform.models.policy import PolicyDocument
from healthcare_insurance_platform.models.results import (
    ClaimPrediction,
    ContradictingFactor,
    MissingDocument,
    SupportingFactor,
)
from healthcare_insurance_platform.services.base import BaseService
from healthcare_insurance_platform.services.knowledge_base import KnowledgeBaseService
from healthcare_insurance_platform.services.llm_engine import LLMEngine

logger = get_logger(__name__)


class ClaimPredictorService(BaseService):
    """
    Service for predicting claim acceptance and analyzing claims against policy terms.
    
    Handles:
    - Claim analysis against policy terms
    - Acceptance probability calculation
    - Document requirement generation
    - Missing document identification
    
    Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBaseService] = None,
        llm_engine: Optional[LLMEngine] = None,
        db=None,
        vector_store=None,
    ):
        """Initialize Claim Predictor service.
        
        Args:
            knowledge_base: Knowledge base service for policy retrieval
            llm_engine: LLM engine for generating predictions
            db: Database session
            vector_store: Vector store for document retrieval
        """
        super().__init__(db=db, vector_store=vector_store)
        self.knowledge_base = knowledge_base or KnowledgeBaseService(
            db_session=db,
            vector_store=vector_store,
        )
        self.llm_engine = llm_engine or LLMEngine(
            db=db,
            vector_store=vector_store,
        )
    
    async def analyze_claim_against_policy(
        self,
        claim_details: ClaimDetails,
        policy_document: PolicyDocument,
        language: str = "en",
    ) -> Dict:
        """
        Analyze a claim against policy terms to identify relevant clauses.
        
        This method:
        1. Parses claim details and policy document
        2. Identifies relevant policy clauses for the claim
        3. Compares claim scenario with exclusions and waiting periods
        4. Extracts supporting and contradicting factors
        
        Args:
            claim_details: Claim information
            policy_document: Policy document to analyze against
            language: Output language (default: "en")
            
        Returns:
            Dictionary containing:
                - relevant_clauses: List of relevant policy clauses
                - exclusion_matches: List of exclusions that may apply
                - waiting_period_issues: List of waiting period concerns
                - supporting_factors: Factors supporting claim acceptance
                - contradicting_factors: Factors contradicting claim acceptance
                
        Requirements: 5.1, 5.3, 5.5
        """
        self._log_operation(
            "analyze_claim_against_policy",
            claim_id=claim_details.claim_id,
            policy_id=policy_document.policy_id,
            claim_type=claim_details.claim_type,
        )
        
        try:
            # Step 1: Identify relevant policy clauses
            relevant_clauses = await self._identify_relevant_clauses(
                claim_details=claim_details,
                policy_document=policy_document,
            )
            
            # Step 2: Check exclusions
            exclusion_matches = self._check_exclusions(
                claim_details=claim_details,
                policy_document=policy_document,
            )
            
            # Step 3: Check waiting periods
            waiting_period_issues = self._check_waiting_periods(
                claim_details=claim_details,
                policy_document=policy_document,
            )
            
            # Step 4: Analyze coverage inclusions
            inclusion_matches = self._check_inclusions(
                claim_details=claim_details,
                policy_document=policy_document,
            )
            
            # Step 5: Extract supporting and contradicting factors
            supporting_factors, contradicting_factors = self._extract_factors(
                claim_details=claim_details,
                policy_document=policy_document,
                relevant_clauses=relevant_clauses,
                exclusion_matches=exclusion_matches,
                waiting_period_issues=waiting_period_issues,
                inclusion_matches=inclusion_matches,
            )
            
            logger.info(
                "Claim analysis completed",
                claim_id=claim_details.claim_id,
                policy_id=policy_document.policy_id,
                relevant_clauses_count=len(relevant_clauses),
                exclusion_matches_count=len(exclusion_matches),
                waiting_period_issues_count=len(waiting_period_issues),
                supporting_factors_count=len(supporting_factors),
                contradicting_factors_count=len(contradicting_factors),
            )
            
            return {
                'relevant_clauses': relevant_clauses,
                'exclusion_matches': exclusion_matches,
                'waiting_period_issues': waiting_period_issues,
                'inclusion_matches': inclusion_matches,
                'supporting_factors': supporting_factors,
                'contradicting_factors': contradicting_factors,
            }
            
        except Exception as e:
            self._log_error(
                "analyze_claim_against_policy",
                e,
                claim_id=claim_details.claim_id,
                policy_id=policy_document.policy_id,
            )
            raise
    
    async def _identify_relevant_clauses(
        self,
        claim_details: ClaimDetails,
        policy_document: PolicyDocument,
    ) -> List[Dict]:
        """
        Identify policy clauses relevant to the claim.
        
        Args:
            claim_details: Claim information
            policy_document: Policy document
            
        Returns:
            List of relevant clauses with metadata
        """
        relevant_clauses = []
        
        # Get claim-specific information
        condition = claim_details.treatment_details.condition.lower()
        diagnosis = claim_details.treatment_details.diagnosis.lower()
        procedures = [p.lower() for p in claim_details.treatment_details.procedures]
        claim_type = claim_details.claim_type.lower()
        
        # Check parsed clauses for relevance
        for clause in policy_document.parsed_clauses:
            clause_text_lower = clause.text.lower()
            
            # Check if clause mentions the condition, diagnosis, or procedures
            is_relevant = False
            relevance_reason = []
            
            if condition in clause_text_lower:
                is_relevant = True
                relevance_reason.append(f"mentions condition: {condition}")
            
            if diagnosis in clause_text_lower:
                is_relevant = True
                relevance_reason.append(f"mentions diagnosis: {diagnosis}")
            
            for procedure in procedures:
                if procedure in clause_text_lower:
                    is_relevant = True
                    relevance_reason.append(f"mentions procedure: {procedure}")
                    break
            
            # Check if clause is about the claim type
            if claim_type in clause_text_lower:
                is_relevant = True
                relevance_reason.append(f"relates to claim type: {claim_type}")
            
            if is_relevant:
                relevant_clauses.append({
                    'clause_type': clause.clause_type,
                    'text': clause.text,
                    'importance': clause.importance,
                    'relevance_reason': '; '.join(relevance_reason),
                })
        
        # Always include critical clauses (coverage, waiting periods)
        for clause in policy_document.parsed_clauses:
            if clause.importance == 'critical' and clause.clause_type in ['coverage', 'waiting_period']:
                # Check if not already added
                if not any(c['text'] == clause.text for c in relevant_clauses):
                    relevant_clauses.append({
                        'clause_type': clause.clause_type,
                        'text': clause.text,
                        'importance': clause.importance,
                        'relevance_reason': 'critical policy clause',
                    })
        
        return relevant_clauses
    
    def _check_exclusions(
        self,
        claim_details: ClaimDetails,
        policy_document: PolicyDocument,
    ) -> List[Dict]:
        """
        Check if claim matches any policy exclusions.
        
        Args:
            claim_details: Claim information
            policy_document: Policy document
            
        Returns:
            List of matching exclusions
        """
        exclusion_matches = []
        
        # Get claim-specific information
        condition = claim_details.treatment_details.condition.lower()
        diagnosis = claim_details.treatment_details.diagnosis.lower()
        procedures = [p.lower() for p in claim_details.treatment_details.procedures]
        
        # Check each exclusion
        for exclusion in policy_document.exclusions:
            exclusion_lower = exclusion.lower()
            
            # Check for matches
            match_reason = []
            
            if condition in exclusion_lower or exclusion_lower in condition:
                match_reason.append(f"condition '{condition}' matches exclusion")
            
            if diagnosis in exclusion_lower or exclusion_lower in diagnosis:
                match_reason.append(f"diagnosis '{diagnosis}' matches exclusion")
            
            for procedure in procedures:
                if procedure in exclusion_lower or exclusion_lower in procedure:
                    match_reason.append(f"procedure '{procedure}' matches exclusion")
                    break
            
            if match_reason:
                exclusion_matches.append({
                    'exclusion': exclusion,
                    'match_reason': '; '.join(match_reason),
                    'severity': 'high',  # Exclusions are typically deal-breakers
                })
        
        return exclusion_matches
    
    def _check_waiting_periods(
        self,
        claim_details: ClaimDetails,
        policy_document: PolicyDocument,
    ) -> List[Dict]:
        """
        Check if claim violates waiting period requirements.
        
        Args:
            claim_details: Claim information
            policy_document: Policy document
            
        Returns:
            List of waiting period issues
        """
        waiting_period_issues = []
        
        # Note: In a real implementation, we would need the policy start date
        # and user's medical history to properly check waiting periods.
        # For now, we'll identify potential waiting period concerns.
        
        waiting_periods = policy_document.waiting_periods
        
        # Check general waiting period
        if waiting_periods.general > 0:
            waiting_period_issues.append({
                'period_type': 'general',
                'days': waiting_periods.general,
                'description': f"General waiting period of {waiting_periods.general} days applies to all claims",
                'severity': 'medium',
            })
        
        # Check pre-existing disease waiting period
        if waiting_periods.pre_existing > 0:
            waiting_period_issues.append({
                'period_type': 'pre_existing',
                'days': waiting_periods.pre_existing,
                'description': (
                    f"Pre-existing disease waiting period of {waiting_periods.pre_existing} days "
                    f"may apply if condition existed before policy start"
                ),
                'severity': 'high',
            })
        
        # Check specific condition waiting periods
        condition = claim_details.treatment_details.condition.lower()
        for specific in waiting_periods.specific_conditions:
            specific_condition = specific.get('condition', '').lower()
            specific_days = specific.get('days', 0)
            if condition in specific_condition or specific_condition in condition:
                waiting_period_issues.append({
                    'period_type': 'specific_condition',
                    'condition': specific.get('condition', ''),
                    'days': specific_days,
                    'description': (
                        f"Specific waiting period of {specific_days} days applies "
                        f"to condition: {specific.get('condition', '')}"
                    ),
                    'severity': 'high',
                })
        
        return waiting_period_issues
    
    def _check_inclusions(
        self,
        claim_details: ClaimDetails,
        policy_document: PolicyDocument,
    ) -> List[Dict]:
        """
        Check if claim matches policy inclusions/coverage.
        
        Args:
            claim_details: Claim information
            policy_document: Policy document
            
        Returns:
            List of matching inclusions
        """
        inclusion_matches = []
        
        # Get claim-specific information
        condition = claim_details.treatment_details.condition.lower()
        diagnosis = claim_details.treatment_details.diagnosis.lower()
        procedures = [p.lower() for p in claim_details.treatment_details.procedures]
        claim_type = claim_details.claim_type.lower()
        
        # Check each inclusion
        for inclusion in policy_document.inclusions:
            inclusion_lower = inclusion.lower()
            
            # Check for matches
            match_reason = []
            
            if condition in inclusion_lower or inclusion_lower in condition:
                match_reason.append(f"condition '{condition}' is covered")
            
            if diagnosis in inclusion_lower or inclusion_lower in diagnosis:
                match_reason.append(f"diagnosis '{diagnosis}' is covered")
            
            for procedure in procedures:
                if procedure in inclusion_lower or inclusion_lower in procedure:
                    match_reason.append(f"procedure '{procedure}' is covered")
                    break
            
            if claim_type in inclusion_lower:
                match_reason.append(f"claim type '{claim_type}' is covered")
            
            if match_reason:
                inclusion_matches.append({
                    'inclusion': inclusion,
                    'match_reason': '; '.join(match_reason),
                    'strength': 'strong',
                })
        
        return inclusion_matches
    
    def _extract_factors(
        self,
        claim_details: ClaimDetails,
        policy_document: PolicyDocument,
        relevant_clauses: List[Dict],
        exclusion_matches: List[Dict],
        waiting_period_issues: List[Dict],
        inclusion_matches: List[Dict],
    ) -> Tuple[List[SupportingFactor], List[ContradictingFactor]]:
        """
        Extract supporting and contradicting factors from analysis.
        
        Args:
            claim_details: Claim information
            policy_document: Policy document
            relevant_clauses: Relevant policy clauses
            exclusion_matches: Matching exclusions
            waiting_period_issues: Waiting period concerns
            inclusion_matches: Matching inclusions
            
        Returns:
            Tuple of (supporting_factors, contradicting_factors)
        """
        supporting_factors = []
        contradicting_factors = []
        
        # Add supporting factors from inclusions
        for inclusion_match in inclusion_matches:
            supporting_factors.append(
                SupportingFactor(
                    factor=f"Treatment is covered under policy inclusions",
                    policy_clause=inclusion_match['inclusion'],
                    impact='positive',
                    weight=0.3,  # Base weight for inclusion match
                )
            )
        
        # Add supporting factor if claim amount is within coverage
        if claim_details.claim_amount <= policy_document.coverage_amount:
            supporting_factors.append(
                SupportingFactor(
                    factor=f"Claim amount (₹{claim_details.claim_amount:,.0f}) is within policy coverage limit",
                    policy_clause=f"Coverage Amount: ₹{policy_document.coverage_amount:,.0f}",
                    impact='positive',
                    weight=0.2,
                )
            )
        else:
            # Exceeds coverage - contradicting factor
            contradicting_factors.append(
                ContradictingFactor(
                    factor=f"Claim amount exceeds policy coverage limit",
                    policy_clause=f"Coverage Amount: ₹{policy_document.coverage_amount:,.0f}",
                    reason=(
                        f"Claim amount (₹{claim_details.claim_amount:,.0f}) exceeds "
                        f"maximum coverage (₹{policy_document.coverage_amount:,.0f})"
                    ),
                )
            )
        
        # Add contradicting factors from exclusions
        for exclusion_match in exclusion_matches:
            contradicting_factors.append(
                ContradictingFactor(
                    factor=f"Treatment may be excluded from coverage",
                    policy_clause=exclusion_match['exclusion'],
                    reason=exclusion_match['match_reason'],
                )
            )
        
        # Add contradicting factors from waiting periods
        for waiting_issue in waiting_period_issues:
            if waiting_issue['severity'] == 'high':
                contradicting_factors.append(
                    ContradictingFactor(
                        factor=f"Waiting period may not be satisfied",
                        policy_clause=waiting_issue['description'],
                        reason=(
                            f"{waiting_issue['period_type'].replace('_', ' ').title()} "
                            f"waiting period of {waiting_issue['days']} days may apply"
                        ),
                    )
                )
        
        # Add supporting factor for claim type coverage
        if claim_details.claim_type in ['hospitalization', 'surgery']:
            # These are typically well-covered
            supporting_factors.append(
                SupportingFactor(
                    factor=f"Claim type '{claim_details.claim_type}' is typically covered",
                    policy_clause=f"Policy covers {claim_details.claim_type} expenses",
                    impact='positive',
                    weight=0.15,
                )
            )
        
        return supporting_factors, contradicting_factors

    
    async def get_policy_document(
        self,
        policy_id: str,
    ) -> Optional[PolicyDocument]:
        """
        Retrieve a policy document from the knowledge base.
        
        This is a helper method to fetch policy documents for analysis.
        In a real implementation, this would query the database or
        knowledge base service.
        
        Args:
            policy_id: Policy identifier
            
        Returns:
            PolicyDocument if found, None otherwise
        """
        self._log_operation(
            "get_policy_document",
            policy_id=policy_id,
        )
        
        try:
            # In a real implementation, this would query the database
            # For now, we'll use the vector store to search for the policy
            if not self.vector_store:
                logger.warning("Vector store not available, cannot retrieve policy")
                return None
            
            # Search for policy by ID
            results = await self.vector_store.similarity_search(
                query=f"policy {policy_id}",
                k=1,
                filter={'policy_id': policy_id},
            )
            
            if not results:
                logger.warning(f"Policy not found: {policy_id}")
                return None
            
            # Note: In a real implementation, we would reconstruct the full
            # PolicyDocument from the database. For now, we return None
            # and expect the caller to provide the policy document.
            logger.info(f"Policy document found in vector store: {policy_id}")
            return None
            
        except Exception as e:
            self._log_error("get_policy_document", e, policy_id=policy_id)
            return None
    
    def _calculate_base_probability(
        self,
        supporting_factors: List[SupportingFactor],
        contradicting_factors: List[ContradictingFactor],
    ) -> float:
        """
        Calculate base acceptance probability from factors.
        
        This uses a weighted scoring approach:
        - Start with 0.5 (neutral)
        - Add weighted positive factors
        - Subtract impact of contradicting factors
        
        Args:
            supporting_factors: List of supporting factors
            contradicting_factors: List of contradicting factors
            
        Returns:
            Probability score between 0 and 1
        """
        # Start with neutral probability
        probability = 0.5
        
        # Add supporting factor weights
        total_support = sum(factor.weight for factor in supporting_factors)
        probability += total_support * 0.3  # Scale support impact
        
        # Subtract contradicting factor impact
        # Each contradicting factor reduces probability
        contradiction_penalty = len(contradicting_factors) * 0.15
        probability -= contradiction_penalty
        
        # Ensure probability is in valid range [0, 1]
        probability = max(0.0, min(1.0, probability))
        
        return probability
    
    def _determine_confidence_level(
        self,
        supporting_factors: List[SupportingFactor],
        contradicting_factors: List[ContradictingFactor],
        relevant_clauses: List[Dict],
    ) -> str:
        """
        Determine confidence level for the prediction.
        
        Confidence is based on:
        - Number of relevant clauses found
        - Clarity of supporting/contradicting factors
        - Presence of ambiguous situations
        
        Args:
            supporting_factors: List of supporting factors
            contradicting_factors: List of contradicting factors
            relevant_clauses: List of relevant policy clauses
            
        Returns:
            Confidence level: 'low', 'medium', or 'high'
        """
        # Calculate confidence score
        confidence_score = 0
        
        # More relevant clauses = higher confidence
        if len(relevant_clauses) >= 5:
            confidence_score += 2
        elif len(relevant_clauses) >= 3:
            confidence_score += 1
        
        # Clear factors = higher confidence
        total_factors = len(supporting_factors) + len(contradicting_factors)
        if total_factors >= 4:
            confidence_score += 2
        elif total_factors >= 2:
            confidence_score += 1
        
        # Conflicting signals = lower confidence
        if supporting_factors and contradicting_factors:
            confidence_score -= 1
        
        # Map score to confidence level
        if confidence_score >= 3:
            return 'high'
        elif confidence_score >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _generate_recommendations(
        self,
        claim_details: ClaimDetails,
        analysis_result: Dict,
        acceptance_probability: float,
    ) -> List[str]:
        """
        Generate recommendations for improving claim acceptance.
        
        Args:
            claim_details: Claim information
            analysis_result: Result from analyze_claim_against_policy
            acceptance_probability: Calculated acceptance probability
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Recommendations based on exclusions
        if analysis_result['exclusion_matches']:
            recommendations.append(
                "Review policy exclusions carefully. Your claim may match excluded conditions. "
                "Consider consulting with your insurance provider for clarification."
            )
        
        # Recommendations based on waiting periods
        if analysis_result['waiting_period_issues']:
            high_severity_issues = [
                issue for issue in analysis_result['waiting_period_issues']
                if issue['severity'] == 'high'
            ]
            if high_severity_issues:
                recommendations.append(
                    "Verify that all applicable waiting periods have been satisfied. "
                    "Pre-existing disease waiting periods may apply."
                )
        
        # Recommendations based on coverage amount
        if claim_details.claim_amount > 0:
            recommendations.append(
                "Ensure all medical bills and receipts are properly documented and itemized."
            )
        
        # Recommendations based on probability
        if acceptance_probability < 0.3:
            recommendations.append(
                "Consider consulting with an insurance advisor before submitting this claim. "
                "The acceptance probability is low based on policy terms."
            )
        elif acceptance_probability < 0.6:
            recommendations.append(
                "Gather additional supporting documentation to strengthen your claim."
            )
        
        # General recommendations
        if not claim_details.documents_provided:
            recommendations.append(
                "Ensure you have all required documents before submitting the claim."
            )
        
        return recommendations
    
    def _generate_explanation(
        self,
        claim_details: ClaimDetails,
        policy_document: PolicyDocument,
        analysis_result: Dict,
        acceptance_probability: float,
        confidence_level: str,
    ) -> str:
        """
        Generate detailed explanation of the prediction.
        
        Args:
            claim_details: Claim information
            policy_document: Policy document
            analysis_result: Result from analyze_claim_against_policy
            acceptance_probability: Calculated acceptance probability
            confidence_level: Confidence level
            
        Returns:
            Explanation text
        """
        explanation_parts = []
        
        # Introduction
        explanation_parts.append(
            f"Analysis of {claim_details.claim_type} claim for "
            f"{claim_details.treatment_details.condition} against "
            f"{policy_document.policy_name}."
        )
        
        # Probability assessment
        if acceptance_probability >= 0.7:
            explanation_parts.append(
                f"The claim has a HIGH acceptance probability ({acceptance_probability:.1%}). "
                f"The treatment appears to be well-covered under the policy terms."
            )
        elif acceptance_probability >= 0.4:
            explanation_parts.append(
                f"The claim has a MODERATE acceptance probability ({acceptance_probability:.1%}). "
                f"There are both supporting and potentially contradicting factors."
            )
        else:
            explanation_parts.append(
                f"The claim has a LOW acceptance probability ({acceptance_probability:.1%}). "
                f"Several policy terms may work against claim acceptance."
            )
        
        # Supporting factors summary
        if analysis_result['supporting_factors']:
            explanation_parts.append(
                f"\nSupporting factors ({len(analysis_result['supporting_factors'])}):"
            )
            for factor in analysis_result['supporting_factors'][:3]:  # Top 3
                explanation_parts.append(f"  • {factor.factor}")
        
        # Contradicting factors summary
        if analysis_result['contradicting_factors']:
            explanation_parts.append(
                f"\nPotential issues ({len(analysis_result['contradicting_factors'])}):"
            )
            for factor in analysis_result['contradicting_factors'][:3]:  # Top 3
                explanation_parts.append(f"  • {factor.factor}")
        
        # Confidence note
        explanation_parts.append(
            f"\nConfidence level: {confidence_level.upper()}. "
            f"This assessment is based on {len(analysis_result['relevant_clauses'])} "
            f"relevant policy clauses."
        )
        
        return "\n".join(explanation_parts)
    
    def _extract_citations(
        self,
        analysis_result: Dict,
        policy_document: PolicyDocument,
    ) -> List[str]:
        """
        Extract citations from analysis result.
        
        Args:
            analysis_result: Result from analyze_claim_against_policy
            policy_document: Policy document
            
        Returns:
            List of citation strings
        """
        citations = []
        
        # Add policy document as primary citation
        citations.append(
            f"Policy Document: {policy_document.policy_name} "
            f"(Version {policy_document.version})"
        )
        
        # Add citations for relevant clauses
        for clause in analysis_result['relevant_clauses'][:5]:  # Top 5
            citations.append(
                f"{clause['clause_type'].replace('_', ' ').title()}: {clause['text'][:100]}..."
            )
        
        return citations
    
    async def predict_claim_acceptance(
        self,
        claim_details: ClaimDetails,
        policy_id: str,
        language: str = "en",
    ) -> ClaimPrediction:
        """
        Predict claim acceptance probability and generate detailed analysis.
        
        This method:
        1. Retrieves the policy document
        2. Analyzes the claim against policy terms
        3. Calculates weighted acceptance probability
        4. Generates detailed reasoning with citations
        5. Provides recommendations
        
        Args:
            claim_details: Claim information including treatment details
            policy_id: Policy identifier to analyze against
            language: Output language (default: "en")
            
        Returns:
            ClaimPrediction with acceptance probability, factors, and reasoning
            
        Requirements: 5.2, 5.3, 5.4
        """
        self._log_operation(
            "predict_claim_acceptance",
            claim_id=claim_details.claim_id,
            policy_id=policy_id,
            claim_type=claim_details.claim_type,
            claim_amount=claim_details.claim_amount,
        )
        
        try:
            # Step 1: Retrieve policy document
            # Note: In a real implementation, this would fetch from the database
            # For now, we expect the policy to be provided or retrieved via knowledge base
            policy_document = await self._get_policy_for_prediction(policy_id)
            
            if not policy_document:
                raise ValueError(f"Policy document not found: {policy_id}")
            
            # Step 2: Analyze claim against policy terms
            analysis_result = await self.analyze_claim_against_policy(
                claim_details=claim_details,
                policy_document=policy_document,
                language=language,
            )
            
            # Step 3: Calculate weighted acceptance probability
            acceptance_probability = self._calculate_acceptance_probability(
                supporting_factors=analysis_result['supporting_factors'],
                contradicting_factors=analysis_result['contradicting_factors'],
                inclusion_matches=analysis_result['inclusion_matches'],
                exclusion_matches=analysis_result['exclusion_matches'],
                waiting_period_issues=analysis_result['waiting_period_issues'],
                claim_details=claim_details,
                policy_document=policy_document,
            )
            
            # Step 4: Determine confidence level
            confidence_level = self._determine_confidence_level(
                supporting_factors=analysis_result['supporting_factors'],
                contradicting_factors=analysis_result['contradicting_factors'],
                relevant_clauses=analysis_result['relevant_clauses'],
            )
            
            # Step 5: Generate detailed explanation with citations
            explanation = self._generate_explanation(
                claim_details=claim_details,
                policy_document=policy_document,
                analysis_result=analysis_result,
                acceptance_probability=acceptance_probability,
                confidence_level=confidence_level,
            )
            
            # Step 6: Extract citations
            citations = self._extract_citations(
                analysis_result=analysis_result,
                policy_document=policy_document,
            )
            
            # Step 7: Generate recommendations
            recommendations = self._generate_recommendations(
                claim_details=claim_details,
                analysis_result=analysis_result,
                acceptance_probability=acceptance_probability,
            )
            
            # Step 8: Create ClaimPrediction result
            prediction = ClaimPrediction(
                prediction_id=str(uuid.uuid4()),
                claim_id=claim_details.claim_id,
                acceptance_probability=acceptance_probability,
                confidence_level=confidence_level,
                supporting_factors=analysis_result['supporting_factors'],
                contradicting_factors=analysis_result['contradicting_factors'],
                missing_documents=[],  # Will be populated by document analysis methods
                recommendations=recommendations,
                explanation=explanation,
                citations=citations,
                language=language,
                generated_at=datetime.now(timezone.utc),
            )
            
            logger.info(
                "Claim prediction completed",
                claim_id=claim_details.claim_id,
                policy_id=policy_id,
                acceptance_probability=acceptance_probability,
                confidence_level=confidence_level,
                supporting_factors_count=len(analysis_result['supporting_factors']),
                contradicting_factors_count=len(analysis_result['contradicting_factors']),
            )
            
            return prediction
            
        except Exception as e:
            self._log_error(
                "predict_claim_acceptance",
                e,
                claim_id=claim_details.claim_id,
                policy_id=policy_id,
            )
            raise
    
    async def _get_policy_for_prediction(
        self,
        policy_id: str,
    ) -> Optional[PolicyDocument]:
        """
        Retrieve policy document for prediction.
        
        This is a helper method that attempts to retrieve the policy
        from the knowledge base. In a real implementation, this would
        query the database directly.
        
        Args:
            policy_id: Policy identifier
            
        Returns:
            PolicyDocument if found, None otherwise
        """
        # Try to get from knowledge base
        if self.knowledge_base:
            try:
                # Search for the policy in the knowledge base
                # Note: This is a simplified implementation
                # In production, we would have a direct database query
                return await self.get_policy_document(policy_id)
            except Exception as e:
                logger.warning(
                    f"Failed to retrieve policy from knowledge base: {e}",
                    policy_id=policy_id,
                )
        
        return None
    
    def _calculate_acceptance_probability(
        self,
        supporting_factors: List[SupportingFactor],
        contradicting_factors: List[ContradictingFactor],
        inclusion_matches: List[Dict],
        exclusion_matches: List[Dict],
        waiting_period_issues: List[Dict],
        claim_details: ClaimDetails,
        policy_document: PolicyDocument,
    ) -> float:
        """
        Calculate weighted acceptance probability based on all factors.
        
        This method implements a sophisticated scoring algorithm that:
        1. Starts with a base probability
        2. Adds weighted positive factors (inclusions, coverage)
        3. Subtracts weighted negative factors (exclusions, waiting periods)
        4. Applies special rules for critical factors
        
        The algorithm ensures that:
        - Strong exclusions significantly reduce probability
        - Multiple supporting factors increase probability
        - Coverage amount violations are heavily weighted
        - Waiting period issues are context-dependent
        
        Args:
            supporting_factors: List of supporting factors
            contradicting_factors: List of contradicting factors
            inclusion_matches: List of matching inclusions
            exclusion_matches: List of matching exclusions
            waiting_period_issues: List of waiting period concerns
            claim_details: Claim information
            policy_document: Policy document
            
        Returns:
            Probability score between 0.0 and 1.0
            
        Requirements: 5.2, 5.3, 5.4
        """
        # Start with neutral base probability
        probability = 0.5
        
        # Factor 1: Supporting factors (weighted sum)
        # Each supporting factor contributes its weight
        total_support_weight = sum(factor.weight for factor in supporting_factors)
        probability += total_support_weight * 0.4  # Scale to max +0.4
        
        # Factor 2: Inclusion matches (strong positive signal)
        # Having inclusions is a strong indicator of coverage
        if inclusion_matches:
            inclusion_boost = min(len(inclusion_matches) * 0.1, 0.3)
            probability += inclusion_boost
        
        # Factor 3: Exclusion matches (strong negative signal)
        # Even one exclusion can be a deal-breaker
        if exclusion_matches:
            # First exclusion has major impact
            probability -= 0.4
            # Additional exclusions have diminishing impact
            if len(exclusion_matches) > 1:
                probability -= min((len(exclusion_matches) - 1) * 0.1, 0.2)
        
        # Factor 4: Waiting period issues
        # High severity waiting periods are significant concerns
        high_severity_waiting = [
            issue for issue in waiting_period_issues
            if issue.get('severity') == 'high'
        ]
        if high_severity_waiting:
            # Each high-severity waiting period issue reduces probability
            waiting_penalty = min(len(high_severity_waiting) * 0.15, 0.3)
            probability -= waiting_penalty
        
        # Factor 5: Coverage amount check
        # Exceeding coverage is a critical issue
        if claim_details.claim_amount > policy_document.coverage_amount:
            # Major penalty for exceeding coverage
            excess_ratio = claim_details.claim_amount / policy_document.coverage_amount
            if excess_ratio > 1.5:
                # Significantly over coverage limit
                probability -= 0.5
            else:
                # Slightly over coverage limit
                probability -= 0.3
        
        # Factor 6: Contradicting factors
        # Each contradicting factor reduces probability
        if contradicting_factors:
            # Weight by number of contradicting factors
            contradiction_penalty = min(len(contradicting_factors) * 0.1, 0.3)
            probability -= contradiction_penalty
        
        # Factor 7: Claim type consideration
        # Some claim types have historically higher acceptance rates
        if claim_details.claim_type in ['hospitalization', 'surgery']:
            # These are typically well-covered
            probability += 0.05
        elif claim_details.claim_type in ['diagnostic', 'pharmacy']:
            # These may have more restrictions
            probability -= 0.05
        
        # Ensure probability is in valid range [0.0, 1.0]
        probability = max(0.0, min(1.0, probability))
        
        logger.debug(
            "Acceptance probability calculated",
            claim_id=claim_details.claim_id,
            probability=probability,
            supporting_factors_count=len(supporting_factors),
            contradicting_factors_count=len(contradicting_factors),
            inclusion_matches_count=len(inclusion_matches),
            exclusion_matches_count=len(exclusion_matches),
            waiting_period_issues_count=len(waiting_period_issues),
        )
        
        return probability
    
    async def generate_document_requirements(
        self,
        claim_details: ClaimDetails,
        policy_id: str,
        language: str = "en",
    ) -> List[MissingDocument]:
        """
        Generate a list of required documents for a claim based on claim type and policy.
        
        This method:
        1. Retrieves the policy document
        2. Determines required documents based on claim type
        3. Generates explanations for each document
        4. Prioritizes documents by importance (critical, recommended, optional)
        5. Identifies alternative acceptable documents
        
        Args:
            claim_details: Claim information including claim type and treatment details
            policy_id: Policy identifier
            language: Output language (default: "en")
            
        Returns:
            List of MissingDocument objects with requirements, explanations, and priorities
            
        Requirements: 6.1, 6.3, 6.5
        """
        self._log_operation(
            "generate_document_requirements",
            claim_id=claim_details.claim_id,
            policy_id=policy_id,
            claim_type=claim_details.claim_type,
        )
        
        try:
            # Step 1: Retrieve policy document
            policy_document = await self._get_policy_for_prediction(policy_id)
            
            if not policy_document:
                raise ValueError(f"Policy document not found: {policy_id}")
            
            # Step 2: Get base document requirements for claim type
            base_requirements = policy_document.get_document_requirements_for_claim(
                claim_details.claim_type
            )
            
            if not base_requirements:
                logger.warning(
                    f"No document requirements found for claim type: {claim_details.claim_type}",
                    claim_id=claim_details.claim_id,
                    policy_id=policy_id,
                )
                # Return empty list if no requirements found
                return []
            
            # Step 3: Generate detailed document requirements with explanations and priorities
            document_requirements = []
            
            # Process each required document
            for doc_type in base_requirements.documents:
                # Determine importance level based on document type and claim details
                importance = self._determine_document_importance(
                    doc_type=doc_type,
                    claim_details=claim_details,
                    policy_document=policy_document,
                )
                
                # Generate explanation for why this document is required
                reason = self._generate_document_reason(
                    doc_type=doc_type,
                    claim_details=claim_details,
                    policy_document=policy_document,
                )
                
                # Identify alternative acceptable documents
                alternatives = self._identify_document_alternatives(
                    doc_type=doc_type,
                    claim_details=claim_details,
                )
                
                # Create MissingDocument object
                document_requirements.append(
                    MissingDocument(
                        document_type=doc_type,
                        importance=importance,
                        reason=reason,
                        alternatives=alternatives,
                    )
                )
            
            # Step 4: Add claim-specific additional documents
            additional_docs = self._identify_additional_documents(
                claim_details=claim_details,
                policy_document=policy_document,
            )
            
            for doc in additional_docs:
                # Check if not already in the list
                if not any(d.document_type == doc['document_type'] for d in document_requirements):
                    document_requirements.append(
                        MissingDocument(
                            document_type=doc['document_type'],
                            importance=doc['importance'],
                            reason=doc['reason'],
                            alternatives=doc.get('alternatives', []),
                        )
                    )
            
            # Step 5: Sort by importance (critical first, then recommended, then optional)
            importance_order = {'critical': 0, 'recommended': 1, 'optional': 2}
            document_requirements.sort(
                key=lambda d: importance_order.get(d.importance, 3)
            )
            
            logger.info(
                "Document requirements generated",
                claim_id=claim_details.claim_id,
                policy_id=policy_id,
                total_documents=len(document_requirements),
                critical_count=sum(1 for d in document_requirements if d.importance == 'critical'),
                recommended_count=sum(1 for d in document_requirements if d.importance == 'recommended'),
                optional_count=sum(1 for d in document_requirements if d.importance == 'optional'),
            )
            
            return document_requirements
            
        except Exception as e:
            self._log_error(
                "generate_document_requirements",
                e,
                claim_id=claim_details.claim_id,
                policy_id=policy_id,
            )
            raise
    
    def _determine_document_importance(
        self,
        doc_type: str,
        claim_details: ClaimDetails,
        policy_document: PolicyDocument,
    ) -> str:
        """
        Determine the importance level of a document for a claim.
        
        Importance is based on:
        - Document type (some are always critical)
        - Claim amount (higher amounts need more documentation)
        - Claim type (surgery requires more docs than diagnostic)
        - Policy requirements
        
        Args:
            doc_type: Type of document
            claim_details: Claim information
            policy_document: Policy document
            
        Returns:
            Importance level: 'critical', 'recommended', or 'optional'
        """
        doc_type_lower = doc_type.lower()
        
        # Critical documents (always required, claim will be rejected without them)
        critical_docs = {
            'discharge_summary', 'discharge_card', 'hospital_bill', 'medical_bill',
            'original_bills', 'itemized_bill', 'claim_form', 'policy_copy',
            'id_proof', 'surgery_report', 'operation_notes', 'anesthesia_report',
        }
        
        # Check if document type matches critical patterns
        for critical_doc in critical_docs:
            if critical_doc in doc_type_lower or doc_type_lower in critical_doc:
                return 'critical'
        
        # Recommended documents (strongly advised, may delay claim without them)
        recommended_docs = {
            'diagnostic_report', 'lab_report', 'test_report', 'prescription',
            'doctor_certificate', 'medical_certificate', 'consultation_notes',
            'pharmacy_bill', 'investigation_report', 'radiology_report',
        }
        
        for recommended_doc in recommended_docs:
            if recommended_doc in doc_type_lower or doc_type_lower in recommended_doc:
                return 'recommended'
        
        # High-value claims need more critical documentation
        if claim_details.claim_amount > policy_document.coverage_amount * 0.5:
            # For claims over 50% of coverage, most documents become critical
            if any(keyword in doc_type_lower for keyword in ['report', 'certificate', 'bill']):
                return 'critical'
        
        # Surgery and hospitalization claims have stricter requirements
        if claim_details.claim_type in ['surgery', 'hospitalization']:
            if any(keyword in doc_type_lower for keyword in ['report', 'summary', 'notes']):
                return 'recommended'
        
        # Default to optional
        return 'optional'
    
    def _generate_document_reason(
        self,
        doc_type: str,
        claim_details: ClaimDetails,
        policy_document: PolicyDocument,
    ) -> str:
        """
        Generate an explanation for why a document is required.
        
        Args:
            doc_type: Type of document
            claim_details: Claim information
            policy_document: Policy document
            
        Returns:
            Explanation string
        """
        doc_type_lower = doc_type.lower()
        claim_type = claim_details.claim_type
        condition = claim_details.treatment_details.condition
        
        # Generate specific reasons based on document type
        if 'discharge' in doc_type_lower and 'summary' in doc_type_lower:
            return (
                f"Discharge summary is required to verify the diagnosis, treatment provided, "
                f"and duration of hospitalization for your {condition} claim. "
                f"This is a mandatory document for all {claim_type} claims."
            )
        
        elif 'discharge' in doc_type_lower and 'card' in doc_type_lower:
            return (
                f"Discharge card confirms your admission and discharge dates, "
                f"which is essential for validating the claim period and calculating eligible expenses."
            )
        
        elif 'bill' in doc_type_lower or 'invoice' in doc_type_lower:
            if 'hospital' in doc_type_lower or 'medical' in doc_type_lower:
                return (
                    f"Original itemized hospital bills are required to verify the actual expenses incurred "
                    f"during treatment. The policy requires detailed billing to process claims for {condition}."
                )
            elif 'pharmacy' in doc_type_lower:
                return (
                    f"Pharmacy bills with prescription details are needed to verify medication expenses "
                    f"related to your {condition} treatment."
                )
            else:
                return (
                    f"Original bills are required to substantiate the claim amount of ₹{claim_details.claim_amount:,.0f} "
                    f"and ensure compliance with policy terms."
                )
        
        elif 'surgery' in doc_type_lower or 'operation' in doc_type_lower:
            return (
                f"Surgery/operation report is mandatory for surgical procedures. "
                f"It provides details about the procedure performed, surgeon information, "
                f"and medical necessity, which are required for claim approval."
            )
        
        elif 'diagnostic' in doc_type_lower or 'lab' in doc_type_lower or 'test' in doc_type_lower:
            return (
                f"Diagnostic and laboratory reports support the medical diagnosis of {condition} "
                f"and help establish the medical necessity of the treatment claimed."
            )
        
        elif 'prescription' in doc_type_lower:
            return (
                f"Doctor's prescription validates the medications and treatments prescribed for {condition}, "
                f"ensuring that claimed expenses are medically necessary and appropriate."
            )
        
        elif 'certificate' in doc_type_lower:
            if 'doctor' in doc_type_lower or 'medical' in doc_type_lower:
                return (
                    f"Medical certificate from the treating doctor confirms the diagnosis, "
                    f"treatment necessity, and fitness status, supporting your claim for {condition}."
                )
            else:
                return (
                    f"Certificate is required to verify specific aspects of your {claim_type} claim "
                    f"as per policy requirements."
                )
        
        elif 'claim' in doc_type_lower and 'form' in doc_type_lower:
            return (
                f"Completed claim form is mandatory to initiate the claim process. "
                f"It captures essential information about the policyholder, treatment, and expenses."
            )
        
        elif 'policy' in doc_type_lower:
            return (
                f"Copy of the insurance policy document is required to verify coverage terms, "
                f"policy number, and ensure the claim is filed under the correct policy."
            )
        
        elif 'id' in doc_type_lower or 'identity' in doc_type_lower or 'proof' in doc_type_lower:
            return (
                f"Identity proof is required to verify the policyholder's identity "
                f"and prevent fraudulent claims."
            )
        
        elif 'investigation' in doc_type_lower:
            return (
                f"Investigation reports provide detailed medical findings that support "
                f"the diagnosis and treatment plan for {condition}."
            )
        
        elif 'consultation' in doc_type_lower:
            return (
                f"Consultation notes document the doctor's assessment, diagnosis, and treatment plan, "
                f"which are important for validating the medical necessity of the claim."
            )
        
        elif 'anesthesia' in doc_type_lower:
            return (
                f"Anesthesia report is required for surgical procedures to document "
                f"the type and duration of anesthesia used, which affects claim processing."
            )
        
        else:
            # Generic reason
            return (
                f"This document is required as per policy terms to process your {claim_type} claim "
                f"for {condition}. It helps verify the treatment details and claim amount."
            )
    
    def _identify_document_alternatives(
        self,
        doc_type: str,
        claim_details: ClaimDetails,
    ) -> List[str]:
        """
        Identify alternative acceptable documents for a required document.
        
        Args:
            doc_type: Type of document
            claim_details: Claim information
            
        Returns:
            List of alternative document types
        """
        doc_type_lower = doc_type.lower()
        alternatives = []
        
        # Define alternative documents
        if 'discharge' in doc_type_lower and 'summary' in doc_type_lower:
            alternatives = ['discharge_card', 'hospital_discharge_certificate', 'final_medical_report']
        
        elif 'discharge' in doc_type_lower and 'card' in doc_type_lower:
            alternatives = ['discharge_summary', 'hospital_admission_discharge_certificate']
        
        elif 'id' in doc_type_lower or 'identity' in doc_type_lower:
            alternatives = ['passport', 'drivers_license', 'voter_id', 'aadhaar_card', 'pan_card']
        
        elif 'medical' in doc_type_lower and 'certificate' in doc_type_lower:
            alternatives = ['doctor_certificate', 'attending_physician_statement', 'medical_report']
        
        elif 'prescription' in doc_type_lower:
            alternatives = ['doctor_prescription', 'medication_order', 'treatment_plan']
        
        elif 'hospital' in doc_type_lower and 'bill' in doc_type_lower:
            alternatives = ['itemized_medical_bill', 'consolidated_bill', 'final_hospital_invoice']
        
        elif 'diagnostic' in doc_type_lower or 'lab' in doc_type_lower:
            alternatives = ['test_report', 'laboratory_results', 'investigation_report', 'pathology_report']
        
        elif 'surgery' in doc_type_lower and 'report' in doc_type_lower:
            alternatives = ['operation_notes', 'surgical_procedure_report', 'operative_report']
        
        elif 'pharmacy' in doc_type_lower and 'bill' in doc_type_lower:
            alternatives = ['medicine_bill', 'drug_invoice', 'prescription_bill']
        
        return alternatives
    
    def _identify_additional_documents(
        self,
        claim_details: ClaimDetails,
        policy_document: PolicyDocument,
    ) -> List[Dict]:
        """
        Identify additional documents that may be required based on claim specifics.
        
        This method analyzes the claim details and policy to identify documents
        that may not be in the base requirements but are needed for this specific claim.
        
        Args:
            claim_details: Claim information
            policy_document: Policy document
            
        Returns:
            List of additional document dictionaries
        """
        additional_docs = []
        
        # High-value claims need additional verification
        if claim_details.claim_amount > policy_document.coverage_amount * 0.7:
            additional_docs.append({
                'document_type': 'detailed_cost_breakdown',
                'importance': 'critical',
                'reason': (
                    f"Detailed cost breakdown is required for high-value claims "
                    f"(₹{claim_details.claim_amount:,.0f}) to verify each expense component."
                ),
                'alternatives': ['itemized_bill_with_descriptions', 'expense_summary_sheet'],
            })
        
        # Surgery claims need specific documents
        if claim_details.claim_type == 'surgery':
            # Check if surgery report is already in requirements
            additional_docs.append({
                'document_type': 'pre_operative_assessment',
                'importance': 'recommended',
                'reason': (
                    "Pre-operative assessment documents the medical evaluation before surgery, "
                    "supporting the medical necessity of the procedure."
                ),
                'alternatives': ['pre_surgery_consultation_notes', 'surgical_clearance_certificate'],
            })
            
            additional_docs.append({
                'document_type': 'post_operative_notes',
                'importance': 'recommended',
                'reason': (
                    "Post-operative notes document the patient's condition after surgery "
                    "and any complications, which are important for claim assessment."
                ),
                'alternatives': ['post_surgery_follow_up_report', 'recovery_notes'],
            })
        
        # Hospitalization claims may need additional documents
        if claim_details.claim_type == 'hospitalization':
            # Check admission duration (if we had admission/discharge dates, we could calculate)
            additional_docs.append({
                'document_type': 'daily_treatment_chart',
                'importance': 'optional',
                'reason': (
                    "Daily treatment chart provides a detailed record of treatments and medications "
                    "administered during hospitalization, supporting the claimed expenses."
                ),
                'alternatives': ['nursing_notes', 'treatment_summary'],
            })
        
        # Check for specific procedures that need additional documentation
        procedures = claim_details.treatment_details.procedures
        for procedure in procedures:
            procedure_lower = procedure.lower()
            
            if 'implant' in procedure_lower or 'prosthesis' in procedure_lower:
                additional_docs.append({
                    'document_type': 'implant_invoice_and_sticker',
                    'importance': 'critical',
                    'reason': (
                        f"Implant invoice with manufacturer sticker is mandatory for procedures "
                        f"involving implants ({procedure}) to verify authenticity and cost."
                    ),
                    'alternatives': ['implant_certificate', 'prosthesis_documentation'],
                })
            
            if 'icu' in procedure_lower or 'intensive' in procedure_lower:
                additional_docs.append({
                    'document_type': 'icu_admission_notes',
                    'importance': 'recommended',
                    'reason': (
                        "ICU admission documentation is needed to justify intensive care expenses "
                        "and verify the medical necessity of ICU treatment."
                    ),
                    'alternatives': ['critical_care_notes', 'icu_treatment_summary'],
                })
        
        # Check for conditions that need additional documentation
        condition_lower = claim_details.treatment_details.condition.lower()
        
        if any(keyword in condition_lower for keyword in ['cancer', 'tumor', 'malignancy']):
            additional_docs.append({
                'document_type': 'histopathology_report',
                'importance': 'critical',
                'reason': (
                    "Histopathology report is essential for cancer-related claims to confirm "
                    "the diagnosis and stage of the disease."
                ),
                'alternatives': ['biopsy_report', 'pathology_report'],
            })
        
        if any(keyword in condition_lower for keyword in ['cardiac', 'heart', 'coronary']):
            additional_docs.append({
                'document_type': 'ecg_report',
                'importance': 'recommended',
                'reason': (
                    "ECG report is important for cardiac conditions to document heart function "
                    "and support the medical necessity of treatment."
                ),
                'alternatives': ['electrocardiogram', 'cardiac_monitoring_report'],
            })
        
        if any(keyword in condition_lower for keyword in ['fracture', 'bone', 'orthopedic']):
            additional_docs.append({
                'document_type': 'xray_report',
                'importance': 'critical',
                'reason': (
                    "X-ray report is required for orthopedic conditions to confirm the diagnosis "
                    "and document the extent of injury."
                ),
                'alternatives': ['radiological_report', 'imaging_report'],
            })
        
        return additional_docs

    async def identify_missing_documents(
        self,
        claim_details: ClaimDetails,
        policy_id: str,
        provided_docs: List[str],
        language: str = "en",
    ) -> List[MissingDocument]:
        """
        Identify missing documents by comparing required vs provided documents.
        
        This method:
        1. Generates the list of required documents for the claim
        2. Compares required documents with provided documents
        3. Identifies gaps in documentation
        4. Suggests alternative acceptable documents for missing items
        5. Prioritizes missing documents by importance
        
        Args:
            claim_details: Claim information including claim type and treatment details
            policy_id: Policy identifier
            provided_docs: List of document types that the user has provided
            language: Output language (default: "en")
            
        Returns:
            List of MissingDocument objects for documents that are required but not provided
            
        Requirements: 6.2, 6.4
        """
        self._log_operation(
            "identify_missing_documents",
            claim_id=claim_details.claim_id,
            policy_id=policy_id,
            provided_docs_count=len(provided_docs),
        )
        
        try:
            # Step 1: Generate complete list of required documents
            required_documents = await self.generate_document_requirements(
                claim_details=claim_details,
                policy_id=policy_id,
                language=language,
            )
            
            if not required_documents:
                logger.warning(
                    "No required documents found for claim",
                    claim_id=claim_details.claim_id,
                    policy_id=policy_id,
                )
                return []
            
            # Step 2: Normalize provided document names for comparison
            # Convert to lowercase and remove common variations
            normalized_provided = set()
            for doc in provided_docs:
                normalized_provided.add(self._normalize_document_name(doc))
            
            logger.debug(
                "Normalized provided documents",
                claim_id=claim_details.claim_id,
                original_count=len(provided_docs),
                normalized_count=len(normalized_provided),
                normalized_docs=list(normalized_provided),
            )
            
            # Step 3: Identify missing documents
            missing_documents = []
            
            for required_doc in required_documents:
                # Normalize the required document name
                normalized_required = self._normalize_document_name(required_doc.document_type)
                
                # Check if this document or any of its alternatives are provided
                is_provided = self._check_document_provided(
                    required_doc=required_doc,
                    normalized_required=normalized_required,
                    normalized_provided=normalized_provided,
                )
                
                if not is_provided:
                    # Document is missing - add to the list
                    missing_documents.append(required_doc)
                    
                    logger.debug(
                        "Missing document identified",
                        claim_id=claim_details.claim_id,
                        document_type=required_doc.document_type,
                        importance=required_doc.importance,
                    )
            
            # Step 4: Sort missing documents by importance
            # Critical documents first, then recommended, then optional
            importance_order = {'critical': 0, 'recommended': 1, 'optional': 2}
            missing_documents.sort(
                key=lambda d: importance_order.get(d.importance, 3)
            )
            
            logger.info(
                "Missing documents identified",
                claim_id=claim_details.claim_id,
                policy_id=policy_id,
                total_required=len(required_documents),
                total_provided=len(provided_docs),
                total_missing=len(missing_documents),
                critical_missing=sum(1 for d in missing_documents if d.importance == 'critical'),
                recommended_missing=sum(1 for d in missing_documents if d.importance == 'recommended'),
                optional_missing=sum(1 for d in missing_documents if d.importance == 'optional'),
            )
            
            return missing_documents
            
        except Exception as e:
            self._log_error(
                "identify_missing_documents",
                e,
                claim_id=claim_details.claim_id,
                policy_id=policy_id,
            )
            raise
    
    def _normalize_document_name(self, doc_name: str) -> str:
        """
        Normalize document name for comparison.
        
        This method:
        - Converts to lowercase
        - Removes common prefixes/suffixes
        - Removes special characters and extra spaces
        - Standardizes common variations
        
        Args:
            doc_name: Original document name
            
        Returns:
            Normalized document name
        """
        if not doc_name:
            return ""
        
        # Convert to lowercase
        normalized = doc_name.lower().strip()
        
        # Remove common prefixes
        prefixes_to_remove = ['original_', 'copy_of_', 'certified_', 'attested_']
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        
        # Remove common suffixes
        suffixes_to_remove = ['_copy', '_original', '_document', '_form']
        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        
        # Replace underscores and hyphens with spaces
        normalized = normalized.replace('_', ' ').replace('-', ' ')
        
        # Remove special characters except spaces
        normalized = ''.join(char for char in normalized if char.isalnum() or char.isspace())
        
        # Collapse multiple spaces into one
        normalized = ' '.join(normalized.split())
        
        # Standardize common variations
        standardizations = {
            'discharge summary': 'discharge summary',
            'summary discharge': 'discharge summary',
            'discharge report': 'discharge summary',
            'discharge card': 'discharge card',
            'discharge certificate': 'discharge card',
            'hospital bill': 'hospital bill',
            'medical bill': 'hospital bill',
            'hospital invoice': 'hospital bill',
            'claim form': 'claim form',
            'claim application': 'claim form',
            'id proof': 'id proof',
            'identity proof': 'id proof',
            'identification': 'id proof',
            'surgery report': 'surgery report',
            'surgical report': 'surgery report',
            'operation report': 'surgery report',
            'operation notes': 'surgery report',
            'lab report': 'lab report',
            'laboratory report': 'lab report',
            'test report': 'lab report',
            'diagnostic report': 'lab report',
            'prescription': 'prescription',
            'doctor prescription': 'prescription',
            'medical prescription': 'prescription',
        }
        
        # Apply standardizations
        for variation, standard in standardizations.items():
            if variation in normalized:
                normalized = standard
                break
        
        return normalized
    
    def _check_document_provided(
        self,
        required_doc: MissingDocument,
        normalized_required: str,
        normalized_provided: set,
    ) -> bool:
        """
        Check if a required document or any of its alternatives are provided.
        
        This method checks:
        1. Exact match with normalized required document name
        2. Partial match (required name is substring of provided, or vice versa)
        3. Match with any of the alternative documents
        
        Args:
            required_doc: Required document object
            normalized_required: Normalized name of required document
            normalized_provided: Set of normalized provided document names
            
        Returns:
            True if document is provided (directly or via alternative), False otherwise
        """
        # Check 1: Exact match
        if normalized_required in normalized_provided:
            return True
        
        # Check 2: Partial match (fuzzy matching)
        # Check if required document name is a substring of any provided document
        for provided in normalized_provided:
            # Check if required is substring of provided
            if normalized_required in provided:
                return True
            # Check if provided is substring of required (for shorter provided names)
            if provided in normalized_required and len(provided) > 5:
                # Only match if provided name is reasonably long (> 5 chars)
                # to avoid false positives like "id" matching "medical"
                return True
        
        # Check 3: Check alternatives
        if required_doc.alternatives:
            for alternative in required_doc.alternatives:
                normalized_alternative = self._normalize_document_name(alternative)
                
                # Exact match with alternative
                if normalized_alternative in normalized_provided:
                    return True
                
                # Partial match with alternative
                for provided in normalized_provided:
                    if normalized_alternative in provided or (
                        provided in normalized_alternative and len(provided) > 5
                    ):
                        return True
        
        # Document not found
        return False
