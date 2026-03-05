"""Policy Analyzer service for comparing and analyzing insurance policies."""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from healthcare_insurance_platform.core.logging import get_logger
from healthcare_insurance_platform.models.policy import PolicyDocument
from healthcare_insurance_platform.models.results import (
    ComparedPolicy,
    ComparisonResult,
    CompatibilityReport,
    CompatiblePolicy,
    MedicationAnalysis,
    PEDAnalysis,
    PolicyClause,
    PolicyExplanation,
    PolicyScore,
)
from healthcare_insurance_platform.models.user_profile import UserProfile
from healthcare_insurance_platform.services.base import BaseService
from healthcare_insurance_platform.services.knowledge_base import KnowledgeBaseService
from healthcare_insurance_platform.services.llm_engine import LLMEngine
from healthcare_insurance_platform.services.translation import TranslationService


logger = get_logger(__name__)


class PolicyFilters(BaseModel):
    """Filters for policy search and comparison."""
    
    min_coverage: Optional[float] = Field(None, ge=0, description="Minimum coverage amount")
    max_coverage: Optional[float] = Field(None, ge=0, description="Maximum coverage amount")
    min_premium: Optional[float] = Field(None, ge=0, description="Minimum premium amount")
    max_premium: Optional[float] = Field(None, ge=0, description="Maximum premium amount")
    policy_type: Optional[str] = Field(None, description="Policy type filter")
    provider_id: Optional[str] = Field(None, description="Insurance provider filter")
    required_benefits: List[str] = Field(
        default_factory=list,
        description="List of required benefits/coverage"
    )


class PolicyAnalyzer(BaseService):
    """
    Policy Analyzer service for comparing and analyzing insurance policies.
    
    This service provides functionality to:
    - Compare multiple insurance policies based on user profile
    - Score policies based on PED compatibility, cost, and coverage
    - Generate structured comparison results with recommendations
    - Support multilingual output
    
    Validates: Requirements 1.1, 1.2, 1.3
    """
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBaseService] = None,
        llm_engine: Optional[LLMEngine] = None,
        translation_service: Optional[TranslationService] = None,
        db=None,
        vector_store=None,
    ):
        """Initialize Policy Analyzer service.
        
        Args:
            knowledge_base: Knowledge base service for policy retrieval
            llm_engine: LLM engine for generating explanations
            translation_service: Translation service for multilingual support
            db: Database session
            vector_store: Vector store
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
        self.translation_service = translation_service or TranslationService(
            db=db,
            vector_store=vector_store,
        )
    
    async def compare_plans(
        self,
        user_profile: UserProfile,
        filters: Optional[PolicyFilters] = None,
        language: str = "en",
        max_policies: int = 10,
    ) -> ComparisonResult:
        """
        Compare insurance plans based on user profile and filters.
        
        This method:
        1. Retrieves policies from knowledge base matching filters
        2. Scores each policy based on user profile
        3. Generates pros/cons and recommendations
        4. Translates results to requested language
        
        Args:
            user_profile: User profile with medical history
            filters: Optional filters for policy search
            language: Target language for results (ISO code)
            max_policies: Maximum number of policies to compare
            
        Returns:
            ComparisonResult with scored and ranked policies
            
        Raises:
            ValueError: If no policies found matching filters
            
        Requirements: 1.1, 1.2, 1.3
        """
        self._log_operation(
            "compare_plans",
            user_id=user_profile.user_id,
            language=language,
            max_policies=max_policies,
        )
        
        try:
            # Step 1: Retrieve policies from knowledge base
            policies = await self._retrieve_policies(filters, max_policies)
            
            if not policies:
                raise ValueError(
                    "No policies found matching the specified filters. "
                    "Please adjust your search criteria."
                )
            
            self.logger.info(
                f"Retrieved {len(policies)} policies for comparison",
                user_id=user_profile.user_id,
            )
            
            # Step 2: Score each policy based on user profile
            compared_policies = []
            for policy in policies:
                scored_policy = await self._score_policy(policy, user_profile)
                compared_policies.append(scored_policy)
            
            # Sort by overall score (descending)
            compared_policies.sort(key=lambda p: p.overall_score, reverse=True)
            
            # Step 3: Generate overall recommendations
            recommendations = await self._generate_recommendations(
                compared_policies,
                user_profile,
                language,
            )
            
            # Step 4: Generate explanation
            explanation = await self._generate_comparison_explanation(
                compared_policies,
                user_profile,
                language,
            )
            
            # Step 5: Create comparison result
            result = ComparisonResult(
                request_id=str(uuid.uuid4()),
                user_profile_id=user_profile.user_id,
                compared_policies=compared_policies,
                recommendations=recommendations,
                explanation=explanation,
                citations=self._extract_policy_citations(policies),
                language=language,
                generated_at=datetime.now(timezone.utc),
            )
            
            self.logger.info(
                "Policy comparison completed",
                user_id=user_profile.user_id,
                policies_compared=len(compared_policies),
                language=language,
            )
            
            return result
        
        except Exception as e:
            self._log_error("compare_plans", e, user_id=user_profile.user_id)
            raise
    
    async def _retrieve_policies(
        self,
        filters: Optional[PolicyFilters],
        max_policies: int,
    ) -> List[PolicyDocument]:
        """
        Retrieve policies from knowledge base matching filters.
        
        Args:
            filters: Policy filters
            max_policies: Maximum number of policies to retrieve
            
        Returns:
            List of policy documents
            
        Requirements: 1.1, 1.3
        """
        # Build search query based on filters
        search_query = "health insurance policy"
        
        if filters and filters.required_benefits:
            # Add required benefits to search query for better semantic matching
            benefits_text = " ".join(filters.required_benefits)
            search_query = f"health insurance policy covering {benefits_text}"
        
        # Build metadata filters for knowledge base
        kb_filters = {}
        if filters:
            if filters.provider_id:
                kb_filters['provider_id'] = filters.provider_id
            if filters.policy_type:
                kb_filters['policy_type'] = filters.policy_type
        
        # Search knowledge base
        search_results = await self.knowledge_base.search_policies(
            query=search_query,
            filters=kb_filters if kb_filters else None,
            k=max_policies * 2,  # Get more to filter
        )
        
        # For now, we'll create mock PolicyDocument objects from search results
        # In a real implementation, we'd retrieve full documents from database
        policies = []
        seen_policy_ids = set()
        
        for result in search_results:
            policy_id = result.get('policy_id')
            
            # Skip duplicates
            if policy_id in seen_policy_ids:
                continue
            
            seen_policy_ids.add(policy_id)
            
            # Apply additional filters
            if filters:
                # Filter by coverage amount
                if filters.min_coverage or filters.max_coverage:
                    coverage = result.get('metadata', {}).get('coverage_amount', 0)
                    if filters.min_coverage and coverage < filters.min_coverage:
                        continue
                    if filters.max_coverage and coverage > filters.max_coverage:
                        continue
                
                # Filter by premium
                if filters.min_premium or filters.max_premium:
                    premium = result.get('metadata', {}).get('premium', 0)
                    if filters.min_premium and premium < filters.min_premium:
                        continue
                    if filters.max_premium and premium > filters.max_premium:
                        continue
            
            # Create a simplified PolicyDocument from search result
            # Note: In production, we'd fetch the full document from database
            policy = self._create_policy_from_search_result(result)
            policies.append(policy)
            
            if len(policies) >= max_policies:
                break
        
        return policies
    
    def _create_policy_from_search_result(self, result: Dict) -> PolicyDocument:
        """
        Create a PolicyDocument from search result.
        
        This is a helper method that constructs a PolicyDocument from
        search result metadata. In production, this would fetch the full
        document from the database.
        
        Args:
            result: Search result dictionary
            
        Returns:
            PolicyDocument instance
        """
        from datetime import date
        from healthcare_insurance_platform.models.policy import (
            DocumentRequirement,
            ParsedClause,
            WaitingPeriod,
        )
        
        metadata = result.get('metadata', {})
        
        # Extract basic information
        policy_id = result.get('policy_id', 'unknown')
        policy_name = result.get('policy_name', 'Unknown Policy')
        provider_id = result.get('provider_id', 'unknown')
        policy_type = result.get('policy_type', 'individual')
        coverage_amount = metadata.get('coverage_amount', 500000)
        premium = metadata.get('premium', 10000)
        
        # Create default structures
        waiting_periods = WaitingPeriod(
            general=30,
            pre_existing=730,
            specific_conditions=[],
        )
        
        # Parse content for inclusions/exclusions
        content = result.get('content', '')
        inclusions = self._extract_inclusions_from_content(content)
        exclusions = self._extract_exclusions_from_content(content)
        
        # Create document requirements
        document_requirements = [
            DocumentRequirement(
                claim_type="hospitalization",
                documents=["Hospital discharge summary", "Medical bills", "Diagnostic reports"]
            )
        ]
        
        # Create parsed clauses
        parsed_clauses = [
            ParsedClause(
                clause_type="coverage",
                text=f"Coverage amount: Rs. {coverage_amount:,.0f}",
                importance="critical",
            ),
            ParsedClause(
                clause_type="premium",
                text=f"Annual premium: Rs. {premium:,.0f}",
                importance="critical",
            ),
        ]
        
        return PolicyDocument(
            policy_id=policy_id,
            provider_id=provider_id,
            policy_name=policy_name,
            policy_type=policy_type,
            version=metadata.get('version', '1.0'),
            effective_date=date.today(),
            coverage_amount=coverage_amount,
            premium=premium,
            waiting_periods=waiting_periods,
            inclusions=inclusions if inclusions else ["General hospitalization", "Diagnostic tests"],
            exclusions=exclusions if exclusions else ["Cosmetic procedures", "Dental treatment"],
            ped_policy="Pre-existing diseases covered after waiting period",
            claim_process="Submit claim with required documents within 30 days",
            document_requirements=document_requirements,
            full_text=content,
            parsed_clauses=parsed_clauses,
            last_updated=datetime.now(timezone.utc),
        )
    
    def _extract_inclusions_from_content(self, content: str) -> List[str]:
        """Extract inclusions from policy content."""
        inclusions = []
        
        # Look for inclusion keywords
        if "hospitalization" in content.lower():
            inclusions.append("Hospitalization expenses")
        if "surgery" in content.lower() or "surgical" in content.lower():
            inclusions.append("Surgical procedures")
        if "diagnostic" in content.lower() or "tests" in content.lower():
            inclusions.append("Diagnostic tests")
        if "ambulance" in content.lower():
            inclusions.append("Ambulance charges")
        if "daycare" in content.lower() or "day care" in content.lower():
            inclusions.append("Day care procedures")
        
        return inclusions if inclusions else ["General medical coverage"]
    
    def _extract_exclusions_from_content(self, content: str) -> List[str]:
        """Extract exclusions from policy content."""
        exclusions = []
        
        # Look for exclusion keywords
        if "cosmetic" in content.lower():
            exclusions.append("Cosmetic procedures")
        if "dental" in content.lower():
            exclusions.append("Dental treatment")
        if "infertility" in content.lower():
            exclusions.append("Infertility treatment")
        if "war" in content.lower():
            exclusions.append("War-related injuries")
        if "self-inflicted" in content.lower():
            exclusions.append("Self-inflicted injuries")
        
        return exclusions if exclusions else ["Standard exclusions apply"]
    
    async def _score_policy(
        self,
        policy: PolicyDocument,
        user_profile: UserProfile,
    ) -> ComparedPolicy:
        """
        Score a policy based on user profile.
        
        Scoring considers:
        - PED compatibility (40% weight)
        - Cost effectiveness (30% weight)
        - Coverage comprehensiveness (20% weight)
        - Claim settlement ratio (10% weight)
        
        Args:
            policy: Policy document to score
            user_profile: User profile
            
        Returns:
            ComparedPolicy with scores and analysis
            
        Requirements: 1.2
        """
        # Calculate individual scores
        ped_score = self._calculate_ped_compatibility_score(policy, user_profile)
        cost_score = self._calculate_cost_effectiveness_score(policy, user_profile)
        coverage_score = self._calculate_coverage_score(policy)
        claim_ratio_score = self._calculate_claim_settlement_score(policy)
        
        # Calculate weighted overall score
        overall_score = (
            ped_score * 0.4 +
            cost_score * 0.3 +
            coverage_score * 0.2 +
            claim_ratio_score * 0.1
        )
        
        # Generate pros and cons
        pros, cons = self._generate_pros_cons(policy, user_profile, {
            'ped': ped_score,
            'cost': cost_score,
            'coverage': coverage_score,
            'claim_ratio': claim_ratio_score,
        })
        
        # Determine rejection risk
        rejection_risk = self._calculate_rejection_risk(policy, user_profile, ped_score)
        
        # Generate reasoning
        reasoning = self._generate_policy_reasoning(
            policy,
            user_profile,
            overall_score,
            ped_score,
            cost_score,
            rejection_risk,
        )
        
        return ComparedPolicy(
            policy_id=policy.policy_id,
            policy_name=policy.policy_name,
            provider=policy.provider_id,
            overall_score=round(overall_score, 2),
            score_breakdown=PolicyScore(
                ped_compatibility=round(ped_score, 2),
                cost_effectiveness=round(cost_score, 2),
                coverage_comprehensiveness=round(coverage_score, 2),
                claim_settlement_ratio=round(claim_ratio_score, 2),
            ),
            pros=pros,
            cons=cons,
            rejection_risk=rejection_risk,
            reasoning=reasoning,
        )
    
    def _calculate_ped_compatibility_score(
        self,
        policy: PolicyDocument,
        user_profile: UserProfile,
    ) -> float:
        """
        Calculate PED compatibility score (0-100).
        
        Higher score means better compatibility with user's pre-existing diseases.
        
        Args:
            policy: Policy document
            user_profile: User profile
            
        Returns:
            Score from 0 to 100
        """
        ped_list = user_profile.get_ped_list()
        
        # If no PEDs, perfect score
        if not ped_list:
            return 100.0
        
        # Check how many PEDs are explicitly excluded
        excluded_count = 0
        for ped in ped_list:
            if policy.has_exclusion(ped):
                excluded_count += 1
        
        # Calculate score based on exclusion rate
        exclusion_rate = excluded_count / len(ped_list)
        base_score = (1 - exclusion_rate) * 100
        
        # Adjust for waiting period (longer waiting period = lower score)
        waiting_penalty = min(policy.waiting_periods.pre_existing / 3650, 0.3)  # Max 30% penalty
        adjusted_score = base_score * (1 - waiting_penalty)
        
        return max(0.0, min(100.0, adjusted_score))
    
    def _calculate_cost_effectiveness_score(
        self,
        policy: PolicyDocument,
        user_profile: UserProfile,
    ) -> float:
        """
        Calculate cost effectiveness score (0-100).
        
        Considers premium relative to coverage amount and user's age.
        
        Args:
            policy: Policy document
            user_profile: User profile
            
        Returns:
            Score from 0 to 100
        """
        # Calculate premium as percentage of coverage
        premium_ratio = policy.premium / policy.coverage_amount
        
        # Lower ratio is better (aim for < 2%)
        if premium_ratio <= 0.01:  # 1% or less
            base_score = 100.0
        elif premium_ratio <= 0.02:  # 1-2%
            base_score = 80.0
        elif premium_ratio <= 0.03:  # 2-3%
            base_score = 60.0
        elif premium_ratio <= 0.05:  # 3-5%
            base_score = 40.0
        else:  # > 5%
            base_score = 20.0
        
        # Adjust for user age (older users expect higher premiums)
        age = user_profile.demographics.age
        if age > 60:
            # More lenient for senior citizens
            base_score = min(100.0, base_score * 1.2)
        elif age < 30:
            # Expect better rates for young users
            base_score = base_score * 0.9
        
        return max(0.0, min(100.0, base_score))
    
    def _calculate_coverage_score(self, policy: PolicyDocument) -> float:
        """
        Calculate coverage comprehensiveness score (0-100).
        
        Based on number and quality of inclusions.
        
        Args:
            policy: Policy document
            
        Returns:
            Score from 0 to 100
        """
        # Base score on number of inclusions
        inclusion_count = len(policy.inclusions)
        
        if inclusion_count >= 20:
            base_score = 100.0
        elif inclusion_count >= 15:
            base_score = 85.0
        elif inclusion_count >= 10:
            base_score = 70.0
        elif inclusion_count >= 5:
            base_score = 50.0
        else:
            base_score = 30.0
        
        # Bonus for comprehensive coverage
        comprehensive_keywords = [
            'hospitalization', 'surgery', 'diagnostic', 'ambulance',
            'daycare', 'maternity', 'organ', 'transplant'
        ]
        
        coverage_text = ' '.join(policy.inclusions).lower()
        keyword_matches = sum(1 for kw in comprehensive_keywords if kw in coverage_text)
        bonus = min(15.0, keyword_matches * 2)
        
        return min(100.0, base_score + bonus)
    
    def _calculate_claim_settlement_score(self, policy: PolicyDocument) -> float:
        """
        Calculate claim settlement ratio score (0-100).
        
        In production, this would use actual claim settlement data.
        For now, we use a default score based on provider.
        
        Args:
            policy: Policy document
            
        Returns:
            Score from 0 to 100
        """
        # Default score (in production, fetch from database)
        # Most insurers have 85-95% settlement ratio
        return 85.0
    
    def _generate_pros_cons(
        self,
        policy: PolicyDocument,
        user_profile: UserProfile,
        scores: Dict[str, float],
    ) -> tuple[List[str], List[str]]:
        """
        Generate pros and cons for a policy.
        
        Args:
            policy: Policy document
            user_profile: User profile
            scores: Dictionary of scores
            
        Returns:
            Tuple of (pros list, cons list)
        """
        pros = []
        cons = []
        
        # Analyze PED compatibility
        if scores['ped'] >= 80:
            pros.append("Excellent compatibility with your pre-existing conditions")
        elif scores['ped'] >= 60:
            pros.append("Good coverage for most of your pre-existing conditions")
        elif scores['ped'] < 40:
            cons.append("Limited coverage for your pre-existing conditions")
        
        # Analyze cost
        if scores['cost'] >= 80:
            pros.append("Excellent value for money with competitive premium rates")
        elif scores['cost'] >= 60:
            pros.append("Reasonable premium for the coverage provided")
        elif scores['cost'] < 40:
            cons.append("Premium is relatively high compared to coverage amount")
        
        # Analyze coverage
        if scores['coverage'] >= 80:
            pros.append("Comprehensive coverage with wide range of inclusions")
        elif scores['coverage'] < 50:
            cons.append("Limited coverage compared to other policies")
        
        # Analyze waiting periods
        if policy.waiting_periods.general <= 30:
            pros.append("Short general waiting period")
        if policy.waiting_periods.pre_existing > 1095:  # > 3 years
            cons.append("Long waiting period for pre-existing diseases")
        
        # Coverage amount analysis
        if policy.coverage_amount >= 1000000:  # 10 lakh+
            pros.append(f"High coverage amount of Rs. {policy.coverage_amount:,.0f}")
        elif policy.coverage_amount < 300000:  # < 3 lakh
            cons.append("Coverage amount may be insufficient for major medical expenses")
        
        return pros, cons
    
    def _calculate_rejection_risk(
        self,
        policy: PolicyDocument,
        user_profile: UserProfile,
        ped_score: float,
    ) -> str:
        """
        Calculate rejection risk level.
        
        Args:
            policy: Policy document
            user_profile: User profile
            ped_score: PED compatibility score
            
        Returns:
            Risk level: 'low', 'medium', or 'high'
        """
        ped_list = user_profile.get_ped_list()
        
        # No PEDs = low risk
        if not ped_list:
            return "low"
        
        # Check for explicit exclusions
        excluded_count = sum(1 for ped in ped_list if policy.has_exclusion(ped))
        
        if excluded_count == 0:
            return "low"
        elif excluded_count < len(ped_list) / 2:
            return "medium"
        else:
            return "high"
    
    def _generate_policy_reasoning(
        self,
        policy: PolicyDocument,
        user_profile: UserProfile,
        overall_score: float,
        ped_score: float,
        cost_score: float,
        rejection_risk: str,
    ) -> str:
        """
        Generate reasoning for policy scores.
        
        Args:
            policy: Policy document
            user_profile: User profile
            overall_score: Overall policy score
            ped_score: PED compatibility score
            cost_score: Cost effectiveness score
            rejection_risk: Rejection risk level
            
        Returns:
            Reasoning text
        """
        reasoning_parts = []
        
        # Overall assessment
        if overall_score >= 80:
            reasoning_parts.append("This policy is highly suitable for your profile.")
        elif overall_score >= 60:
            reasoning_parts.append("This policy is a good match for your needs.")
        elif overall_score >= 40:
            reasoning_parts.append("This policy has moderate suitability for your profile.")
        else:
            reasoning_parts.append("This policy may not be the best fit for your needs.")
        
        # PED analysis
        ped_list = user_profile.get_ped_list()
        if ped_list:
            if ped_score >= 80:
                reasoning_parts.append(
                    f"It provides excellent coverage for your pre-existing conditions "
                    f"({', '.join(ped_list[:2])})."
                )
            elif ped_score < 40:
                reasoning_parts.append(
                    f"However, it has limited coverage for some of your pre-existing conditions."
                )
        
        # Cost analysis
        premium_ratio = (policy.premium / policy.coverage_amount) * 100
        reasoning_parts.append(
            f"The premium is {premium_ratio:.2f}% of the coverage amount "
            f"(Rs. {policy.premium:,.0f} for Rs. {policy.coverage_amount:,.0f} coverage)."
        )
        
        # Rejection risk
        if rejection_risk == "high":
            reasoning_parts.append(
                "Note: There is a high risk of application rejection due to "
                "exclusions related to your medical history."
            )
        elif rejection_risk == "medium":
            reasoning_parts.append(
                "There is a moderate risk of limitations or exclusions based on your medical history."
            )
        
        return " ".join(reasoning_parts)
    
    async def _generate_recommendations(
        self,
        compared_policies: List[ComparedPolicy],
        user_profile: UserProfile,
        language: str,
    ) -> List[str]:
        """
        Generate comprehensive policy recommendations based on user profile.
        
        This method implements the policy recommendation engine that:
        1. Ranks policies by compatibility score (already sorted by compare_plans)
        2. Filters and recommends top policies based on user profile
        3. Generates detailed recommendation reasoning
        4. Considers PED compatibility, cost, coverage, and rejection risk
        
        Args:
            compared_policies: List of compared policies (sorted by overall score)
            user_profile: User profile with medical history
            language: Target language for recommendations
            
        Returns:
            List of recommendation strings with reasoning
            
        Requirements: 2.4
        Task: 7.3 - Implement policy recommendation engine
        """
        recommendations = []
        
        if not compared_policies:
            return ["No policies available for comparison."]
        
        # Get user context
        ped_list = user_profile.get_ped_list()
        user_age = user_profile.demographics.age
        has_peds = len(ped_list) > 0
        
        # Filter top policies (score >= 60 or top 3, whichever is more)
        top_policies = [p for p in compared_policies if p.overall_score >= 60]
        if len(top_policies) < 3 and len(compared_policies) >= 3:
            top_policies = compared_policies[:3]
        elif not top_policies and compared_policies:
            top_policies = compared_policies[:1]
        
        # 1. PRIMARY RECOMMENDATION - Best overall policy
        if top_policies:
            top_policy = top_policies[0]
            primary_rec = self._generate_primary_recommendation(
                top_policy, user_profile, has_peds
            )
            recommendations.append(primary_rec)
        
        # 2. REJECTION RISK RECOMMENDATION - Lowest risk policy
        low_risk_policies = [p for p in compared_policies if p.rejection_risk == "low"]
        if low_risk_policies and has_peds:
            best_low_risk = low_risk_policies[0]
            if best_low_risk.policy_id != top_policies[0].policy_id:
                risk_rec = self._generate_risk_based_recommendation(
                    best_low_risk, ped_list
                )
                recommendations.append(risk_rec)
        
        # 3. PED COMPATIBILITY RECOMMENDATION - Best for pre-existing conditions
        if has_peds:
            best_ped_policy = max(
                compared_policies,
                key=lambda p: p.score_breakdown.ped_compatibility
            )
            if best_ped_policy.policy_id != top_policies[0].policy_id:
                ped_rec = self._generate_ped_recommendation(
                    best_ped_policy, ped_list
                )
                recommendations.append(ped_rec)
        
        # 4. COST EFFECTIVENESS RECOMMENDATION - Best value for money
        best_value_policy = max(
            compared_policies,
            key=lambda p: p.score_breakdown.cost_effectiveness
        )
        if best_value_policy.policy_id != top_policies[0].policy_id:
            value_rec = self._generate_value_recommendation(
                best_value_policy, user_age
            )
            recommendations.append(value_rec)
        
        # 5. COVERAGE RECOMMENDATION - Most comprehensive coverage
        best_coverage_policy = max(
            compared_policies,
            key=lambda p: p.score_breakdown.coverage_comprehensiveness
        )
        if (best_coverage_policy.policy_id != top_policies[0].policy_id and
            best_coverage_policy.score_breakdown.coverage_comprehensiveness >= 70):
            coverage_rec = self._generate_coverage_recommendation(
                best_coverage_policy
            )
            recommendations.append(coverage_rec)
        
        # 6. AGE-SPECIFIC RECOMMENDATIONS
        age_rec = self._generate_age_specific_recommendation(
            compared_policies, user_age, has_peds
        )
        if age_rec:
            recommendations.append(age_rec)
        
        # 7. GENERAL GUIDANCE
        general_guidance = self._generate_general_guidance(
            compared_policies, has_peds, user_age
        )
        if general_guidance:
            recommendations.append(general_guidance)
        
        # Translate if needed
        if language != "en":
            translated_recommendations = []
            for rec in recommendations:
                translated = await self.translation_service.translate(
                    text=rec,
                    source_language="en",
                    target_language=language,
                    context_type="general",
                )
                translated_recommendations.append(translated.translated_content)
            return translated_recommendations
        
        return recommendations
    
    def _generate_primary_recommendation(
        self,
        policy: ComparedPolicy,
        user_profile: UserProfile,
        has_peds: bool,
    ) -> str:
        """
        Generate primary recommendation for the top-ranked policy.
        
        Args:
            policy: Top-ranked policy
            user_profile: User profile
            has_peds: Whether user has pre-existing diseases
            
        Returns:
            Primary recommendation string with reasoning
        """
        rec_parts = [
            f"PRIMARY RECOMMENDATION: We recommend '{policy.policy_name}' from {policy.provider} "
            f"with an overall score of {policy.overall_score}/100."
        ]
        
        # Add reasoning based on strengths
        strengths = []
        if policy.score_breakdown.ped_compatibility >= 70 and has_peds:
            strengths.append(
                f"excellent compatibility with your pre-existing conditions "
                f"({policy.score_breakdown.ped_compatibility}/100)"
            )
        if policy.score_breakdown.cost_effectiveness >= 70:
            strengths.append(
                f"competitive pricing ({policy.score_breakdown.cost_effectiveness}/100)"
            )
        if policy.score_breakdown.coverage_comprehensiveness >= 70:
            strengths.append(
                f"comprehensive coverage ({policy.score_breakdown.coverage_comprehensiveness}/100)"
            )
        
        if strengths:
            rec_parts.append(
                f" This policy offers {', '.join(strengths)}."
            )
        
        # Add rejection risk context
        if policy.rejection_risk == "low":
            rec_parts.append(" Your application has a high likelihood of acceptance.")
        elif policy.rejection_risk == "medium":
            rec_parts.append(
                " Your application has moderate acceptance likelihood; "
                "ensure full disclosure of medical history."
            )
        elif policy.rejection_risk == "high":
            rec_parts.append(
                " Note: This policy may have acceptance challenges due to your medical history. "
                "Consider alternative options below."
            )
        
        return "".join(rec_parts)
    
    def _generate_risk_based_recommendation(
        self,
        policy: ComparedPolicy,
        ped_list: List[str],
    ) -> str:
        """
        Generate recommendation based on rejection risk.
        
        Args:
            policy: Low-risk policy
            ped_list: List of pre-existing diseases
            
        Returns:
            Risk-based recommendation string
        """
        return (
            f"LOWEST REJECTION RISK: '{policy.policy_name}' has the lowest rejection risk "
            f"for your profile (score: {policy.overall_score}/100). "
            f"This policy is more likely to accept applicants with pre-existing conditions like "
            f"{', '.join(ped_list[:2])}{'...' if len(ped_list) > 2 else ''}."
        )
    
    def _generate_ped_recommendation(
        self,
        policy: ComparedPolicy,
        ped_list: List[str],
    ) -> str:
        """
        Generate recommendation for best PED compatibility.
        
        Args:
            policy: Policy with best PED compatibility
            ped_list: List of pre-existing diseases
            
        Returns:
            PED-focused recommendation string
        """
        return (
            f"BEST FOR PRE-EXISTING CONDITIONS: '{policy.policy_name}' provides the best coverage "
            f"for your pre-existing conditions (PED compatibility: {policy.score_breakdown.ped_compatibility}/100). "
            f"This policy has favorable terms for conditions like {', '.join(ped_list[:2])}."
        )
    
    def _generate_value_recommendation(
        self,
        policy: ComparedPolicy,
        user_age: int,
    ) -> str:
        """
        Generate recommendation for best value.
        
        Args:
            policy: Policy with best cost effectiveness
            user_age: User's age
            
        Returns:
            Value-focused recommendation string
        """
        age_context = ""
        if user_age < 30:
            age_context = " This is particularly good value for your age group."
        elif user_age > 60:
            age_context = " This offers competitive rates for senior citizens."
        
        return (
            f"BEST VALUE FOR MONEY: '{policy.policy_name}' offers the most cost-effective coverage "
            f"(cost effectiveness: {policy.score_breakdown.cost_effectiveness}/100).{age_context}"
        )
    
    def _generate_coverage_recommendation(
        self,
        policy: ComparedPolicy,
    ) -> str:
        """
        Generate recommendation for most comprehensive coverage.
        
        Args:
            policy: Policy with best coverage
            
        Returns:
            Coverage-focused recommendation string
        """
        return (
            f"MOST COMPREHENSIVE COVERAGE: '{policy.policy_name}' provides the widest range of coverage "
            f"(coverage score: {policy.score_breakdown.coverage_comprehensiveness}/100). "
            f"Consider this if you want maximum protection across various medical scenarios."
        )
    
    def _generate_age_specific_recommendation(
        self,
        policies: List[ComparedPolicy],
        user_age: int,
        has_peds: bool,
    ) -> Optional[str]:
        """
        Generate age-specific recommendations.
        
        Args:
            policies: List of compared policies
            user_age: User's age
            has_peds: Whether user has pre-existing diseases
            
        Returns:
            Age-specific recommendation or None
        """
        if user_age < 30:
            return (
                "AGE-SPECIFIC ADVICE: At your age, prioritize policies with good coverage "
                "and reasonable premiums. You can typically get better rates now, "
                "so consider higher coverage amounts for long-term protection."
            )
        elif user_age >= 60:
            if has_peds:
                return (
                    "AGE-SPECIFIC ADVICE: As a senior citizen with pre-existing conditions, "
                    "focus on policies with shorter waiting periods and comprehensive PED coverage. "
                    "Senior citizen-specific plans may offer better terms."
                )
            else:
                return (
                    "AGE-SPECIFIC ADVICE: Consider senior citizen-specific health insurance plans "
                    "that may offer better coverage and terms for your age group."
                )
        elif 45 <= user_age < 60:
            return (
                "AGE-SPECIFIC ADVICE: At this stage, ensure adequate coverage for lifestyle diseases "
                "and consider policies with good coverage for diagnostic tests and preventive care."
            )
        
        return None
    
    def _generate_general_guidance(
        self,
        policies: List[ComparedPolicy],
        has_peds: bool,
        user_age: int,
    ) -> Optional[str]:
        """
        Generate general guidance for policy selection.
        
        Args:
            policies: List of compared policies
            has_peds: Whether user has pre-existing diseases
            user_age: User's age
            
        Returns:
            General guidance string or None
        """
        guidance_parts = ["GENERAL GUIDANCE:"]
        
        # Check if there are high-risk policies
        high_risk_count = sum(1 for p in policies if p.rejection_risk == "high")
        if high_risk_count > len(policies) / 2 and has_peds:
            guidance_parts.append(
                " Many policies show high rejection risk for your profile. "
                "Consider working with an insurance advisor who specializes in high-risk cases."
            )
        
        # General advice
        guidance_parts.append(
            " Always read the policy document carefully, especially exclusions and waiting periods."
        )
        
        if has_peds:
            guidance_parts.append(
                " Disclose all pre-existing conditions during application to avoid claim rejection later."
            )
        
        guidance_parts.append(
            " Compare multiple quotes and consider applying to 2-3 insurers to get the best offer."
        )
        
        return "".join(guidance_parts)
    
    async def analyze_ped_compatibility(
        self,
        ped_list: List[str],
        medications: List[str],
        policy_id: Optional[str] = None,
        language: str = "en",
    ) -> CompatibilityReport:
        """
        Analyze PED compatibility with insurance policies.
        
        This method:
        1. Analyzes each PED against policy exclusions
        2. Checks medications for condition implications using LLM
        3. Calculates rejection probability scores
        4. Identifies compatible policies with higher acceptance likelihood
        5. Provides detailed reasoning and recommendations
        
        Args:
            ped_list: List of pre-existing diseases
            medications: List of current medications
            policy_id: Optional specific policy to analyze (if None, analyzes all policies)
            language: Target language for results (ISO code)
            
        Returns:
            CompatibilityReport with PED analysis, rejection probability, and recommendations
            
        Raises:
            ValueError: If no policies found or invalid inputs
            
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
        """
        self._log_operation(
            "analyze_ped_compatibility",
            policy_id=policy_id,
            ped_count=len(ped_list),
            medication_count=len(medications),
            language=language,
        )
        
        try:
            # Validate inputs
            if not ped_list and not medications:
                raise ValueError(
                    "At least one pre-existing disease or medication must be provided for analysis."
                )
            
            # Step 1: Get policies to analyze
            if policy_id:
                # Analyze specific policy
                policies = await self._get_policy_by_id(policy_id)
                if not policies:
                    raise ValueError(f"Policy with ID '{policy_id}' not found.")
            else:
                # Analyze all available policies
                policies = await self._retrieve_policies(filters=None, max_policies=20)
                if not policies:
                    raise ValueError("No policies available for analysis.")
            
            self.logger.info(
                f"Analyzing PED compatibility for {len(policies)} policies",
                ped_count=len(ped_list),
                medication_count=len(medications),
            )
            
            # Step 2: Analyze medications for implied conditions
            medication_analyses = []
            if medications:
                medication_analyses = await self._analyze_medications(medications, language)
            
            # Step 3: Analyze each PED against policies
            # For single policy analysis, analyze that policy
            # For multiple policies, analyze the best-fit policy
            target_policy = policies[0] if policy_id else await self._select_best_policy_for_ped(
                policies, ped_list, medications
            )
            
            ped_analyses = await self._analyze_peds_against_policy(
                ped_list, target_policy, medication_analyses, language
            )
            
            # Step 4: Calculate overall rejection probability
            rejection_probability, rejection_explanation = self._calculate_rejection_probability(
                ped_analyses, medication_analyses, target_policy
            )
            
            # Step 5: Identify compatible policies (policies with lower rejection risk)
            compatible_policies = await self._identify_compatible_policies(
                policies, ped_list, medications, rejection_probability
            )
            
            # Step 6: Generate recommendations
            recommendations = await self._generate_ped_recommendations(
                ped_analyses,
                medication_analyses,
                rejection_probability,
                compatible_policies,
                language,
            )
            
            # Step 7: Generate overall explanation
            explanation = await self._generate_compatibility_explanation(
                ped_analyses,
                medication_analyses,
                rejection_probability,
                compatible_policies,
                language,
            )
            
            # Step 8: Extract citations
            citations = self._extract_policy_citations(policies)
            
            # Translate if needed
            if language != "en":
                rejection_explanation = await self._translate_text(rejection_explanation, language)
                explanation = await self._translate_text(explanation, language)
                recommendations = await self._translate_list(recommendations, language)
            
            # Create compatibility report
            report = CompatibilityReport(
                report_id=str(uuid.uuid4()),
                user_profile_id="",  # Will be set by caller if needed
                policy_id=policy_id,
                ped_analyses=ped_analyses,
                medication_analyses=medication_analyses,
                overall_rejection_probability=rejection_probability,
                rejection_probability_explanation=rejection_explanation,
                compatible_policies=compatible_policies,
                recommendations=recommendations,
                explanation=explanation,
                citations=citations,
                language=language,
                generated_at=datetime.now(timezone.utc),
            )
            
            self.logger.info(
                "PED compatibility analysis completed",
                rejection_probability=rejection_probability,
                compatible_policies_count=len(compatible_policies),
                language=language,
            )
            
            return report
        
        except Exception as e:
            self._log_error("analyze_ped_compatibility", e, policy_id=policy_id)
            raise
    
    async def _get_policy_by_id(self, policy_id: str) -> List[PolicyDocument]:
        """
        Retrieve a specific policy by ID.
        
        Args:
            policy_id: Policy identifier
            
        Returns:
            List containing the policy document (or empty if not found)
        """
        # Search for the specific policy
        search_results = await self.knowledge_base.search_policies(
            query=f"policy {policy_id}",
            filters={'policy_id': policy_id},
            k=1,
        )
        
        if not search_results:
            return []
        
        policy = self._create_policy_from_search_result(search_results[0])
        return [policy]
    
    async def _analyze_medications(
        self,
        medications: List[str],
        language: str,
    ) -> List[MedicationAnalysis]:
        """
        Analyze medications for implied medical conditions using LLM.
        
        Args:
            medications: List of medication names
            language: Target language
            
        Returns:
            List of medication analyses
            
        Requirements: 2.5
        """
        medication_analyses = []
        
        for medication in medications:
            # Use LLM to analyze medication implications
            prompt = f"""Analyze the medication "{medication}" and identify:
1. What medical conditions this medication is typically prescribed for
2. How this medication might affect insurance policy acceptance
3. The risk level (low, medium, high) for policy rejection based on this medication

Provide a concise analysis focusing on insurance implications."""
            
            try:
                response = await self.llm_engine.generate_response(
                    prompt=prompt,
                    context="",
                    language="en",  # Always analyze in English first
                )
                
                # Parse LLM response to extract information
                implied_conditions = self._extract_implied_conditions(response.content)
                impact = self._extract_impact_statement(response.content, medication)
                risk_level = self._extract_risk_level(response.content)
                
                analysis = MedicationAnalysis(
                    medication=medication,
                    implied_conditions=implied_conditions,
                    impact_on_acceptance=impact,
                    risk_level=risk_level,
                )
                
                medication_analyses.append(analysis)
                
            except Exception as e:
                self.logger.warning(
                    f"Failed to analyze medication '{medication}': {e}",
                    medication=medication,
                )
                # Provide default analysis
                medication_analyses.append(
                    MedicationAnalysis(
                        medication=medication,
                        implied_conditions=["Chronic condition (specific condition unknown)"],
                        impact_on_acceptance=f"Medication {medication} may indicate a chronic condition that could affect policy acceptance.",
                        risk_level="medium",
                    )
                )
        
        return medication_analyses
    
    def _extract_implied_conditions(self, llm_response: str) -> List[str]:
        """Extract implied medical conditions from LLM response."""
        conditions = []
        
        # Look for common patterns in LLM responses
        lines = llm_response.lower().split('\n')
        for line in lines:
            if 'prescribed for' in line or 'used to treat' in line or 'condition' in line:
                # Extract condition names (simplified extraction)
                if 'diabetes' in line:
                    conditions.append("Diabetes")
                if 'hypertension' in line or 'blood pressure' in line:
                    conditions.append("Hypertension")
                if 'heart' in line or 'cardiac' in line:
                    conditions.append("Cardiac condition")
                if 'asthma' in line or 'respiratory' in line:
                    conditions.append("Respiratory condition")
                if 'thyroid' in line:
                    conditions.append("Thyroid disorder")
                if 'cholesterol' in line:
                    conditions.append("High cholesterol")
        
        # If no specific conditions found, provide generic
        if not conditions:
            conditions.append("Chronic medical condition")
        
        return conditions
    
    def _extract_impact_statement(self, llm_response: str, medication: str) -> str:
        """Extract impact statement from LLM response."""
        # Look for impact-related sentences
        lines = llm_response.split('.')
        for line in lines:
            if 'insurance' in line.lower() or 'policy' in line.lower() or 'acceptance' in line.lower():
                return line.strip()
        
        # Default statement
        return f"This medication may indicate a pre-existing condition that could affect policy acceptance and waiting periods."
    
    def _extract_risk_level(self, llm_response: str) -> str:
        """Extract risk level from LLM response."""
        response_lower = llm_response.lower()
        
        if 'high risk' in response_lower or 'significant risk' in response_lower:
            return "high"
        elif 'low risk' in response_lower or 'minimal risk' in response_lower:
            return "low"
        else:
            return "medium"
    
    async def _select_best_policy_for_ped(
        self,
        policies: List[PolicyDocument],
        ped_list: List[str],
        medications: List[str],
    ) -> PolicyDocument:
        """
        Select the best policy for PED analysis from available policies.
        
        Args:
            policies: List of available policies
            ped_list: List of pre-existing diseases
            medications: List of medications
            
        Returns:
            Best policy for analysis
        """
        # Score each policy based on PED compatibility
        best_policy = None
        best_score = -1
        
        for policy in policies:
            # Count how many PEDs are NOT excluded
            non_excluded_count = sum(
                1 for ped in ped_list if not policy.has_exclusion(ped)
            )
            
            # Calculate simple compatibility score
            if ped_list:
                score = non_excluded_count / len(ped_list)
            else:
                score = 1.0
            
            if score > best_score:
                best_score = score
                best_policy = policy
        
        return best_policy or policies[0]
    
    async def _analyze_peds_against_policy(
        self,
        ped_list: List[str],
        policy: PolicyDocument,
        medication_analyses: List[MedicationAnalysis],
        language: str,
    ) -> List[PEDAnalysis]:
        """
        Analyze each PED against a specific policy.
        
        Args:
            ped_list: List of pre-existing diseases
            policy: Policy to analyze against
            medication_analyses: Medication analysis results
            language: Target language
            
        Returns:
            List of PED analyses
            
        Requirements: 2.1, 2.2
        """
        ped_analyses = []
        
        # Add PEDs from medication implications
        implied_peds = set()
        for med_analysis in medication_analyses:
            implied_peds.update(med_analysis.implied_conditions)
        
        # Combine explicit PEDs and implied PEDs
        all_peds = set(ped_list) | implied_peds
        
        for ped in all_peds:
            # Check if condition is explicitly excluded
            is_excluded = policy.has_exclusion(ped)
            
            # Determine waiting period
            waiting_period = None
            if not is_excluded:
                # Check for specific waiting period
                for specific in policy.waiting_periods.specific_conditions:
                    if ped.lower() in specific.condition.lower():
                        waiting_period = specific.days
                        break
                
                # Use general PED waiting period if no specific period
                if waiting_period is None:
                    waiting_period = policy.waiting_periods.pre_existing
            
            # Generate coverage details
            if is_excluded:
                coverage_details = f"This condition is explicitly excluded from coverage under this policy."
            elif waiting_period:
                coverage_details = (
                    f"This condition will be covered after a waiting period of {waiting_period} days "
                    f"({waiting_period // 365} years, {waiting_period % 365} days)."
                )
            else:
                coverage_details = "This condition is covered under the policy."
            
            # Determine rejection risk
            if is_excluded:
                rejection_risk = "high"
            elif waiting_period and waiting_period > 1095:  # > 3 years
                rejection_risk = "medium"
            else:
                rejection_risk = "low"
            
            analysis = PEDAnalysis(
                condition=ped,
                is_excluded=is_excluded,
                waiting_period_days=waiting_period,
                coverage_details=coverage_details,
                rejection_risk=rejection_risk,
            )
            
            ped_analyses.append(analysis)
        
        return ped_analyses
    
    def _calculate_rejection_probability(
        self,
        ped_analyses: List[PEDAnalysis],
        medication_analyses: List[MedicationAnalysis],
        policy: PolicyDocument,
    ) -> tuple[float, str]:
        """
        Calculate overall rejection probability and explanation.
        
        Args:
            ped_analyses: List of PED analyses
            medication_analyses: List of medication analyses
            policy: Policy being analyzed
            
        Returns:
            Tuple of (rejection probability 0-1, explanation text)
            
        Requirements: 2.3
        """
        if not ped_analyses and not medication_analyses:
            return 0.0, "No pre-existing conditions or medications to analyze. Low rejection risk."
        
        # Count risk factors
        high_risk_peds = sum(1 for ped in ped_analyses if ped.rejection_risk == "high")
        medium_risk_peds = sum(1 for ped in ped_analyses if ped.rejection_risk == "medium")
        high_risk_meds = sum(1 for med in medication_analyses if med.risk_level == "high")
        medium_risk_meds = sum(1 for med in medication_analyses if med.risk_level == "medium")
        
        total_conditions = len(ped_analyses)
        excluded_count = sum(1 for ped in ped_analyses if ped.is_excluded)
        
        # Calculate base probability
        if total_conditions == 0:
            base_probability = 0.2  # Some risk from medications
        else:
            exclusion_rate = excluded_count / total_conditions
            base_probability = exclusion_rate * 0.7  # Excluded conditions contribute 70% weight
        
        # Adjust for medication risks
        medication_adjustment = (high_risk_meds * 0.15) + (medium_risk_meds * 0.08)
        
        # Adjust for medium-risk PEDs
        medium_risk_adjustment = (medium_risk_peds / max(total_conditions, 1)) * 0.2
        
        # Calculate final probability
        rejection_probability = min(1.0, base_probability + medication_adjustment + medium_risk_adjustment)
        
        # Generate explanation
        explanation_parts = []
        
        if excluded_count > 0:
            explanation_parts.append(
                f"{excluded_count} of your pre-existing conditions are explicitly excluded by this policy, "
                f"which significantly increases rejection risk."
            )
        
        if high_risk_peds > 0:
            explanation_parts.append(
                f"{high_risk_peds} condition(s) have high rejection risk due to policy exclusions."
            )
        
        if medium_risk_peds > 0:
            explanation_parts.append(
                f"{medium_risk_peds} condition(s) have medium rejection risk due to long waiting periods "
                f"(typically {policy.waiting_periods.pre_existing} days)."
            )
        
        if high_risk_meds > 0:
            explanation_parts.append(
                f"{high_risk_meds} of your medications indicate conditions that may affect policy acceptance."
            )
        
        if rejection_probability < 0.3:
            explanation_parts.append(
                "Overall, your profile has a low rejection risk for this policy."
            )
        elif rejection_probability < 0.6:
            explanation_parts.append(
                "Overall, your profile has a moderate rejection risk. "
                "Consider policies with better PED coverage."
            )
        else:
            explanation_parts.append(
                "Overall, your profile has a high rejection risk for this policy. "
                "We strongly recommend exploring alternative policies."
            )
        
        explanation = " ".join(explanation_parts)
        
        return rejection_probability, explanation
    
    async def _identify_compatible_policies(
        self,
        policies: List[PolicyDocument],
        ped_list: List[str],
        medications: List[str],
        current_rejection_prob: float,
    ) -> List[CompatiblePolicy]:
        """
        Identify policies with higher acceptance likelihood.
        
        Args:
            policies: List of available policies
            ped_list: List of pre-existing diseases
            medications: List of medications
            current_rejection_prob: Current rejection probability
            
        Returns:
            List of compatible policies
            
        Requirements: 2.4
        """
        compatible_policies = []
        
        for policy in policies:
            # Calculate compatibility score for this policy
            excluded_count = sum(1 for ped in ped_list if policy.has_exclusion(ped))
            
            if not ped_list:
                compatibility_score = 100.0
                acceptance_likelihood = "high"
            else:
                # Score based on non-excluded conditions
                non_excluded_rate = 1 - (excluded_count / len(ped_list))
                compatibility_score = non_excluded_rate * 100
                
                # Adjust for waiting periods
                if policy.waiting_periods.pre_existing > 1095:  # > 3 years
                    compatibility_score *= 0.85
                
                # Determine acceptance likelihood
                if compatibility_score >= 80:
                    acceptance_likelihood = "high"
                elif compatibility_score >= 50:
                    acceptance_likelihood = "medium"
                else:
                    acceptance_likelihood = "low"
            
            # Only include policies better than current
            if compatibility_score >= (1 - current_rejection_prob) * 100:
                # Generate key benefits
                key_benefits = []
                if excluded_count == 0:
                    key_benefits.append("No exclusions for your pre-existing conditions")
                elif excluded_count < len(ped_list):
                    key_benefits.append(f"Covers {len(ped_list) - excluded_count} of your {len(ped_list)} conditions")
                
                if policy.waiting_periods.pre_existing <= 730:  # <= 2 years
                    key_benefits.append(f"Reasonable waiting period of {policy.waiting_periods.pre_existing} days")
                
                if policy.coverage_amount >= 500000:
                    key_benefits.append(f"Good coverage amount of Rs. {policy.coverage_amount:,.0f}")
                
                # Generate limitations
                limitations = []
                if excluded_count > 0:
                    limitations.append(f"{excluded_count} of your conditions are excluded")
                
                if policy.waiting_periods.pre_existing > 1095:
                    limitations.append(f"Long waiting period of {policy.waiting_periods.pre_existing} days for PEDs")
                
                compatible_policy = CompatiblePolicy(
                    policy_id=policy.policy_id,
                    policy_name=policy.policy_name,
                    provider=policy.provider_id,
                    compatibility_score=round(compatibility_score, 2),
                    acceptance_likelihood=acceptance_likelihood,
                    key_benefits=key_benefits if key_benefits else ["Standard coverage available"],
                    limitations=limitations if limitations else ["Standard policy terms apply"],
                )
                
                compatible_policies.append(compatible_policy)
        
        # Sort by compatibility score
        compatible_policies.sort(key=lambda p: p.compatibility_score, reverse=True)
        
        # Return top 5
        return compatible_policies[:5]
    
    async def _generate_ped_recommendations(
        self,
        ped_analyses: List[PEDAnalysis],
        medication_analyses: List[MedicationAnalysis],
        rejection_probability: float,
        compatible_policies: List[CompatiblePolicy],
        language: str,
    ) -> List[str]:
        """
        Generate recommendations for improving acceptance chances.
        
        Args:
            ped_analyses: PED analyses
            medication_analyses: Medication analyses
            rejection_probability: Overall rejection probability
            compatible_policies: Compatible policies
            language: Target language
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # High rejection risk recommendations
        if rejection_probability >= 0.6:
            recommendations.append(
                "Consider applying to policies that explicitly cover your pre-existing conditions."
            )
            
            if compatible_policies:
                top_policy = compatible_policies[0]
                recommendations.append(
                    f"We recommend '{top_policy.policy_name}' from {top_policy.provider} "
                    f"with {top_policy.compatibility_score:.0f}% compatibility with your profile."
                )
        
        # Excluded conditions recommendations
        excluded_peds = [ped for ped in ped_analyses if ped.is_excluded]
        if excluded_peds:
            recommendations.append(
                f"Avoid policies that exclude {', '.join([ped.condition for ped in excluded_peds[:2]])}. "
                f"Look for policies with comprehensive PED coverage."
            )
        
        # Waiting period recommendations
        long_waiting_peds = [ped for ped in ped_analyses if ped.waiting_period_days and ped.waiting_period_days > 1095]
        if long_waiting_peds:
            recommendations.append(
                "Consider policies with shorter waiting periods for pre-existing diseases (2 years or less)."
            )
        
        # Medication-based recommendations
        high_risk_meds = [med for med in medication_analyses if med.risk_level == "high"]
        if high_risk_meds:
            recommendations.append(
                "Disclose all medications during application to avoid claim rejection later. "
                "Some insurers offer better terms for well-managed chronic conditions."
            )
        
        # General recommendations
        if rejection_probability < 0.3:
            recommendations.append(
                "Your profile has good acceptance chances. Apply to multiple insurers to compare offers."
            )
        
        recommendations.append(
            "Always read the policy document carefully, especially the exclusions and waiting period clauses."
        )
        
        return recommendations
    
    async def _generate_compatibility_explanation(
        self,
        ped_analyses: List[PEDAnalysis],
        medication_analyses: List[MedicationAnalysis],
        rejection_probability: float,
        compatible_policies: List[CompatiblePolicy],
        language: str,
    ) -> str:
        """
        Generate overall explanation of compatibility analysis.
        
        Args:
            ped_analyses: PED analyses
            medication_analyses: Medication analyses
            rejection_probability: Overall rejection probability
            compatible_policies: Compatible policies
            language: Target language
            
        Returns:
            Explanation text
        """
        explanation_parts = []
        
        # Summary
        explanation_parts.append(
            f"We analyzed {len(ped_analyses)} pre-existing conditions and {len(medication_analyses)} medications "
            f"against available insurance policies. "
        )
        
        # Rejection probability
        rejection_pct = rejection_probability * 100
        explanation_parts.append(
            f"Based on your medical profile, the overall rejection probability is {rejection_pct:.1f}%. "
        )
        
        # Excluded conditions
        excluded_count = sum(1 for ped in ped_analyses if ped.is_excluded)
        if excluded_count > 0:
            explanation_parts.append(
                f"{excluded_count} of your conditions are commonly excluded by insurance policies, "
                f"which increases the rejection risk. "
            )
        
        # Compatible policies
        if compatible_policies:
            high_acceptance = [p for p in compatible_policies if p.acceptance_likelihood == "high"]
            if high_acceptance:
                explanation_parts.append(
                    f"However, we found {len(high_acceptance)} policies with high acceptance likelihood for your profile. "
                )
            else:
                explanation_parts.append(
                    f"We found {len(compatible_policies)} policies that may accept your application with certain conditions. "
                )
        
        # Medication implications
        if medication_analyses:
            explanation_parts.append(
                f"Your medications indicate chronic conditions that insurers will consider during underwriting. "
                f"Full disclosure is essential to avoid claim rejection later. "
            )
        
        return "".join(explanation_parts)
    
    async def _translate_text(self, text: str, language: str) -> str:
        """Translate text to target language."""
        if language == "en":
            return text
        
        try:
            translated = await self.translation_service.translate(
                text=text,
                source_language="en",
                target_language=language,
                context_type="general",
            )
            return translated.translated_content
        except Exception as e:
            self.logger.warning(f"Translation failed: {e}")
            return text
    
    async def explain_policy(
        self,
        policy_id: str,
        language: str = "en",
    ) -> PolicyExplanation:
        """
        Explain a policy document in simple, everyday language.
        
        This method:
        1. Retrieves the policy document from knowledge base
        2. Parses and extracts key clauses (inclusions, exclusions, waiting periods)
        3. Simplifies complex insurance terminology using LLM
        4. Identifies hidden or easily missed clauses
        5. Translates explanations to requested language
        
        Args:
            policy_id: Policy identifier
            language: Target language for explanations (ISO code)
            
        Returns:
            PolicyExplanation with simplified terms and key clauses
            
        Raises:
            ValueError: If policy not found
            
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        """
        self._log_operation(
            "explain_policy",
            policy_id=policy_id,
            language=language,
        )
        
        try:
            # Step 1: Retrieve policy document
            policies = await self._get_policy_by_id(policy_id)
            if not policies:
                raise ValueError(f"Policy with ID '{policy_id}' not found.")
            
            policy = policies[0]
            
            self.logger.info(
                f"Explaining policy: {policy.policy_name}",
                policy_id=policy_id,
                language=language,
            )
            
            # Step 2: Extract and explain inclusions
            inclusions = await self._explain_inclusions(policy, language)
            
            # Step 3: Extract and explain exclusions
            exclusions = await self._explain_exclusions(policy, language)
            
            # Step 4: Extract and explain waiting periods
            waiting_periods = await self._explain_waiting_periods(policy, language)
            
            # Step 5: Extract and explain coverage limits
            coverage_limits = await self._explain_coverage_limits(policy, language)
            
            # Step 6: Identify and explain hidden clauses
            hidden_clauses = await self._identify_hidden_clauses(policy, language)
            
            # Step 7: Generate overall summary
            summary = await self._generate_policy_summary(
                policy, inclusions, exclusions, waiting_periods, language
            )
            
            # Step 8: Generate key benefits and limitations
            key_benefits = self._extract_key_benefits(policy, inclusions)
            key_limitations = self._extract_key_limitations(policy, exclusions, waiting_periods)
            
            # Step 9: Generate important notes
            important_notes = self._generate_important_notes(
                policy, exclusions, hidden_clauses, waiting_periods
            )
            
            # Step 10: Generate detailed explanation
            explanation = await self._generate_detailed_explanation(
                policy, inclusions, exclusions, hidden_clauses, language
            )
            
            # Step 11: Extract citations
            citations = [
                f"Policy Document: {policy.policy_name} (ID: {policy.policy_id})",
                f"Provider: {policy.provider_id}",
                f"Version: {policy.version}",
                f"Effective Date: {policy.effective_date}",
            ]
            
            # Step 12: Create policy explanation
            policy_explanation = PolicyExplanation(
                explanation_id=str(uuid.uuid4()),
                policy_id=policy.policy_id,
                policy_name=policy.policy_name,
                provider=policy.provider_id,
                inclusions=inclusions,
                exclusions=exclusions,
                waiting_periods=waiting_periods,
                coverage_limits=coverage_limits,
                hidden_clauses=hidden_clauses,
                summary=summary,
                key_benefits=key_benefits,
                key_limitations=key_limitations,
                important_notes=important_notes,
                explanation=explanation,
                citations=citations,
                language=language,
                generated_at=datetime.now(timezone.utc),
            )
            
            self.logger.info(
                "Policy explanation completed",
                policy_id=policy_id,
                inclusions_count=len(inclusions),
                exclusions_count=len(exclusions),
                hidden_clauses_count=len(hidden_clauses),
                language=language,
            )
            
            return policy_explanation
        
        except Exception as e:
            self._log_error("explain_policy", e, policy_id=policy_id)
            raise

    async def _translate_list(self, items: List[str], language: str) -> List[str]:
        """Translate list of strings to target language."""
        if language == "en":
            return items
        
        translated_items = []
        for item in items:
            translated = await self._translate_text(item, language)
            translated_items.append(translated)
        
        return translated_items
    
    async def _generate_recommendations(
        self,
        compared_policies: List[ComparedPolicy],
        user_profile: UserProfile,
        language: str,
    ) -> List[str]:
        """
        Generate overall recommendations based on compared policies.
        
        Args:
            compared_policies: List of compared policies
            user_profile: User profile
            language: Target language
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if not compared_policies:
            return ["No policies available for comparison."]
        
        # Top policy recommendation
        top_policy = compared_policies[0]
        recommendations.append(
            f"We recommend '{top_policy.policy_name}' from {top_policy.provider} "
            f"with an overall score of {top_policy.overall_score}/100."
        )
        
        # Low risk policies
        low_risk_policies = [p for p in compared_policies if p.rejection_risk == "low"]
        if low_risk_policies and low_risk_policies[0].policy_id != top_policy.policy_id:
            recommendations.append(
                f"For lowest rejection risk, consider '{low_risk_policies[0].policy_name}'."
            )
        
        # Best value recommendation
        best_value = max(compared_policies, key=lambda p: p.score_breakdown.cost_effectiveness)
        if best_value.policy_id != top_policy.policy_id:
            recommendations.append(
                f"For best value for money, '{best_value.policy_name}' offers competitive pricing."
            )
        
        # PED-specific recommendation
        ped_list = user_profile.get_ped_list()
        if ped_list:
            best_ped = max(compared_policies, key=lambda p: p.score_breakdown.ped_compatibility)
            if best_ped.policy_id != top_policy.policy_id:
                recommendations.append(
                    f"For best coverage of your pre-existing conditions, "
                    f"consider '{best_ped.policy_name}'."
                )
        
        # Translate if needed
        if language != "en":
            translated_recommendations = []
            for rec in recommendations:
                translated = await self.translation_service.translate(
                    text=rec,
                    source_language="en",
                    target_language=language,
                    context_type="general",
                )
                translated_recommendations.append(translated.translated_content)
            return translated_recommendations
        
        return recommendations
    
    async def _generate_comparison_explanation(
        self,
        compared_policies: List[ComparedPolicy],
        user_profile: UserProfile,
        language: str,
    ) -> str:
        """
        Generate overall explanation of comparison results.
        
        Args:
            compared_policies: List of compared policies
            user_profile: User profile
            language: Target language
            
        Returns:
            Explanation text
        """
        explanation_parts = []
        
        explanation_parts.append(
            f"We compared {len(compared_policies)} insurance policies based on your profile. "
        )
        
        # Scoring methodology
        explanation_parts.append(
            "Each policy was scored on four factors: "
            "PED compatibility (40%), cost effectiveness (30%), "
            "coverage comprehensiveness (20%), and claim settlement ratio (10%). "
        )
        
        # User-specific factors
        ped_list = user_profile.get_ped_list()
        if ped_list:
            explanation_parts.append(
                f"Your pre-existing conditions ({', '.join(ped_list[:3])}) "
                f"were carefully considered in the compatibility analysis. "
            )
        
        # Top policies summary
        if len(compared_policies) >= 3:
            top_3 = compared_policies[:3]
            explanation_parts.append(
                f"The top three policies are: "
                f"1) {top_3[0].policy_name} ({top_3[0].overall_score}/100), "
                f"2) {top_3[1].policy_name} ({top_3[1].overall_score}/100), "
                f"3) {top_3[2].policy_name} ({top_3[2].overall_score}/100). "
            )
        
        explanation = "".join(explanation_parts)
        
        # Translate if needed
        if language != "en":
            translated = await self.translation_service.translate(
                text=explanation,
                source_language="en",
                target_language=language,
                context_type="general",
            )
            return translated.translated_content
        
        return explanation
    
    def _extract_policy_citations(self, policies: List[PolicyDocument]) -> List[str]:
        """
        Extract citations from policies.
        
        Args:
            policies: List of policy documents
            
        Returns:
            List of citation strings
        """
        citations = []
        
        for policy in policies:
            citation = (
                f"Policy: {policy.policy_name} (ID: {policy.policy_id}), "
                f"Provider: {policy.provider_id}, Version: {policy.version}"
            )
            citations.append(citation)
        
        return citations

    async def _explain_inclusions(
        self,
        policy: PolicyDocument,
        language: str,
    ) -> List[PolicyClause]:
        """
        Extract and explain policy inclusions (what IS covered).
        
        Args:
            policy: Policy document
            language: Target language
            
        Returns:
            List of PolicyClause objects for inclusions
            
        Requirements: 3.1, 3.4
        """
        inclusion_clauses = []
        
        for inclusion in policy.inclusions:
            # Use LLM to simplify the inclusion
            prompt = f"""Explain this insurance policy inclusion in simple, everyday language:

Inclusion: "{inclusion}"

Provide:
1. A simple explanation (2-3 sentences) that anyone can understand
2. How this affects claims (what situations this covers)

Keep it concise and clear."""
            
            try:
                response = await self.llm_engine.generate_response(
                    prompt=prompt,
                    context=f"Policy: {policy.policy_name}\nCoverage: Rs. {policy.coverage_amount:,.0f}",
                    language="en",
                )
                
                # Parse response
                simplified = self._extract_simplified_explanation(response.content)
                impact = self._extract_impact_explanation(response.content)
                
                # Determine importance
                importance = self._determine_clause_importance(inclusion, "inclusion")
                
                clause = PolicyClause(
                    clause_type="inclusion",
                    original_text=inclusion,
                    simplified_explanation=simplified,
                    importance=importance,
                    impact_on_claims=impact,
                )
                
                inclusion_clauses.append(clause)
                
            except Exception as e:
                self.logger.warning(f"Failed to explain inclusion '{inclusion}': {e}")
                # Provide default explanation
                inclusion_clauses.append(
                    PolicyClause(
                        clause_type="inclusion",
                        original_text=inclusion,
                        simplified_explanation=f"This policy covers {inclusion.lower()}.",
                        importance="important",
                        impact_on_claims=f"Claims related to {inclusion.lower()} will be considered for coverage.",
                    )
                )
        
        return inclusion_clauses
    
    async def _explain_exclusions(
        self,
        policy: PolicyDocument,
        language: str,
    ) -> List[PolicyClause]:
        """
        Extract and explain policy exclusions (what is NOT covered).
        
        Args:
            policy: Policy document
            language: Target language
            
        Returns:
            List of PolicyClause objects for exclusions
            
        Requirements: 3.1, 3.3
        """
        exclusion_clauses = []
        
        for exclusion in policy.exclusions:
            # Use LLM to simplify the exclusion
            prompt = f"""Explain this insurance policy exclusion in simple, everyday language:

Exclusion: "{exclusion}"

Provide:
1. A simple explanation (2-3 sentences) of what is NOT covered
2. Why claims related to this will be rejected

Be clear and direct about what policyholders cannot claim."""
            
            try:
                response = await self.llm_engine.generate_response(
                    prompt=prompt,
                    context=f"Policy: {policy.policy_name}",
                    language="en",
                )
                
                # Parse response
                simplified = self._extract_simplified_explanation(response.content)
                impact = self._extract_impact_explanation(response.content)
                
                # Exclusions are typically critical
                importance = "critical"
                
                clause = PolicyClause(
                    clause_type="exclusion",
                    original_text=exclusion,
                    simplified_explanation=simplified,
                    importance=importance,
                    impact_on_claims=impact,
                )
                
                exclusion_clauses.append(clause)
                
            except Exception as e:
                self.logger.warning(f"Failed to explain exclusion '{exclusion}': {e}")
                # Provide default explanation
                exclusion_clauses.append(
                    PolicyClause(
                        clause_type="exclusion",
                        original_text=exclusion,
                        simplified_explanation=f"This policy does NOT cover {exclusion.lower()}.",
                        importance="critical",
                        impact_on_claims=f"Claims for {exclusion.lower()} will be rejected.",
                    )
                )
        
        return exclusion_clauses
    
    async def _explain_waiting_periods(
        self,
        policy: PolicyDocument,
        language: str,
    ) -> List[PolicyClause]:
        """
        Extract and explain waiting period clauses.
        
        Args:
            policy: Policy document
            language: Target language
            
        Returns:
            List of PolicyClause objects for waiting periods
            
        Requirements: 3.1
        """
        waiting_period_clauses = []
        
        # General waiting period
        if policy.waiting_periods.general > 0:
            days = policy.waiting_periods.general
            years = days // 365
            remaining_days = days % 365
            
            if years > 0:
                period_text = f"{years} year(s) and {remaining_days} day(s)" if remaining_days > 0 else f"{years} year(s)"
            else:
                period_text = f"{days} day(s)"
            
            clause = PolicyClause(
                clause_type="waiting_period",
                original_text=f"General waiting period: {days} days",
                simplified_explanation=(
                    f"You must wait {period_text} after buying this policy before you can make claims "
                    f"for most medical treatments."
                ),
                importance="critical",
                impact_on_claims=(
                    f"Any claims made within the first {period_text} will be rejected, "
                    f"except for accidental injuries."
                ),
            )
            waiting_period_clauses.append(clause)
        
        # Pre-existing disease waiting period
        if policy.waiting_periods.pre_existing > 0:
            days = policy.waiting_periods.pre_existing
            years = days // 365
            remaining_days = days % 365
            
            if years > 0:
                period_text = f"{years} year(s) and {remaining_days} day(s)" if remaining_days > 0 else f"{years} year(s)"
            else:
                period_text = f"{days} day(s)"
            
            clause = PolicyClause(
                clause_type="waiting_period",
                original_text=f"Pre-existing disease waiting period: {days} days",
                simplified_explanation=(
                    f"If you have any pre-existing medical conditions, you must wait {period_text} "
                    f"before you can claim for treatments related to those conditions."
                ),
                importance="critical",
                impact_on_claims=(
                    f"Claims for pre-existing diseases made within {period_text} will be rejected."
                ),
            )
            waiting_period_clauses.append(clause)
        
        # Specific condition waiting periods
        for specific in policy.waiting_periods.specific_conditions:
            days = specific.days
            years = days // 365
            remaining_days = days % 365
            
            if years > 0:
                period_text = f"{years} year(s) and {remaining_days} day(s)" if remaining_days > 0 else f"{years} year(s)"
            else:
                period_text = f"{days} day(s)"
            
            clause = PolicyClause(
                clause_type="waiting_period",
                original_text=f"Waiting period for {specific.condition}: {days} days",
                simplified_explanation=(
                    f"For {specific.condition}, you must wait {period_text} before making claims."
                ),
                importance="important",
                impact_on_claims=(
                    f"Claims for {specific.condition} made within {period_text} will be rejected."
                ),
            )
            waiting_period_clauses.append(clause)
        
        return waiting_period_clauses
    
    async def _explain_coverage_limits(
        self,
        policy: PolicyDocument,
        language: str,
    ) -> List[PolicyClause]:
        """
        Extract and explain coverage limits and sub-limits.
        
        Args:
            policy: Policy document
            language: Target language
            
        Returns:
            List of PolicyClause objects for coverage limits
            
        Requirements: 3.1
        """
        coverage_limit_clauses = []
        
        # Main coverage limit
        clause = PolicyClause(
            clause_type="coverage_limit",
            original_text=f"Sum Insured: Rs. {policy.coverage_amount:,.0f}",
            simplified_explanation=(
                f"The maximum amount this policy will pay for all your medical expenses in a year "
                f"is Rs. {policy.coverage_amount:,.0f}."
            ),
            importance="critical",
            impact_on_claims=(
                f"If your total medical bills exceed Rs. {policy.coverage_amount:,.0f} in a year, "
                f"you will have to pay the extra amount yourself."
            ),
        )
        coverage_limit_clauses.append(clause)
        
        # Room rent limits (common sub-limit)
        # In a real implementation, this would be extracted from policy document
        # For now, we'll add a typical room rent limit
        room_rent_limit_pct = 1.0  # 1% of sum insured is typical
        room_rent_limit = policy.coverage_amount * room_rent_limit_pct / 100
        
        clause = PolicyClause(
            clause_type="coverage_limit",
            original_text=f"Room rent limit: {room_rent_limit_pct}% of sum insured",
            simplified_explanation=(
                f"The policy will pay up to Rs. {room_rent_limit:,.0f} per day for your hospital room. "
                f"If you choose a more expensive room, you'll pay the difference."
            ),
            importance="important",
            impact_on_claims=(
                f"If your room costs more than Rs. {room_rent_limit:,.0f} per day, "
                f"the insurance company may reduce your entire claim proportionally."
            ),
        )
        coverage_limit_clauses.append(clause)
        
        return coverage_limit_clauses
    
    async def _identify_hidden_clauses(
        self,
        policy: PolicyDocument,
        language: str,
    ) -> List[PolicyClause]:
        """
        Identify hidden or easily missed clauses that affect claims.
        
        Args:
            policy: Policy document
            language: Target language
            
        Returns:
            List of PolicyClause objects for hidden clauses
            
        Requirements: 3.5
        """
        hidden_clauses = []
        
        # Use LLM to identify hidden clauses from policy text
        prompt = f"""Analyze this insurance policy and identify any hidden or easily missed clauses that could affect claims:

Policy: {policy.policy_name}
Full Text: {policy.full_text[:2000]}...

Identify 2-3 clauses that:
1. Are buried in fine print
2. Could surprise policyholders when making claims
3. Have significant impact on claim acceptance

For each clause, explain:
- What the clause says
- Why it's easily missed
- How it affects claims"""
        
        try:
            response = await self.llm_engine.generate_response(
                prompt=prompt,
                context="",
                language="en",
            )
            
            # Parse response to extract hidden clauses
            # This is a simplified extraction - in production, use more sophisticated parsing
            content = response.content
            
            # Look for common hidden clauses
            if "co-payment" in content.lower() or "copay" in content.lower():
                hidden_clauses.append(
                    PolicyClause(
                        clause_type="hidden",
                        original_text="Co-payment clause",
                        simplified_explanation=(
                            "You may have to pay a percentage (typically 10-20%) of every claim yourself, "
                            "even if the claim is approved. This is called co-payment."
                        ),
                        importance="critical",
                        impact_on_claims=(
                            "Even approved claims will require you to pay a portion out of pocket."
                        ),
                    )
                )
            
            if "proportionate deduction" in content.lower() or "room rent" in content.lower():
                hidden_clauses.append(
                    PolicyClause(
                        clause_type="hidden",
                        original_text="Proportionate deduction clause",
                        simplified_explanation=(
                            "If you exceed the room rent limit, the insurance company may reduce "
                            "your ENTIRE claim proportionally, not just the room charges."
                        ),
                        importance="critical",
                        impact_on_claims=(
                            "Choosing a room above the limit can reduce your entire claim by 20-40%."
                        ),
                    )
                )
            
            if "sublimit" in content.lower() or "sub-limit" in content.lower():
                hidden_clauses.append(
                    PolicyClause(
                        clause_type="hidden",
                        original_text="Disease-specific sub-limits",
                        simplified_explanation=(
                            "Certain diseases (like cataract, hernia, joint replacement) may have "
                            "lower coverage limits than the main sum insured."
                        ),
                        importance="important",
                        impact_on_claims=(
                            "Even if your sum insured is high, specific treatments may have much lower limits."
                        ),
                    )
                )
            
        except Exception as e:
            self.logger.warning(f"Failed to identify hidden clauses: {e}")
            # Provide common hidden clauses as default
            hidden_clauses.append(
                PolicyClause(
                    clause_type="hidden",
                    original_text="Claim documentation requirements",
                    simplified_explanation=(
                        "You must submit all required documents within a specific timeframe "
                        "(usually 30 days) or your claim may be rejected."
                    ),
                    importance="critical",
                    impact_on_claims=(
                        "Late submission of documents can lead to claim rejection, "
                        "even if the treatment is covered."
                    ),
                )
            )
        
        return hidden_clauses
    
    async def _generate_policy_summary(
        self,
        policy: PolicyDocument,
        inclusions: List[PolicyClause],
        exclusions: List[PolicyClause],
        waiting_periods: List[PolicyClause],
        language: str,
    ) -> str:
        """
        Generate overall policy summary in simple language.
        
        Args:
            policy: Policy document
            inclusions: Inclusion clauses
            exclusions: Exclusion clauses
            waiting_periods: Waiting period clauses
            language: Target language
            
        Returns:
            Summary text
            
        Requirements: 3.2
        """
        summary_parts = []
        
        # Basic coverage
        summary_parts.append(
            f"{policy.policy_name} is a health insurance policy from {policy.provider_id} "
            f"that covers medical expenses up to Rs. {policy.coverage_amount:,.0f} per year "
            f"for an annual premium of Rs. {policy.premium:,.0f}."
        )
        
        # Coverage scope
        summary_parts.append(
            f"It covers {len(inclusions)} types of medical treatments including hospitalization, "
            f"surgeries, and diagnostic tests."
        )
        
        # Key exclusions
        if exclusions:
            summary_parts.append(
                f"However, it does NOT cover {len(exclusions)} categories including "
                f"{', '.join([e.original_text.lower() for e in exclusions[:2]])}."
            )
        
        # Waiting periods
        if waiting_periods:
            general_waiting = next(
                (wp for wp in waiting_periods if "general" in wp.original_text.lower()),
                None
            )
            if general_waiting:
                summary_parts.append(
                    f"You must wait {policy.waiting_periods.general} days before making most claims."
                )
            
            ped_waiting = next(
                (wp for wp in waiting_periods if "pre-existing" in wp.original_text.lower()),
                None
            )
            if ped_waiting:
                summary_parts.append(
                    f"For pre-existing diseases, the waiting period is {policy.waiting_periods.pre_existing} days "
                    f"({policy.waiting_periods.pre_existing // 365} years)."
                )
        
        summary = " ".join(summary_parts)
        
        # Translate if needed
        if language != "en":
            summary = await self._translate_text(summary, language)
        
        return summary
    
    def _extract_key_benefits(
        self,
        policy: PolicyDocument,
        inclusions: List[PolicyClause],
    ) -> List[str]:
        """
        Extract key benefits of the policy.
        
        Args:
            policy: Policy document
            inclusions: Inclusion clauses
            
        Returns:
            List of key benefit strings
        """
        benefits = []
        
        # Coverage amount
        if policy.coverage_amount >= 1000000:
            benefits.append(f"High coverage of Rs. {policy.coverage_amount:,.0f}")
        else:
            benefits.append(f"Coverage of Rs. {policy.coverage_amount:,.0f}")
        
        # Comprehensive coverage
        if len(inclusions) >= 10:
            benefits.append("Comprehensive coverage for wide range of treatments")
        
        # Specific benefits
        inclusion_text = " ".join([inc.original_text.lower() for inc in inclusions])
        
        if "hospitalization" in inclusion_text:
            benefits.append("Covers hospitalization expenses")
        
        if "daycare" in inclusion_text or "day care" in inclusion_text:
            benefits.append("Covers day care procedures")
        
        if "ambulance" in inclusion_text:
            benefits.append("Ambulance charges covered")
        
        if "pre and post" in inclusion_text or "pre-hospitalization" in inclusion_text:
            benefits.append("Pre and post hospitalization expenses covered")
        
        # Waiting period benefits
        if policy.waiting_periods.general <= 30:
            benefits.append("Short initial waiting period")
        
        return benefits[:5]  # Return top 5 benefits
    
    def _extract_key_limitations(
        self,
        policy: PolicyDocument,
        exclusions: List[PolicyClause],
        waiting_periods: List[PolicyClause],
    ) -> List[str]:
        """
        Extract key limitations of the policy.
        
        Args:
            policy: Policy document
            exclusions: Exclusion clauses
            waiting_periods: Waiting period clauses
            
        Returns:
            List of key limitation strings
        """
        limitations = []
        
        # Coverage amount limitation
        if policy.coverage_amount < 500000:
            limitations.append(f"Limited coverage of Rs. {policy.coverage_amount:,.0f} may not be sufficient for major treatments")
        
        # Waiting periods
        if policy.waiting_periods.pre_existing > 1095:
            years = policy.waiting_periods.pre_existing // 365
            limitations.append(f"Long {years}-year waiting period for pre-existing diseases")
        
        # Key exclusions
        if exclusions:
            exclusion_text = " ".join([exc.original_text.lower() for exc in exclusions])
            
            if "pre-existing" in exclusion_text or "ped" in exclusion_text:
                limitations.append("Pre-existing diseases may be excluded or have long waiting periods")
            
            if "dental" in exclusion_text:
                limitations.append("Dental treatments not covered")
            
            if "cosmetic" in exclusion_text:
                limitations.append("Cosmetic procedures not covered")
        
        # Room rent limits
        limitations.append("Room rent limits may apply, affecting overall claim amount")
        
        return limitations[:5]  # Return top 5 limitations
    
    def _generate_important_notes(
        self,
        policy: PolicyDocument,
        exclusions: List[PolicyClause],
        hidden_clauses: List[PolicyClause],
        waiting_periods: List[PolicyClause],
    ) -> List[str]:
        """
        Generate important notes and warnings for policyholders.
        
        Args:
            policy: Policy document
            exclusions: Exclusion clauses
            hidden_clauses: Hidden clauses
            waiting_periods: Waiting period clauses
            
        Returns:
            List of important note strings
        """
        notes = []
        
        # Disclosure requirement
        notes.append(
            "Always disclose all pre-existing diseases and medical history accurately. "
            "Non-disclosure can lead to claim rejection."
        )
        
        # Waiting period warning
        if waiting_periods:
            notes.append(
                "Remember the waiting periods - claims made during waiting periods will be rejected."
            )
        
        # Hidden clauses warning
        if hidden_clauses:
            notes.append(
                "Pay attention to hidden clauses like co-payment and room rent limits - "
                "they can significantly reduce your claim amount."
            )
        
        # Documentation requirement
        notes.append(
            "Keep all medical bills, prescriptions, and diagnostic reports. "
            "Submit claim documents within the specified timeframe (usually 30 days)."
        )
        
        # Exclusions warning
        if len(exclusions) > 5:
            notes.append(
                f"This policy has {len(exclusions)} exclusions. "
                "Read the exclusions list carefully to understand what is NOT covered."
            )
        
        # Renewal reminder
        notes.append(
            "Renew your policy on time to avoid losing coverage and having to restart waiting periods."
        )
        
        return notes[:5]  # Return top 5 notes
    
    async def _generate_detailed_explanation(
        self,
        policy: PolicyDocument,
        inclusions: List[PolicyClause],
        exclusions: List[PolicyClause],
        hidden_clauses: List[PolicyClause],
        language: str,
    ) -> str:
        """
        Generate detailed explanation of policy terms.
        
        Args:
            policy: Policy document
            inclusions: Inclusion clauses
            exclusions: Exclusion clauses
            hidden_clauses: Hidden clauses
            language: Target language
            
        Returns:
            Detailed explanation text
            
        Requirements: 3.2, 3.6
        """
        explanation_parts = []
        
        # Introduction
        explanation_parts.append(
            f"This explanation breaks down {policy.policy_name} into simple terms "
            f"so you can understand exactly what you're buying."
        )
        
        # Coverage explanation
        explanation_parts.append(
            f"\n\nCOVERAGE: This policy will pay up to Rs. {policy.coverage_amount:,.0f} "
            f"for your medical expenses each year. You pay Rs. {policy.premium:,.0f} annually for this coverage."
        )
        
        # What's covered
        explanation_parts.append(
            f"\n\nWHAT'S COVERED: The policy covers {len(inclusions)} types of medical treatments. "
            f"This includes common treatments like hospitalization, surgeries, and diagnostic tests. "
            f"When you need these treatments, the insurance company will pay the bills (up to the coverage limit)."
        )
        
        # What's NOT covered
        explanation_parts.append(
            f"\n\nWHAT'S NOT COVERED: There are {len(exclusions)} things this policy will NOT pay for. "
            f"These exclusions are important because claims for these will be rejected. "
            f"Common exclusions include cosmetic procedures, dental work, and certain pre-existing conditions."
        )
        
        # Waiting periods
        explanation_parts.append(
            f"\n\nWAITING PERIODS: You cannot make claims immediately after buying this policy. "
            f"There is a waiting period of {policy.waiting_periods.general} days for most treatments. "
            f"For pre-existing diseases, you must wait {policy.waiting_periods.pre_existing} days "
            f"({policy.waiting_periods.pre_existing // 365} years). "
            f"Claims made during waiting periods will be rejected."
        )
        
        # Hidden clauses
        if hidden_clauses:
            explanation_parts.append(
                f"\n\nIMPORTANT HIDDEN CLAUSES: There are {len(hidden_clauses)} clauses that are easily missed "
                f"but can significantly affect your claims. These include things like co-payment requirements, "
                f"room rent limits, and disease-specific sub-limits. Read these carefully."
            )
        
        # Claim process
        explanation_parts.append(
            f"\n\nCLAIM PROCESS: {policy.claim_process}"
        )
        
        # Final advice
        explanation_parts.append(
            "\n\nREMEMBER: Always read the complete policy document, especially the exclusions. "
            "Disclose all medical history accurately when applying. Keep all medical bills and documents. "
            "Submit claims within the specified timeframe."
        )
        
        explanation = "".join(explanation_parts)
        
        # Translate if needed
        if language != "en":
            explanation = await self._translate_text(explanation, language)
        
        return explanation
    
    def _extract_simplified_explanation(self, llm_response: str) -> str:
        """Extract simplified explanation from LLM response."""
        # Look for the explanation part
        lines = llm_response.split('\n')
        explanation_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('1.') and not line.startswith('2.') and not line.startswith('#'):
                # Skip numbered lists and headers
                if len(line) > 20:  # Meaningful content
                    explanation_lines.append(line)
        
        if explanation_lines:
            return " ".join(explanation_lines[:3])  # First 3 meaningful lines
        
        # Fallback
        return llm_response[:200].strip()
    
    def _extract_impact_explanation(self, llm_response: str) -> str:
        """Extract impact explanation from LLM response."""
        # Look for impact-related sentences
        lines = llm_response.split('.')
        for line in lines:
            if 'claim' in line.lower() or 'cover' in line.lower() or 'affect' in line.lower():
                return line.strip() + "."
        
        # Fallback
        return "This clause affects what claims will be accepted or rejected."
    
    def _determine_clause_importance(self, clause_text: str, clause_type: str) -> str:
        """Determine importance level of a clause."""
        clause_lower = clause_text.lower()
        
        # Critical importance keywords
        critical_keywords = [
            'hospitalization', 'surgery', 'emergency', 'icu', 'critical',
            'accident', 'ambulance', 'life-threatening'
        ]
        
        # Check for critical keywords
        if any(keyword in clause_lower for keyword in critical_keywords):
            return "critical"
        
        # Exclusions are typically critical
        if clause_type == "exclusion":
            return "critical"
        
        # Important keywords
        important_keywords = [
            'diagnostic', 'test', 'consultation', 'medication', 'treatment'
        ]
        
        if any(keyword in clause_lower for keyword in important_keywords):
            return "important"
        
        # Default to informational
        return "informational"
