"""Result data models for AI-generated outputs."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class PolicyScore(BaseModel):
    """Score breakdown for a policy in comparison results."""
    
    ped_compatibility: float = Field(..., ge=0, le=100, description="PED compatibility score (0-100)")
    cost_effectiveness: float = Field(..., ge=0, le=100, description="Cost effectiveness score (0-100)")
    coverage_comprehensiveness: float = Field(..., ge=0, le=100, description="Coverage comprehensiveness score (0-100)")
    claim_settlement_ratio: float = Field(..., ge=0, le=100, description="Claim settlement ratio score (0-100)")


class ComparedPolicy(BaseModel):
    """Individual policy in comparison results."""
    
    policy_id: str = Field(..., min_length=1, description="Policy identifier")
    policy_name: str = Field(..., min_length=1, description="Policy name")
    provider: str = Field(..., min_length=1, description="Insurance provider name")
    overall_score: float = Field(..., ge=0, le=100, description="Overall policy score (0-100)")
    score_breakdown: PolicyScore = Field(..., description="Detailed score breakdown")
    pros: List[str] = Field(default_factory=list, description="Policy advantages")
    cons: List[str] = Field(default_factory=list, description="Policy disadvantages")
    rejection_risk: str = Field(..., description="Rejection risk level: low, medium, high")
    reasoning: str = Field(..., min_length=1, description="Explanation for the scores and risk")
    
    @field_validator('rejection_risk')
    @classmethod
    def validate_rejection_risk(cls, v):
        """Validate rejection risk level."""
        valid_risks = {'low', 'medium', 'high'}
        if v.lower() not in valid_risks:
            raise ValueError(f"Rejection risk must be one of: {', '.join(valid_risks)}")
        return v.lower()


class ComparisonResult(BaseModel):
    """
    Policy comparison result with explanations and citations.
    
    This model represents the output of policy comparison analysis,
    including scores, recommendations, and multilingual support.
    Validates: Requirements 14.1, 14.2
    """
    
    request_id: str = Field(..., min_length=1, description="Unique request identifier")
    user_profile_id: str = Field(..., min_length=1, description="User profile identifier")
    compared_policies: List[ComparedPolicy] = Field(
        ...,
        min_length=1,
        description="List of compared policies with scores"
    )
    recommendations: List[str] = Field(
        ...,
        min_length=1,
        description="Policy recommendations based on analysis"
    )
    explanation: str = Field(..., min_length=1, description="Overall explanation of comparison results")
    citations: List[str] = Field(default_factory=list, description="Source citations for the analysis")
    language: str = Field(default="en", description="Language of the output")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Result generation timestamp"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code."""
        valid_languages = {'en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu'}
        if v.lower() not in valid_languages:
            raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v.lower()
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ComparisonResult':
        """Deserialize from dictionary."""
        return cls.model_validate(data)
    
    def get_top_policies(self, n: int = 3) -> List[ComparedPolicy]:
        """
        Get top N policies by overall score.
        
        Args:
            n: Number of top policies to return
            
        Returns:
            List of top N policies sorted by score
        """
        sorted_policies = sorted(
            self.compared_policies,
            key=lambda p: p.overall_score,
            reverse=True
        )
        return sorted_policies[:n]
    
    def get_low_risk_policies(self) -> List[ComparedPolicy]:
        """
        Get policies with low rejection risk.
        
        Returns:
            List of policies with low rejection risk
        """
        return [p for p in self.compared_policies if p.rejection_risk == 'low']


class SupportingFactor(BaseModel):
    """Factor supporting claim acceptance."""
    
    factor: str = Field(..., min_length=1, description="Description of the factor")
    policy_clause: str = Field(..., min_length=1, description="Relevant policy clause")
    impact: str = Field(..., description="Impact type: positive, negative")
    weight: float = Field(..., ge=0, le=1, description="Weight of this factor (0-1)")
    
    @field_validator('impact')
    @classmethod
    def validate_impact(cls, v):
        """Validate impact type."""
        valid_impacts = {'positive', 'negative'}
        if v.lower() not in valid_impacts:
            raise ValueError(f"Impact must be one of: {', '.join(valid_impacts)}")
        return v.lower()


class ContradictingFactor(BaseModel):
    """Factor contradicting claim acceptance."""
    
    factor: str = Field(..., min_length=1, description="Description of the factor")
    policy_clause: str = Field(..., min_length=1, description="Relevant policy clause")
    reason: str = Field(..., min_length=1, description="Reason why this contradicts the claim")


class MissingDocument(BaseModel):
    """Missing document information for a claim."""
    
    document_type: str = Field(..., min_length=1, description="Type of missing document")
    importance: str = Field(..., description="Importance level: critical, recommended, optional")
    reason: str = Field(..., min_length=1, description="Why this document is required")
    alternatives: List[str] = Field(default_factory=list, description="Alternative acceptable documents")
    
    @field_validator('importance')
    @classmethod
    def validate_importance(cls, v):
        """Validate importance level."""
        valid_levels = {'critical', 'recommended', 'optional'}
        if v.lower() not in valid_levels:
            raise ValueError(f"Importance must be one of: {', '.join(valid_levels)}")
        return v.lower()


class ClaimPrediction(BaseModel):
    """
    Claim acceptance prediction with explanations and citations.
    
    This model represents the output of claim analysis, including
    acceptance probability, supporting/contradicting factors, and
    missing documents. Includes multilingual support.
    Validates: Requirements 14.1, 14.2
    """
    
    prediction_id: str = Field(..., min_length=1, description="Unique prediction identifier")
    claim_id: str = Field(..., min_length=1, description="Claim identifier")
    acceptance_probability: float = Field(..., ge=0, le=1, description="Acceptance probability (0-1)")
    confidence_level: str = Field(..., description="Confidence level: low, medium, high")
    supporting_factors: List[SupportingFactor] = Field(
        default_factory=list,
        description="Factors supporting claim acceptance"
    )
    contradicting_factors: List[ContradictingFactor] = Field(
        default_factory=list,
        description="Factors contradicting claim acceptance"
    )
    missing_documents: List[MissingDocument] = Field(
        default_factory=list,
        description="Documents missing from the claim"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for improving claim acceptance"
    )
    explanation: str = Field(..., min_length=1, description="Detailed explanation of the prediction")
    citations: List[str] = Field(default_factory=list, description="Source citations for the analysis")
    language: str = Field(default="en", description="Language of the output")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Prediction generation timestamp"
    )
    
    @field_validator('confidence_level')
    @classmethod
    def validate_confidence(cls, v):
        """Validate confidence level."""
        valid_levels = {'low', 'medium', 'high'}
        if v.lower() not in valid_levels:
            raise ValueError(f"Confidence level must be one of: {', '.join(valid_levels)}")
        return v.lower()
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code."""
        valid_languages = {'en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu'}
        if v.lower() not in valid_languages:
            raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v.lower()
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ClaimPrediction':
        """Deserialize from dictionary."""
        return cls.model_validate(data)
    
    def is_likely_accepted(self, threshold: float = 0.5) -> bool:
        """
        Check if claim is likely to be accepted.
        
        Args:
            threshold: Probability threshold for acceptance (default 0.5)
            
        Returns:
            True if acceptance probability exceeds threshold
        """
        return self.acceptance_probability >= threshold
    
    def get_critical_missing_documents(self) -> List[MissingDocument]:
        """
        Get list of critical missing documents.
        
        Returns:
            List of documents with critical importance
        """
        return [doc for doc in self.missing_documents if doc.importance == 'critical']
    
    def has_critical_gaps(self) -> bool:
        """
        Check if there are critical document gaps.
        
        Returns:
            True if any critical documents are missing
        """
        return len(self.get_critical_missing_documents()) > 0


class TimelineEvent(BaseModel):
    """Medical timeline event."""
    
    date: str = Field(..., description="Event date (ISO format)")
    event_type: str = Field(..., description="Event type: diagnosis, procedure, test, medication_change")
    description: str = Field(..., min_length=1, description="Event description")
    significance: str = Field(..., description="Significance level: critical, important, routine")
    
    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v):
        """Validate event type."""
        valid_types = {'diagnosis', 'procedure', 'test', 'medication_change'}
        if v.lower() not in valid_types:
            raise ValueError(f"Event type must be one of: {', '.join(valid_types)}")
        return v.lower()
    
    @field_validator('significance')
    @classmethod
    def validate_significance(cls, v):
        """Validate significance level."""
        valid_levels = {'critical', 'important', 'routine'}
        if v.lower() not in valid_levels:
            raise ValueError(f"Significance must be one of: {', '.join(valid_levels)}")
        return v.lower()


class CurrentCondition(BaseModel):
    """Current medical condition."""
    
    condition: str = Field(..., min_length=1, description="Condition name")
    diagnosis_date: str = Field(..., description="Diagnosis date (ISO format)")
    status: str = Field(..., description="Status: active, managed, resolved")
    treatments: List[str] = Field(default_factory=list, description="Current treatments")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate condition status."""
        valid_statuses = {'active', 'managed', 'resolved'}
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.lower()


class CurrentMedication(BaseModel):
    """Current medication information."""
    
    name: str = Field(..., min_length=1, description="Medication name")
    dosage: str = Field(..., min_length=1, description="Dosage information")
    purpose: str = Field(..., min_length=1, description="Purpose of medication")
    start_date: str = Field(..., description="Start date (ISO format)")


class AbnormalFinding(BaseModel):
    """Abnormal test finding."""
    
    test_type: str = Field(..., min_length=1, description="Type of test")
    date: str = Field(..., description="Test date (ISO format)")
    finding: str = Field(..., min_length=1, description="Description of abnormal finding")
    trend: str = Field(..., description="Trend: improving, worsening, stable")
    
    @field_validator('trend')
    @classmethod
    def validate_trend(cls, v):
        """Validate trend."""
        valid_trends = {'improving', 'worsening', 'stable'}
        if v.lower() not in valid_trends:
            raise ValueError(f"Trend must be one of: {', '.join(valid_trends)}")
        return v.lower()


class MedicalSummary(BaseModel):
    """
    Medical history summary with explanations and citations.
    
    This model represents a summarized view of patient medical history,
    organized chronologically with key events highlighted.
    Includes multilingual support.
    Validates: Requirements 14.1, 14.2
    """
    
    summary_id: str = Field(..., min_length=1, description="Unique summary identifier")
    patient_id: str = Field(..., min_length=1, description="Patient identifier")
    timeline_events: List[TimelineEvent] = Field(
        default_factory=list,
        description="Chronological timeline of medical events"
    )
    current_conditions: List[CurrentCondition] = Field(
        default_factory=list,
        description="Current active medical conditions"
    )
    current_medications: List[CurrentMedication] = Field(
        default_factory=list,
        description="Current medications"
    )
    allergies: List[str] = Field(default_factory=list, description="Known allergies")
    abnormal_findings: List[AbnormalFinding] = Field(
        default_factory=list,
        description="Abnormal test results and findings"
    )
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    summary_text: str = Field(..., min_length=1, description="Narrative summary of medical history")
    explanation: str = Field(..., min_length=1, description="Explanation of key findings and trends")
    citations: List[str] = Field(default_factory=list, description="Source citations for the summary")
    language: str = Field(default="en", description="Language of the output")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Summary generation timestamp"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code."""
        valid_languages = {'en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu'}
        if v.lower() not in valid_languages:
            raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v.lower()
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MedicalSummary':
        """Deserialize from dictionary."""
        return cls.model_validate(data)
    
    def get_critical_events(self) -> List[TimelineEvent]:
        """
        Get critical timeline events.
        
        Returns:
            List of events with critical significance
        """
        return [event for event in self.timeline_events if event.significance == 'critical']
    
    def get_active_conditions(self) -> List[CurrentCondition]:
        """
        Get active medical conditions.
        
        Returns:
            List of conditions with active status
        """
        return [cond for cond in self.current_conditions if cond.status == 'active']
    
    def get_worsening_findings(self) -> List[AbnormalFinding]:
        """
        Get abnormal findings with worsening trend.
        
        Returns:
            List of findings trending worse
        """
        return [finding for finding in self.abnormal_findings if finding.trend == 'worsening']


class WorkflowStep(BaseModel):
    """Individual step in a workflow."""
    
    step_id: str = Field(..., min_length=1, description="Step identifier")
    step_name: str = Field(..., min_length=1, description="Step name")
    actor: str = Field(..., description="Actor: human, system, external_service")
    action: str = Field(..., min_length=1, description="Action description")
    inputs: List[str] = Field(default_factory=list, description="Input requirements")
    outputs: List[str] = Field(default_factory=list, description="Output products")
    
    @field_validator('actor')
    @classmethod
    def validate_actor(cls, v):
        """Validate actor type."""
        valid_actors = {'human', 'system', 'external_service'}
        if v.lower() not in valid_actors:
            raise ValueError(f"Actor must be one of: {', '.join(valid_actors)}")
        return v.lower()


class DataFlow(BaseModel):
    """Data flow between workflow steps."""
    
    from_step: str = Field(..., min_length=1, description="Source step ID")
    to_step: str = Field(..., min_length=1, description="Destination step ID")
    data_type: str = Field(..., min_length=1, description="Type of data being transferred")


class IntegrationPoint(BaseModel):
    """External system integration point."""
    
    system_name: str = Field(..., min_length=1, description="External system name")
    integration_type: str = Field(..., description="Integration type: API, database, file")
    purpose: str = Field(..., min_length=1, description="Purpose of integration")
    
    @field_validator('integration_type')
    @classmethod
    def validate_integration_type(cls, v):
        """Validate integration type."""
        valid_types = {'api', 'database', 'file'}
        if v.lower() not in valid_types:
            raise ValueError(f"Integration type must be one of: {', '.join(valid_types)}")
        return v.lower()


class AutomationOpportunity(BaseModel):
    """Automation opportunity for a workflow step."""
    
    step_id: str = Field(..., min_length=1, description="Step identifier")
    automation_type: str = Field(..., description="Automation type: full, partial, assisted")
    complexity: str = Field(..., description="Complexity: low, medium, high")
    estimated_effort: str = Field(..., min_length=1, description="Estimated implementation effort")
    
    @field_validator('automation_type')
    @classmethod
    def validate_automation_type(cls, v):
        """Validate automation type."""
        valid_types = {'full', 'partial', 'assisted'}
        if v.lower() not in valid_types:
            raise ValueError(f"Automation type must be one of: {', '.join(valid_types)}")
        return v.lower()
    
    @field_validator('complexity')
    @classmethod
    def validate_complexity(cls, v):
        """Validate complexity level."""
        valid_levels = {'low', 'medium', 'high'}
        if v.lower() not in valid_levels:
            raise ValueError(f"Complexity must be one of: {', '.join(valid_levels)}")
        return v.lower()


class WorkflowStructure(BaseModel):
    """
    Parsed workflow structure with explanations.
    
    This model represents a workflow parsed from natural language,
    including steps, data flows, and automation opportunities.
    Includes multilingual support.
    Validates: Requirements 14.1, 14.2
    """
    
    workflow_id: str = Field(..., min_length=1, description="Unique workflow identifier")
    workflow_name: str = Field(..., min_length=1, description="Workflow name")
    description: str = Field(..., min_length=1, description="Workflow description")
    steps: List[WorkflowStep] = Field(..., min_length=1, description="Workflow steps")
    data_flows: List[DataFlow] = Field(default_factory=list, description="Data flows between steps")
    integration_points: List[IntegrationPoint] = Field(
        default_factory=list,
        description="External system integration points"
    )
    automation_opportunities: List[AutomationOpportunity] = Field(
        default_factory=list,
        description="Identified automation opportunities"
    )
    explanation: str = Field(..., min_length=1, description="Explanation of workflow structure")
    citations: List[str] = Field(default_factory=list, description="Source citations")
    language: str = Field(default="en", description="Language of the output")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Structure generation timestamp"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code."""
        valid_languages = {'en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu'}
        if v.lower() not in valid_languages:
            raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v.lower()
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WorkflowStructure':
        """Deserialize from dictionary."""
        return cls.model_validate(data)
    
    def get_human_steps(self) -> List[WorkflowStep]:
        """Get steps requiring human actors."""
        return [step for step in self.steps if step.actor == 'human']
    
    def get_automation_candidates(self) -> List[AutomationOpportunity]:
        """Get full automation candidates."""
        return [opp for opp in self.automation_opportunities if opp.automation_type == 'full']


class ResearchPaper(BaseModel):
    """Research paper recommendation."""
    
    paper_id: str = Field(..., min_length=1, description="Paper identifier")
    title: str = Field(..., min_length=1, description="Paper title")
    authors: List[str] = Field(default_factory=list, description="Paper authors")
    abstract: str = Field(..., min_length=1, description="Paper abstract")
    key_findings: List[str] = Field(default_factory=list, description="Key findings from the paper")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score (0-1)")
    relevance_explanation: str = Field(..., min_length=1, description="Why this paper is relevant")
    publication_date: str = Field(..., description="Publication date")
    journal: str = Field(..., min_length=1, description="Journal or publication venue")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")


class ResearchRecommendations(BaseModel):
    """
    Medical research recommendations with explanations.
    
    This model represents recommended research papers for a medical case,
    ranked by relevance with explanations.
    Validates: Requirements 14.1, 14.2
    """
    
    recommendation_id: str = Field(..., min_length=1, description="Unique recommendation identifier")
    case_description: str = Field(..., min_length=1, description="Medical case description")
    papers: List[ResearchPaper] = Field(..., min_length=1, description="Recommended research papers")
    explanation: str = Field(..., min_length=1, description="Overall explanation of recommendations")
    citations: List[str] = Field(default_factory=list, description="Source citations")
    language: str = Field(default="en", description="Language of the output")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Recommendation generation timestamp"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code."""
        valid_languages = {'en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu'}
        if v.lower() not in valid_languages:
            raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v.lower()
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ResearchRecommendations':
        """Deserialize from dictionary."""
        return cls.model_validate(data)
    
    def get_top_papers(self, n: int = 5) -> List[ResearchPaper]:
        """
        Get top N papers by relevance score.
        
        Args:
            n: Number of papers to return
            
        Returns:
            List of top N papers sorted by relevance
        """
        sorted_papers = sorted(
            self.papers,
            key=lambda p: p.relevance_score,
            reverse=True
        )
        return sorted_papers[:n]


class PEDAnalysis(BaseModel):
    """Analysis of a specific pre-existing disease against a policy."""
    
    condition: str = Field(..., min_length=1, description="Pre-existing disease name")
    is_excluded: bool = Field(..., description="Whether this condition is explicitly excluded")
    waiting_period_days: Optional[int] = Field(None, ge=0, description="Waiting period for this condition in days")
    coverage_details: str = Field(..., min_length=1, description="Details of coverage for this condition")
    rejection_risk: str = Field(..., description="Rejection risk for this condition: low, medium, high")
    
    @field_validator('rejection_risk')
    @classmethod
    def validate_rejection_risk(cls, v):
        """Validate rejection risk level."""
        valid_risks = {'low', 'medium', 'high'}
        if v.lower() not in valid_risks:
            raise ValueError(f"Rejection risk must be one of: {', '.join(valid_risks)}")
        return v.lower()


class MedicationAnalysis(BaseModel):
    """Analysis of medication implications for policy acceptance."""
    
    medication: str = Field(..., min_length=1, description="Medication name")
    implied_conditions: List[str] = Field(
        default_factory=list,
        description="Medical conditions implied by this medication"
    )
    impact_on_acceptance: str = Field(..., min_length=1, description="How this medication affects policy acceptance")
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    
    @field_validator('risk_level')
    @classmethod
    def validate_risk_level(cls, v):
        """Validate risk level."""
        valid_levels = {'low', 'medium', 'high'}
        if v.lower() not in valid_levels:
            raise ValueError(f"Risk level must be one of: {', '.join(valid_levels)}")
        return v.lower()


class CompatiblePolicy(BaseModel):
    """Policy compatible with user's medical profile."""
    
    policy_id: str = Field(..., min_length=1, description="Policy identifier")
    policy_name: str = Field(..., min_length=1, description="Policy name")
    provider: str = Field(..., min_length=1, description="Insurance provider")
    compatibility_score: float = Field(..., ge=0, le=100, description="Compatibility score (0-100)")
    acceptance_likelihood: str = Field(..., description="Acceptance likelihood: high, medium, low")
    key_benefits: List[str] = Field(default_factory=list, description="Key benefits for user's profile")
    limitations: List[str] = Field(default_factory=list, description="Limitations or restrictions")
    
    @field_validator('acceptance_likelihood')
    @classmethod
    def validate_acceptance_likelihood(cls, v):
        """Validate acceptance likelihood."""
        valid_levels = {'high', 'medium', 'low'}
        if v.lower() not in valid_levels:
            raise ValueError(f"Acceptance likelihood must be one of: {', '.join(valid_levels)}")
        return v.lower()


class CompatibilityReport(BaseModel):
    """
    PED compatibility analysis report with explanations and recommendations.
    
    This model represents the analysis of pre-existing diseases and medications
    against insurance policies, including rejection probability and compatible
    policy recommendations.
    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 14.1, 14.2
    """
    
    report_id: str = Field(..., min_length=1, description="Unique report identifier")
    user_profile_id: str = Field(..., min_length=1, description="User profile identifier")
    policy_id: Optional[str] = Field(None, description="Specific policy analyzed (if applicable)")
    ped_analyses: List[PEDAnalysis] = Field(
        default_factory=list,
        description="Analysis of each pre-existing disease"
    )
    medication_analyses: List[MedicationAnalysis] = Field(
        default_factory=list,
        description="Analysis of medications and their implications"
    )
    overall_rejection_probability: float = Field(
        ...,
        ge=0,
        le=1,
        description="Overall rejection probability (0-1)"
    )
    rejection_probability_explanation: str = Field(
        ...,
        min_length=1,
        description="Detailed explanation of rejection probability"
    )
    compatible_policies: List[CompatiblePolicy] = Field(
        default_factory=list,
        description="Policies with higher acceptance likelihood"
    )
    recommendations: List[str] = Field(
        ...,
        min_length=1,
        description="Recommendations for improving acceptance chances"
    )
    explanation: str = Field(..., min_length=1, description="Overall explanation of compatibility analysis")
    citations: List[str] = Field(default_factory=list, description="Source citations for the analysis")
    language: str = Field(default="en", description="Language of the output")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Report generation timestamp"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code."""
        valid_languages = {'en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu'}
        if v.lower() not in valid_languages:
            raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v.lower()
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CompatibilityReport':
        """Deserialize from dictionary."""
        return cls.model_validate(data)
    
    def get_high_risk_conditions(self) -> List[PEDAnalysis]:
        """
        Get pre-existing diseases with high rejection risk.
        
        Returns:
            List of PED analyses with high rejection risk
        """
        return [ped for ped in self.ped_analyses if ped.rejection_risk == 'high']
    
    def get_excluded_conditions(self) -> List[PEDAnalysis]:
        """
        Get explicitly excluded pre-existing diseases.
        
        Returns:
            List of PED analyses where condition is excluded
        """
        return [ped for ped in self.ped_analyses if ped.is_excluded]
    
    def get_high_acceptance_policies(self) -> List[CompatiblePolicy]:
        """
        Get policies with high acceptance likelihood.
        
        Returns:
            List of compatible policies with high acceptance likelihood
        """
        return [policy for policy in self.compatible_policies if policy.acceptance_likelihood == 'high']
    
    def is_high_rejection_risk(self, threshold: float = 0.5) -> bool:
        """
        Check if overall rejection risk is high.
        
        Args:
            threshold: Probability threshold for high risk (default 0.5)
            
        Returns:
            True if rejection probability exceeds threshold
        """
        return self.overall_rejection_probability >= threshold


class AlternativePolicy(BaseModel):
    """Alternative policy recommendation."""
    
    policy_id: str = Field(..., min_length=1, description="Policy identifier")
    policy_name: str = Field(..., min_length=1, description="Policy name")
    provider: str = Field(..., min_length=1, description="Insurance provider")
    coverage_differences: List[str] = Field(
        ...,
        min_length=1,
        description="How coverage differs from current policy"
    )
    cost_comparison: str = Field(..., min_length=1, description="Cost comparison with current policy")
    suitability_score: float = Field(..., ge=0, le=100, description="Suitability score (0-100)")
    suitability_reasoning: str = Field(..., min_length=1, description="Why this policy is more suitable")
    switching_feasibility: str = Field(..., description="Feasibility: easy, moderate, difficult")
    
    @field_validator('switching_feasibility')
    @classmethod
    def validate_feasibility(cls, v):
        """Validate switching feasibility."""
        valid_levels = {'easy', 'moderate', 'difficult'}
        if v.lower() not in valid_levels:
            raise ValueError(f"Switching feasibility must be one of: {', '.join(valid_levels)}")
        return v.lower()


class PolicyRecommendations(BaseModel):
    """
    Alternative policy recommendations with explanations.
    
    This model represents alternative policy recommendations when
    current policy is unsuitable, with cost and coverage comparisons.
    Validates: Requirements 14.1, 14.2
    """
    
    recommendation_id: str = Field(..., min_length=1, description="Unique recommendation identifier")
    current_policy_id: str = Field(..., min_length=1, description="Current policy identifier")
    unsuitability_reason: str = Field(..., min_length=1, description="Why current policy is unsuitable")
    alternative_policies: List[AlternativePolicy] = Field(
        ...,
        min_length=1,
        description="Alternative policy options"
    )
    explanation: str = Field(..., min_length=1, description="Overall explanation of recommendations")
    citations: List[str] = Field(default_factory=list, description="Source citations")
    language: str = Field(default="en", description="Language of the output")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Recommendation generation timestamp"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code."""
        valid_languages = {'en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu'}
        if v.lower() not in valid_languages:
            raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v.lower()
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PolicyRecommendations':
        """Deserialize from dictionary."""
        return cls.model_validate(data)
    
    def get_top_alternatives(self, n: int = 3) -> List[AlternativePolicy]:
        """
        Get top N alternative policies by suitability score.
        
        Args:
            n: Number of alternatives to return
            
        Returns:
            List of top N alternatives sorted by suitability
        """
        sorted_alternatives = sorted(
            self.alternative_policies,
            key=lambda p: p.suitability_score,
            reverse=True
        )
        return sorted_alternatives[:n]
    
    def get_easy_switches(self) -> List[AlternativePolicy]:
        """
        Get policies that are easy to switch to.
        
        Returns:
            List of policies with easy switching feasibility
        """
        return [p for p in self.alternative_policies if p.switching_feasibility == 'easy']


class PolicyClause(BaseModel):
    """Individual policy clause explanation."""
    
    clause_type: str = Field(..., min_length=1, description="Type of clause: inclusion, exclusion, waiting_period, coverage_limit, hidden")
    original_text: str = Field(..., min_length=1, description="Original policy clause text")
    simplified_explanation: str = Field(..., min_length=1, description="Simplified explanation in everyday language")
    importance: str = Field(..., description="Importance level: critical, important, informational")
    impact_on_claims: str = Field(..., min_length=1, description="How this clause affects claims")
    
    @field_validator('clause_type')
    @classmethod
    def validate_clause_type(cls, v):
        """Validate clause type."""
        valid_types = {'inclusion', 'exclusion', 'waiting_period', 'coverage_limit', 'hidden', 'general'}
        if v.lower() not in valid_types:
            raise ValueError(f"Clause type must be one of: {', '.join(valid_types)}")
        return v.lower()
    
    @field_validator('importance')
    @classmethod
    def validate_importance(cls, v):
        """Validate importance level."""
        valid_levels = {'critical', 'important', 'informational'}
        if v.lower() not in valid_levels:
            raise ValueError(f"Importance must be one of: {', '.join(valid_levels)}")
        return v.lower()


class PolicyExplanation(BaseModel):
    """
    Policy document explanation with simplified terms and key clauses.
    
    This model represents a comprehensive explanation of an insurance policy,
    translating complex terminology into simple language and highlighting
    important clauses, inclusions, exclusions, and hidden terms.
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 14.1, 14.2
    """
    
    explanation_id: str = Field(..., min_length=1, description="Unique explanation identifier")
    policy_id: str = Field(..., min_length=1, description="Policy identifier")
    policy_name: str = Field(..., min_length=1, description="Policy name")
    provider: str = Field(..., min_length=1, description="Insurance provider")
    
    # Key clauses organized by type
    inclusions: List[PolicyClause] = Field(
        default_factory=list,
        description="Coverage inclusions - what is covered"
    )
    exclusions: List[PolicyClause] = Field(
        default_factory=list,
        description="Coverage exclusions - what is NOT covered"
    )
    waiting_periods: List[PolicyClause] = Field(
        default_factory=list,
        description="Waiting period clauses"
    )
    coverage_limits: List[PolicyClause] = Field(
        default_factory=list,
        description="Coverage limits and sub-limits"
    )
    hidden_clauses: List[PolicyClause] = Field(
        default_factory=list,
        description="Hidden or easily missed clauses that affect claims"
    )
    
    # Overall summaries
    summary: str = Field(..., min_length=1, description="Overall policy summary in simple language")
    key_benefits: List[str] = Field(
        default_factory=list,
        description="Key benefits of this policy"
    )
    key_limitations: List[str] = Field(
        default_factory=list,
        description="Key limitations and restrictions"
    )
    important_notes: List[str] = Field(
        default_factory=list,
        description="Important notes and warnings for policyholders"
    )
    
    # Explanations and citations
    explanation: str = Field(..., min_length=1, description="Detailed explanation of policy terms")
    citations: List[str] = Field(default_factory=list, description="Source citations from policy document")
    language: str = Field(default="en", description="Language of the output")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Explanation generation timestamp"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code."""
        valid_languages = {'en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu'}
        if v.lower() not in valid_languages:
            raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v.lower()
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PolicyExplanation':
        """Deserialize from dictionary."""
        return cls.model_validate(data)
    
    def get_critical_clauses(self) -> List[PolicyClause]:
        """
        Get all critical clauses across all categories.
        
        Returns:
            List of clauses with critical importance
        """
        all_clauses = (
            self.inclusions + 
            self.exclusions + 
            self.waiting_periods + 
            self.coverage_limits + 
            self.hidden_clauses
        )
        return [clause for clause in all_clauses if clause.importance == 'critical']
    
    def get_exclusions_summary(self) -> List[str]:
        """
        Get simplified list of what's NOT covered.
        
        Returns:
            List of exclusion summaries
        """
        return [clause.simplified_explanation for clause in self.exclusions]
    
    def get_inclusions_summary(self) -> List[str]:
        """
        Get simplified list of what IS covered.
        
        Returns:
            List of inclusion summaries
        """
        return [clause.simplified_explanation for clause in self.inclusions]
    
    def has_hidden_clauses(self) -> bool:
        """
        Check if policy has hidden or easily missed clauses.
        
        Returns:
            True if hidden clauses exist
        """
        return len(self.hidden_clauses) > 0


class EligibilityResult(BaseModel):
    """
    Ombudsman eligibility check result.
    
    This model represents the result of checking whether a user is eligible
    to file a complaint with the Insurance Ombudsman, including jurisdiction
    validation, deadline calculation, and regional office identification.
    Validates: Requirements 7.2, 7.3, 7.4, 14.1, 14.2
    """
    
    result_id: str = Field(..., min_length=1, description="Unique result identifier")
    claim_id: Optional[str] = Field(None, description="Associated claim identifier")
    
    # Eligibility determination
    is_eligible: bool = Field(..., description="Whether user is eligible to file with Ombudsman")
    eligibility_reasons: List[str] = Field(
        ...,
        min_length=1,
        description="Reasons for eligibility determination"
    )
    
    # Jurisdiction validation (₹20 lakh limit)
    claim_amount: float = Field(..., ge=0, description="Claim amount in rupees")
    jurisdiction_limit: float = Field(default=2000000.0, description="Ombudsman jurisdiction limit (₹20 lakh)")
    within_jurisdiction: bool = Field(..., description="Whether claim amount is within jurisdiction")
    
    # Deadline calculation (1 year from rejection)
    rejection_date: Optional[str] = Field(None, description="Claim rejection date (ISO format)")
    filing_deadline: Optional[str] = Field(None, description="Last date to file complaint (ISO format)")
    days_remaining: Optional[int] = Field(None, description="Days remaining to file complaint")
    within_deadline: bool = Field(..., description="Whether complaint is within filing deadline")
    
    # Regional office identification
    user_location: str = Field(..., min_length=1, description="User's location (city/state)")
    regional_office: Optional[dict] = Field(None, description="Appropriate regional Ombudsman office details")
    
    # Guidance and explanations
    explanation: str = Field(..., min_length=1, description="Detailed explanation of eligibility determination")
    next_steps: List[str] = Field(
        default_factory=list,
        description="Recommended next steps for the user"
    )
    citations: List[str] = Field(default_factory=list, description="Source citations for eligibility rules")
    language: str = Field(default="en", description="Language of the output")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Result generation timestamp"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code."""
        valid_languages = {'en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu'}
        if v.lower() not in valid_languages:
            raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v.lower()
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EligibilityResult':
        """Deserialize from dictionary."""
        return cls.model_validate(data)
    
    def is_urgent(self, threshold_days: int = 30) -> bool:
        """
        Check if filing is urgent (deadline approaching).
        
        Args:
            threshold_days: Number of days to consider urgent (default 30)
            
        Returns:
            True if days remaining is less than threshold
        """
        if self.days_remaining is None:
            return False
        return self.days_remaining < threshold_days
    
    def get_office_name(self) -> Optional[str]:
        """
        Get the name of the regional office.
        
        Returns:
            Office name if available, None otherwise
        """
        if self.regional_office:
            return self.regional_office.get('name')
        return None
    
    def get_office_contact(self) -> Optional[dict]:
        """
        Get contact information for the regional office.
        
        Returns:
            Dictionary with contact details if available, None otherwise
        """
        if self.regional_office:
            return {
                'phone': self.regional_office.get('contact_phone'),
                'email': self.regional_office.get('contact_email'),
                'address': self.regional_office.get('address')
            }
        return None


class ComplaintGuide(BaseModel):
    """
    Ombudsman complaint filing guidance.
    
    This model provides comprehensive guidance on filing a complaint
    with the Insurance Ombudsman, including process steps, required
    documentation, and timeline.
    Validates: Requirements 7.5, 14.1, 14.2
    """
    
    guide_id: str = Field(..., min_length=1, description="Unique guide identifier")
    claim_id: str = Field(..., min_length=1, description="Associated claim identifier")
    
    # Filing process
    filing_process: List[str] = Field(
        ...,
        min_length=1,
        description="Step-by-step filing process"
    )
    
    # Required documentation
    required_documents: List[str] = Field(
        ...,
        min_length=1,
        description="Documents required for filing complaint"
    )
    
    # Argument points
    argument_points: List[str] = Field(
        default_factory=list,
        description="Key argument points to support the complaint"
    )
    
    # Timeline
    expected_timeline: str = Field(..., min_length=1, description="Expected timeline for resolution")
    important_deadlines: List[str] = Field(
        default_factory=list,
        description="Important deadlines to be aware of"
    )
    
    # Additional guidance
    tips_and_warnings: List[str] = Field(
        default_factory=list,
        description="Tips for successful filing and common pitfalls to avoid"
    )
    
    # Explanations and citations
    explanation: str = Field(..., min_length=1, description="Overall explanation of the complaint process")
    citations: List[str] = Field(default_factory=list, description="Source citations for guidance")
    language: str = Field(default="en", description="Language of the output")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Guide generation timestamp"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code."""
        valid_languages = {'en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu'}
        if v.lower() not in valid_languages:
            raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v.lower()
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ComplaintGuide':
        """Deserialize from dictionary."""
        return cls.model_validate(data)
