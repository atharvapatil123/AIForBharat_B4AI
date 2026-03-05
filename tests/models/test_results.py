"""Tests for result data models."""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from healthcare_insurance_platform.models.results import (
    ComparisonResult,
    ComparedPolicy,
    PolicyScore,
    ClaimPrediction,
    SupportingFactor,
    ContradictingFactor,
    MissingDocument,
    MedicalSummary,
    TimelineEvent,
    CurrentCondition,
    CurrentMedication,
    AbnormalFinding,
    WorkflowStructure,
    WorkflowStep,
    DataFlow,
    IntegrationPoint,
    AutomationOpportunity,
    ResearchRecommendations,
    ResearchPaper,
    PolicyRecommendations,
    AlternativePolicy,
)


class TestPolicyScore:
    """Tests for PolicyScore model."""
    
    def test_valid_policy_score(self):
        """Test creating a valid policy score."""
        score = PolicyScore(
            ped_compatibility=85.5,
            cost_effectiveness=70.0,
            coverage_comprehensiveness=90.0,
            claim_settlement_ratio=88.0
        )
        assert score.ped_compatibility == 85.5
        assert score.cost_effectiveness == 70.0
    
    def test_score_out_of_range(self):
        """Test that scores must be between 0 and 100."""
        with pytest.raises(ValidationError):
            PolicyScore(
                ped_compatibility=150.0,  # Invalid: > 100
                cost_effectiveness=70.0,
                coverage_comprehensiveness=90.0,
                claim_settlement_ratio=88.0
            )
        
        with pytest.raises(ValidationError):
            PolicyScore(
                ped_compatibility=85.0,
                cost_effectiveness=-10.0,  # Invalid: < 0
                coverage_comprehensiveness=90.0,
                claim_settlement_ratio=88.0
            )


class TestComparedPolicy:
    """Tests for ComparedPolicy model."""
    
    def test_valid_compared_policy(self):
        """Test creating a valid compared policy."""
        score = PolicyScore(
            ped_compatibility=85.0,
            cost_effectiveness=70.0,
            coverage_comprehensiveness=90.0,
            claim_settlement_ratio=88.0
        )
        policy = ComparedPolicy(
            policy_id="POL123",
            policy_name="Health Plus",
            provider="ABC Insurance",
            overall_score=83.25,
            score_breakdown=score,
            pros=["Comprehensive coverage", "Low premium"],
            cons=["High deductible"],
            rejection_risk="low",
            reasoning="Good match for user profile"
        )
        assert policy.policy_id == "POL123"
        assert policy.rejection_risk == "low"
        assert len(policy.pros) == 2
    
    def test_rejection_risk_validation(self):
        """Test rejection risk must be low, medium, or high."""
        score = PolicyScore(
            ped_compatibility=85.0,
            cost_effectiveness=70.0,
            coverage_comprehensiveness=90.0,
            claim_settlement_ratio=88.0
        )
        
        with pytest.raises(ValidationError):
            ComparedPolicy(
                policy_id="POL123",
                policy_name="Health Plus",
                provider="ABC Insurance",
                overall_score=83.25,
                score_breakdown=score,
                rejection_risk="very_high",  # Invalid
                reasoning="Test"
            )


class TestComparisonResult:
    """Tests for ComparisonResult model."""
    
    def test_valid_comparison_result(self):
        """Test creating a valid comparison result."""
        score = PolicyScore(
            ped_compatibility=85.0,
            cost_effectiveness=70.0,
            coverage_comprehensiveness=90.0,
            claim_settlement_ratio=88.0
        )
        policy = ComparedPolicy(
            policy_id="POL123",
            policy_name="Health Plus",
            provider="ABC Insurance",
            overall_score=83.25,
            score_breakdown=score,
            rejection_risk="low",
            reasoning="Good match"
        )
        
        result = ComparisonResult(
            request_id="REQ123",
            user_profile_id="USER456",
            compared_policies=[policy],
            recommendations=["Consider Health Plus for best coverage"],
            explanation="Based on your profile, Health Plus offers the best value",
            citations=["Policy document section 3.2"],
            language="en"
        )
        
        assert result.request_id == "REQ123"
        assert len(result.compared_policies) == 1
        assert result.language == "en"
    
    def test_get_top_policies(self):
        """Test getting top policies by score."""
        score1 = PolicyScore(
            ped_compatibility=85.0,
            cost_effectiveness=70.0,
            coverage_comprehensiveness=90.0,
            claim_settlement_ratio=88.0
        )
        score2 = PolicyScore(
            ped_compatibility=75.0,
            cost_effectiveness=80.0,
            coverage_comprehensiveness=85.0,
            claim_settlement_ratio=78.0
        )
        
        policy1 = ComparedPolicy(
            policy_id="POL1",
            policy_name="Policy 1",
            provider="Provider 1",
            overall_score=90.0,
            score_breakdown=score1,
            rejection_risk="low",
            reasoning="Best"
        )
        policy2 = ComparedPolicy(
            policy_id="POL2",
            policy_name="Policy 2",
            provider="Provider 2",
            overall_score=75.0,
            score_breakdown=score2,
            rejection_risk="medium",
            reasoning="Good"
        )
        
        result = ComparisonResult(
            request_id="REQ123",
            user_profile_id="USER456",
            compared_policies=[policy2, policy1],  # Unsorted
            recommendations=["Test"],
            explanation="Test explanation"
        )
        
        top = result.get_top_policies(1)
        assert len(top) == 1
        assert top[0].policy_id == "POL1"
    
    def test_get_low_risk_policies(self):
        """Test filtering low risk policies."""
        score = PolicyScore(
            ped_compatibility=85.0,
            cost_effectiveness=70.0,
            coverage_comprehensiveness=90.0,
            claim_settlement_ratio=88.0
        )
        
        policy1 = ComparedPolicy(
            policy_id="POL1",
            policy_name="Policy 1",
            provider="Provider 1",
            overall_score=90.0,
            score_breakdown=score,
            rejection_risk="low",
            reasoning="Best"
        )
        policy2 = ComparedPolicy(
            policy_id="POL2",
            policy_name="Policy 2",
            provider="Provider 2",
            overall_score=75.0,
            score_breakdown=score,
            rejection_risk="high",
            reasoning="Risky"
        )
        
        result = ComparisonResult(
            request_id="REQ123",
            user_profile_id="USER456",
            compared_policies=[policy1, policy2],
            recommendations=["Test"],
            explanation="Test explanation"
        )
        
        low_risk = result.get_low_risk_policies()
        assert len(low_risk) == 1
        assert low_risk[0].policy_id == "POL1"
    
    def test_language_validation(self):
        """Test language must be a supported code."""
        score = PolicyScore(
            ped_compatibility=85.0,
            cost_effectiveness=70.0,
            coverage_comprehensiveness=90.0,
            claim_settlement_ratio=88.0
        )
        policy = ComparedPolicy(
            policy_id="POL123",
            policy_name="Health Plus",
            provider="ABC Insurance",
            overall_score=83.25,
            score_breakdown=score,
            rejection_risk="low",
            reasoning="Good match"
        )
        
        with pytest.raises(ValidationError):
            ComparisonResult(
                request_id="REQ123",
                user_profile_id="USER456",
                compared_policies=[policy],
                recommendations=["Test"],
                explanation="Test",
                language="fr"  # Invalid: not supported
            )


class TestClaimPrediction:
    """Tests for ClaimPrediction model."""
    
    def test_valid_claim_prediction(self):
        """Test creating a valid claim prediction."""
        supporting = SupportingFactor(
            factor="Treatment covered under policy",
            policy_clause="Section 4.2",
            impact="positive",
            weight=0.8
        )
        contradicting = ContradictingFactor(
            factor="Waiting period not met",
            policy_clause="Section 2.1",
            reason="Only 6 months since policy start"
        )
        missing = MissingDocument(
            document_type="Hospital discharge summary",
            importance="critical",
            reason="Required to verify treatment dates",
            alternatives=["Medical certificate with dates"]
        )
        
        prediction = ClaimPrediction(
            prediction_id="PRED123",
            claim_id="CLM456",
            acceptance_probability=0.65,
            confidence_level="medium",
            supporting_factors=[supporting],
            contradicting_factors=[contradicting],
            missing_documents=[missing],
            recommendations=["Obtain discharge summary"],
            explanation="Claim has moderate acceptance probability",
            citations=["Policy section 4.2", "Policy section 2.1"]
        )
        
        assert prediction.acceptance_probability == 0.65
        assert prediction.confidence_level == "medium"
        assert len(prediction.missing_documents) == 1
    
    def test_is_likely_accepted(self):
        """Test checking if claim is likely accepted."""
        prediction = ClaimPrediction(
            prediction_id="PRED123",
            claim_id="CLM456",
            acceptance_probability=0.75,
            confidence_level="high",
            explanation="High probability"
        )
        
        assert prediction.is_likely_accepted() is True
        assert prediction.is_likely_accepted(threshold=0.8) is False
    
    def test_get_critical_missing_documents(self):
        """Test getting critical missing documents."""
        critical_doc = MissingDocument(
            document_type="Hospital bill",
            importance="critical",
            reason="Required for claim amount verification"
        )
        optional_doc = MissingDocument(
            document_type="Prescription copy",
            importance="optional",
            reason="Helpful for verification"
        )
        
        prediction = ClaimPrediction(
            prediction_id="PRED123",
            claim_id="CLM456",
            acceptance_probability=0.65,
            confidence_level="medium",
            missing_documents=[critical_doc, optional_doc],
            explanation="Test"
        )
        
        critical = prediction.get_critical_missing_documents()
        assert len(critical) == 1
        assert critical[0].document_type == "Hospital bill"
    
    def test_has_critical_gaps(self):
        """Test checking for critical document gaps."""
        critical_doc = MissingDocument(
            document_type="Hospital bill",
            importance="critical",
            reason="Required"
        )
        
        prediction1 = ClaimPrediction(
            prediction_id="PRED123",
            claim_id="CLM456",
            acceptance_probability=0.65,
            confidence_level="medium",
            missing_documents=[critical_doc],
            explanation="Test"
        )
        
        prediction2 = ClaimPrediction(
            prediction_id="PRED124",
            claim_id="CLM457",
            acceptance_probability=0.85,
            confidence_level="high",
            missing_documents=[],
            explanation="Test"
        )
        
        assert prediction1.has_critical_gaps() is True
        assert prediction2.has_critical_gaps() is False


class TestMedicalSummary:
    """Tests for MedicalSummary model."""
    
    def test_valid_medical_summary(self):
        """Test creating a valid medical summary."""
        event = TimelineEvent(
            date="2023-01-15",
            event_type="diagnosis",
            description="Diagnosed with hypertension",
            significance="critical"
        )
        condition = CurrentCondition(
            condition="Hypertension",
            diagnosis_date="2023-01-15",
            status="managed",
            treatments=["Medication", "Diet control"]
        )
        medication = CurrentMedication(
            name="Lisinopril",
            dosage="10mg daily",
            purpose="Blood pressure control",
            start_date="2023-01-20"
        )
        finding = AbnormalFinding(
            test_type="Blood pressure",
            date="2023-01-15",
            finding="BP 160/100",
            trend="improving"
        )
        
        summary = MedicalSummary(
            summary_id="SUM123",
            patient_id="PAT456",
            timeline_events=[event],
            current_conditions=[condition],
            current_medications=[medication],
            allergies=["Penicillin"],
            abnormal_findings=[finding],
            risk_factors=["Family history of heart disease"],
            summary_text="Patient with managed hypertension",
            explanation="Condition is well-controlled with medication"
        )
        
        assert summary.patient_id == "PAT456"
        assert len(summary.timeline_events) == 1
        assert len(summary.allergies) == 1
    
    def test_get_critical_events(self):
        """Test getting critical timeline events."""
        critical_event = TimelineEvent(
            date="2023-01-15",
            event_type="diagnosis",
            description="Heart attack",
            significance="critical"
        )
        routine_event = TimelineEvent(
            date="2023-02-01",
            event_type="test",
            description="Routine checkup",
            significance="routine"
        )
        
        summary = MedicalSummary(
            summary_id="SUM123",
            patient_id="PAT456",
            timeline_events=[critical_event, routine_event],
            summary_text="Test",
            explanation="Test"
        )
        
        critical = summary.get_critical_events()
        assert len(critical) == 1
        assert critical[0].description == "Heart attack"
    
    def test_get_active_conditions(self):
        """Test getting active conditions."""
        active_condition = CurrentCondition(
            condition="Diabetes",
            diagnosis_date="2023-01-01",
            status="active",
            treatments=["Insulin"]
        )
        resolved_condition = CurrentCondition(
            condition="Flu",
            diagnosis_date="2023-02-01",
            status="resolved",
            treatments=[]
        )
        
        summary = MedicalSummary(
            summary_id="SUM123",
            patient_id="PAT456",
            current_conditions=[active_condition, resolved_condition],
            summary_text="Test",
            explanation="Test"
        )
        
        active = summary.get_active_conditions()
        assert len(active) == 1
        assert active[0].condition == "Diabetes"
    
    def test_get_worsening_findings(self):
        """Test getting worsening abnormal findings."""
        worsening = AbnormalFinding(
            test_type="Blood sugar",
            date="2023-03-01",
            finding="Glucose 250 mg/dL",
            trend="worsening"
        )
        improving = AbnormalFinding(
            test_type="Blood pressure",
            date="2023-03-01",
            finding="BP 130/85",
            trend="improving"
        )
        
        summary = MedicalSummary(
            summary_id="SUM123",
            patient_id="PAT456",
            abnormal_findings=[worsening, improving],
            summary_text="Test",
            explanation="Test"
        )
        
        worsening_findings = summary.get_worsening_findings()
        assert len(worsening_findings) == 1
        assert worsening_findings[0].test_type == "Blood sugar"


class TestWorkflowStructure:
    """Tests for WorkflowStructure model."""
    
    def test_valid_workflow_structure(self):
        """Test creating a valid workflow structure."""
        step = WorkflowStep(
            step_id="STEP1",
            step_name="Patient registration",
            actor="human",
            action="Register patient details",
            inputs=["Patient information"],
            outputs=["Patient ID"]
        )
        data_flow = DataFlow(
            from_step="STEP1",
            to_step="STEP2",
            data_type="Patient ID"
        )
        integration = IntegrationPoint(
            system_name="Hospital Management System",
            integration_type="api",
            purpose="Retrieve patient records"
        )
        automation = AutomationOpportunity(
            step_id="STEP1",
            automation_type="partial",
            complexity="medium",
            estimated_effort="2 weeks"
        )
        
        workflow = WorkflowStructure(
            workflow_id="WF123",
            workflow_name="Patient Onboarding",
            description="Process for onboarding new patients",
            steps=[step],
            data_flows=[data_flow],
            integration_points=[integration],
            automation_opportunities=[automation],
            explanation="Workflow for patient registration and verification"
        )
        
        assert workflow.workflow_id == "WF123"
        assert len(workflow.steps) == 1
        assert len(workflow.integration_points) == 1
    
    def test_get_human_steps(self):
        """Test getting steps requiring human actors."""
        human_step = WorkflowStep(
            step_id="STEP1",
            step_name="Manual review",
            actor="human",
            action="Review documents"
        )
        system_step = WorkflowStep(
            step_id="STEP2",
            step_name="Auto verification",
            actor="system",
            action="Verify data"
        )
        
        workflow = WorkflowStructure(
            workflow_id="WF123",
            workflow_name="Test Workflow",
            description="Test",
            steps=[human_step, system_step],
            explanation="Test"
        )
        
        human_steps = workflow.get_human_steps()
        assert len(human_steps) == 1
        assert human_steps[0].step_id == "STEP1"
    
    def test_get_automation_candidates(self):
        """Test getting full automation candidates."""
        full_auto = AutomationOpportunity(
            step_id="STEP1",
            automation_type="full",
            complexity="low",
            estimated_effort="1 week"
        )
        partial_auto = AutomationOpportunity(
            step_id="STEP2",
            automation_type="partial",
            complexity="medium",
            estimated_effort="2 weeks"
        )
        
        workflow = WorkflowStructure(
            workflow_id="WF123",
            workflow_name="Test Workflow",
            description="Test",
            steps=[],
            automation_opportunities=[full_auto, partial_auto],
            explanation="Test"
        )
        
        candidates = workflow.get_automation_candidates()
        assert len(candidates) == 1
        assert candidates[0].step_id == "STEP1"


class TestResearchRecommendations:
    """Tests for ResearchRecommendations model."""
    
    def test_valid_research_recommendations(self):
        """Test creating valid research recommendations."""
        paper = ResearchPaper(
            paper_id="PAPER123",
            title="Treatment of Hypertension",
            authors=["Dr. Smith", "Dr. Jones"],
            abstract="Study on hypertension treatment methods",
            key_findings=["ACE inhibitors effective", "Lifestyle changes important"],
            relevance_score=0.92,
            relevance_explanation="Directly addresses patient condition",
            publication_date="2023-01-15",
            journal="Journal of Cardiology",
            doi="10.1234/jcard.2023.001"
        )
        
        recommendations = ResearchRecommendations(
            recommendation_id="REC123",
            case_description="Patient with uncontrolled hypertension",
            papers=[paper],
            explanation="These papers provide evidence-based treatment approaches"
        )
        
        assert recommendations.recommendation_id == "REC123"
        assert len(recommendations.papers) == 1
        assert recommendations.papers[0].relevance_score == 0.92
    
    def test_get_top_papers(self):
        """Test getting top papers by relevance."""
        paper1 = ResearchPaper(
            paper_id="PAPER1",
            title="Paper 1",
            abstract="Abstract 1",
            relevance_score=0.95,
            relevance_explanation="Highly relevant",
            publication_date="2023-01-01",
            journal="Journal 1"
        )
        paper2 = ResearchPaper(
            paper_id="PAPER2",
            title="Paper 2",
            abstract="Abstract 2",
            relevance_score=0.75,
            relevance_explanation="Somewhat relevant",
            publication_date="2023-01-01",
            journal="Journal 2"
        )
        
        recommendations = ResearchRecommendations(
            recommendation_id="REC123",
            case_description="Test case",
            papers=[paper2, paper1],  # Unsorted
            explanation="Test"
        )
        
        top = recommendations.get_top_papers(1)
        assert len(top) == 1
        assert top[0].paper_id == "PAPER1"


class TestPolicyRecommendations:
    """Tests for PolicyRecommendations model."""
    
    def test_valid_policy_recommendations(self):
        """Test creating valid policy recommendations."""
        alternative = AlternativePolicy(
            policy_id="POL789",
            policy_name="Premium Health",
            provider="XYZ Insurance",
            coverage_differences=["Includes dental", "Higher coverage limit"],
            cost_comparison="15% more expensive but better coverage",
            suitability_score=88.5,
            suitability_reasoning="Better coverage for pre-existing conditions",
            switching_feasibility="moderate"
        )
        
        recommendations = PolicyRecommendations(
            recommendation_id="REC456",
            current_policy_id="POL123",
            unsuitability_reason="Current policy excludes diabetes treatment",
            alternative_policies=[alternative],
            explanation="These alternatives provide better coverage for your needs"
        )
        
        assert recommendations.current_policy_id == "POL123"
        assert len(recommendations.alternative_policies) == 1
    
    def test_get_top_alternatives(self):
        """Test getting top alternatives by suitability."""
        alt1 = AlternativePolicy(
            policy_id="POL1",
            policy_name="Policy 1",
            provider="Provider 1",
            coverage_differences=["Better coverage"],
            cost_comparison="Similar cost",
            suitability_score=95.0,
            suitability_reasoning="Best match",
            switching_feasibility="easy"
        )
        alt2 = AlternativePolicy(
            policy_id="POL2",
            policy_name="Policy 2",
            provider="Provider 2",
            coverage_differences=["Good coverage"],
            cost_comparison="Lower cost",
            suitability_score=80.0,
            suitability_reasoning="Good match",
            switching_feasibility="moderate"
        )
        
        recommendations = PolicyRecommendations(
            recommendation_id="REC456",
            current_policy_id="POL123",
            unsuitability_reason="Test",
            alternative_policies=[alt2, alt1],  # Unsorted
            explanation="Test"
        )
        
        top = recommendations.get_top_alternatives(1)
        assert len(top) == 1
        assert top[0].policy_id == "POL1"
    
    def test_get_easy_switches(self):
        """Test getting policies with easy switching."""
        easy_switch = AlternativePolicy(
            policy_id="POL1",
            policy_name="Policy 1",
            provider="Provider 1",
            coverage_differences=["Better"],
            cost_comparison="Similar",
            suitability_score=90.0,
            suitability_reasoning="Good",
            switching_feasibility="easy"
        )
        difficult_switch = AlternativePolicy(
            policy_id="POL2",
            policy_name="Policy 2",
            provider="Provider 2",
            coverage_differences=["Better"],
            cost_comparison="Similar",
            suitability_score=85.0,
            suitability_reasoning="Good",
            switching_feasibility="difficult"
        )
        
        recommendations = PolicyRecommendations(
            recommendation_id="REC456",
            current_policy_id="POL123",
            unsuitability_reason="Test",
            alternative_policies=[easy_switch, difficult_switch],
            explanation="Test"
        )
        
        easy = recommendations.get_easy_switches()
        assert len(easy) == 1
        assert easy[0].policy_id == "POL1"


class TestSerializationDeserialization:
    """Tests for serialization and deserialization of result models."""
    
    def test_comparison_result_serialization(self):
        """Test ComparisonResult to_dict and from_dict."""
        score = PolicyScore(
            ped_compatibility=85.0,
            cost_effectiveness=70.0,
            coverage_comprehensiveness=90.0,
            claim_settlement_ratio=88.0
        )
        policy = ComparedPolicy(
            policy_id="POL123",
            policy_name="Health Plus",
            provider="ABC Insurance",
            overall_score=83.25,
            score_breakdown=score,
            rejection_risk="low",
            reasoning="Good match"
        )
        
        result = ComparisonResult(
            request_id="REQ123",
            user_profile_id="USER456",
            compared_policies=[policy],
            recommendations=["Test"],
            explanation="Test explanation"
        )
        
        # Serialize
        data = result.to_dict()
        assert isinstance(data, dict)
        assert data['request_id'] == "REQ123"
        
        # Deserialize
        restored = ComparisonResult.from_dict(data)
        assert restored.request_id == result.request_id
        assert restored.user_profile_id == result.user_profile_id
    
    def test_claim_prediction_serialization(self):
        """Test ClaimPrediction to_dict and from_dict."""
        prediction = ClaimPrediction(
            prediction_id="PRED123",
            claim_id="CLM456",
            acceptance_probability=0.75,
            confidence_level="high",
            explanation="High probability of acceptance"
        )
        
        # Serialize
        data = prediction.to_dict()
        assert isinstance(data, dict)
        assert data['prediction_id'] == "PRED123"
        
        # Deserialize
        restored = ClaimPrediction.from_dict(data)
        assert restored.prediction_id == prediction.prediction_id
        assert restored.acceptance_probability == prediction.acceptance_probability
    
    def test_medical_summary_serialization(self):
        """Test MedicalSummary to_dict and from_dict."""
        summary = MedicalSummary(
            summary_id="SUM123",
            patient_id="PAT456",
            summary_text="Patient summary",
            explanation="Key findings"
        )
        
        # Serialize
        data = summary.to_dict()
        assert isinstance(data, dict)
        assert data['summary_id'] == "SUM123"
        
        # Deserialize
        restored = MedicalSummary.from_dict(data)
        assert restored.summary_id == summary.summary_id
        assert restored.patient_id == summary.patient_id
