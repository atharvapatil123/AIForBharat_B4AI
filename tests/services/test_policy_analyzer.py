"""Unit tests for Policy Analyzer service."""

import pytest
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from healthcare_insurance_platform.models.policy import (
    DocumentRequirement,
    ParsedClause,
    PolicyDocument,
    WaitingPeriod,
)
from healthcare_insurance_platform.models.user_profile import (
    Demographics,
    MedicalHistory,
    PreExistingDisease,
    UserProfile,
)
from healthcare_insurance_platform.services.policy_analyzer import (
    PolicyAnalyzer,
    PolicyFilters,
)


@pytest.fixture
def sample_user_profile():
    """Create a sample user profile for testing."""
    return UserProfile(
        user_id="user123",
        demographics=Demographics(
            age=35,
            gender="male",
            location="Mumbai",
        ),
        medical_history=MedicalHistory(
            pre_existing_diseases=[
                PreExistingDisease(
                    condition="Hypertension",
                    diagnosis_date=date(2020, 1, 1),
                    severity="moderate",
                ),
                PreExistingDisease(
                    condition="Diabetes",
                    diagnosis_date=date(2019, 6, 15),
                    severity="mild",
                ),
            ],
            current_medications=[],
            allergies=[],
            past_surgeries=[],
        ),
        language_preference="en",
        consent_given=True,
    )


@pytest.fixture
def sample_policy():
    """Create a sample policy document for testing."""
    return PolicyDocument(
        policy_id="policy123",
        provider_id="provider1",
        policy_name="Comprehensive Health Plan",
        policy_type="individual",
        version="1.0",
        effective_date=date.today(),
        coverage_amount=500000.0,
        premium=12000.0,
        waiting_periods=WaitingPeriod(
            general=30,
            pre_existing=730,
            specific_conditions=[],
        ),
        inclusions=[
            "Hospitalization expenses",
            "Surgical procedures",
            "Diagnostic tests",
            "Ambulance charges",
            "Day care procedures",
        ],
        exclusions=[
            "Cosmetic procedures",
            "Dental treatment",
            "Infertility treatment",
        ],
        ped_policy="Pre-existing diseases covered after 2-year waiting period",
        claim_process="Submit claim with required documents within 30 days",
        document_requirements=[
            DocumentRequirement(
                claim_type="hospitalization",
                documents=["Hospital discharge summary", "Medical bills", "Diagnostic reports"],
            ),
        ],
        full_text="Sample policy document text",
        parsed_clauses=[
            ParsedClause(
                clause_type="coverage",
                text="Coverage amount: Rs. 5,00,000",
                importance="critical",
            ),
        ],
    )


@pytest.fixture
def policy_analyzer():
    """Create a PolicyAnalyzer instance with mocked dependencies."""
    # Mock dependencies
    mock_kb = MagicMock()
    mock_llm = MagicMock()
    mock_translation = MagicMock()
    
    analyzer = PolicyAnalyzer(
        knowledge_base=mock_kb,
        llm_engine=mock_llm,
        translation_service=mock_translation,
    )
    
    return analyzer


class TestPolicyAnalyzer:
    """Test suite for PolicyAnalyzer service."""
    
    @pytest.mark.asyncio
    async def test_compare_plans_basic(
        self,
        policy_analyzer,
        sample_user_profile,
        sample_policy,
    ):
        """Test basic policy comparison functionality."""
        # Mock knowledge base to return sample policy
        policy_analyzer.knowledge_base.search_policies = AsyncMock(
            return_value=[
                {
                    'policy_id': sample_policy.policy_id,
                    'policy_name': sample_policy.policy_name,
                    'provider_id': sample_policy.provider_id,
                    'policy_type': sample_policy.policy_type,
                    'content': sample_policy.full_text,
                    'metadata': {
                        'coverage_amount': sample_policy.coverage_amount,
                        'premium': sample_policy.premium,
                        'version': sample_policy.version,
                    },
                }
            ]
        )
        
        # Mock translation service
        policy_analyzer.translation_service.translate = AsyncMock(
            side_effect=lambda text, **kwargs: MagicMock(translated_content=text)
        )
        
        # Execute comparison
        result = await policy_analyzer.compare_plans(
            user_profile=sample_user_profile,
            filters=None,
            language="en",
            max_policies=10,
        )
        
        # Assertions
        assert result is not None
        assert result.user_profile_id == sample_user_profile.user_id
        assert len(result.compared_policies) > 0
        assert len(result.recommendations) > 0
        assert result.explanation
        assert result.language == "en"
        
        # Check first policy
        first_policy = result.compared_policies[0]
        assert first_policy.policy_id == sample_policy.policy_id
        assert first_policy.policy_name == sample_policy.policy_name
        assert 0 <= first_policy.overall_score <= 100
        assert first_policy.rejection_risk in ['low', 'medium', 'high']
    
    @pytest.mark.asyncio
    async def test_compare_plans_with_filters(
        self,
        policy_analyzer,
        sample_user_profile,
        sample_policy,
    ):
        """Test policy comparison with filters applied."""
        # Create filters
        filters = PolicyFilters(
            min_coverage=300000.0,
            max_premium=15000.0,
            policy_type="individual",
        )
        
        # Mock knowledge base
        policy_analyzer.knowledge_base.search_policies = AsyncMock(
            return_value=[
                {
                    'policy_id': sample_policy.policy_id,
                    'policy_name': sample_policy.policy_name,
                    'provider_id': sample_policy.provider_id,
                    'policy_type': sample_policy.policy_type,
                    'content': sample_policy.full_text,
                    'metadata': {
                        'coverage_amount': sample_policy.coverage_amount,
                        'premium': sample_policy.premium,
                        'version': sample_policy.version,
                    },
                }
            ]
        )
        
        # Mock translation
        policy_analyzer.translation_service.translate = AsyncMock(
            side_effect=lambda text, **kwargs: MagicMock(translated_content=text)
        )
        
        # Execute comparison
        result = await policy_analyzer.compare_plans(
            user_profile=sample_user_profile,
            filters=filters,
            language="en",
        )
        
        # Verify filters were applied
        assert result is not None
        assert len(result.compared_policies) > 0
        
        # Verify knowledge base was called with filters
        policy_analyzer.knowledge_base.search_policies.assert_called_once()
        call_args = policy_analyzer.knowledge_base.search_policies.call_args
        assert call_args[1]['filters'] is not None
    
    @pytest.mark.asyncio
    async def test_compare_plans_no_policies_found(
        self,
        policy_analyzer,
        sample_user_profile,
    ):
        """Test error handling when no policies match filters."""
        # Mock knowledge base to return empty results
        policy_analyzer.knowledge_base.search_policies = AsyncMock(
            return_value=[]
        )
        
        # Execute and expect ValueError
        with pytest.raises(ValueError, match="No policies found"):
            await policy_analyzer.compare_plans(
                user_profile=sample_user_profile,
                filters=None,
                language="en",
            )
    
    def test_calculate_ped_compatibility_score_no_peds(
        self,
        policy_analyzer,
        sample_policy,
    ):
        """Test PED compatibility score when user has no PEDs."""
        # Create user profile without PEDs
        user_profile = UserProfile(
            user_id="user123",
            demographics=Demographics(age=25, gender="female", location="Delhi"),
            medical_history=MedicalHistory(),
            language_preference="en",
            consent_given=True,
        )
        
        score = policy_analyzer._calculate_ped_compatibility_score(
            sample_policy,
            user_profile,
        )
        
        # Should return perfect score
        assert score == 100.0
    
    def test_calculate_ped_compatibility_score_with_exclusions(
        self,
        policy_analyzer,
        sample_user_profile,
    ):
        """Test PED compatibility score when policy excludes user's conditions."""
        # Create policy that excludes diabetes
        policy = PolicyDocument(
            policy_id="policy123",
            provider_id="provider1",
            policy_name="Limited Health Plan",
            policy_type="individual",
            version="1.0",
            effective_date=date.today(),
            coverage_amount=300000.0,
            premium=8000.0,
            waiting_periods=WaitingPeriod(general=30, pre_existing=1095, specific_conditions=[]),
            inclusions=["Hospitalization", "Surgery"],
            exclusions=["Diabetes-related complications", "Hypertension treatment"],
            ped_policy="Limited PED coverage",
            claim_process="Standard process",
            document_requirements=[
                DocumentRequirement(claim_type="hospitalization", documents=["Bills"]),
            ],
            full_text="Policy text",
            parsed_clauses=[
                ParsedClause(clause_type="coverage", text="Coverage", importance="high"),
            ],
        )
        
        score = policy_analyzer._calculate_ped_compatibility_score(
            policy,
            sample_user_profile,
        )
        
        # Score should be low due to exclusions
        assert score < 50.0
    
    def test_calculate_cost_effectiveness_score(
        self,
        policy_analyzer,
        sample_policy,
        sample_user_profile,
    ):
        """Test cost effectiveness score calculation."""
        score = policy_analyzer._calculate_cost_effectiveness_score(
            sample_policy,
            sample_user_profile,
        )
        
        # Premium is 12000 for 500000 coverage = 2.4%
        # Should get a score around 60-80
        assert 40.0 <= score <= 100.0
    
    def test_calculate_cost_effectiveness_score_senior_citizen(
        self,
        policy_analyzer,
        sample_policy,
    ):
        """Test cost effectiveness score for senior citizens."""
        # Create senior citizen profile
        senior_profile = UserProfile(
            user_id="senior123",
            demographics=Demographics(age=65, gender="male", location="Bangalore"),
            medical_history=MedicalHistory(),
            language_preference="en",
            consent_given=True,
        )
        
        score = policy_analyzer._calculate_cost_effectiveness_score(
            sample_policy,
            senior_profile,
        )
        
        # Senior citizens should get adjusted (more lenient) scores
        assert score >= 0.0
    
    def test_calculate_coverage_score(
        self,
        policy_analyzer,
        sample_policy,
    ):
        """Test coverage comprehensiveness score calculation."""
        score = policy_analyzer._calculate_coverage_score(sample_policy)
        
        # Sample policy has 5 inclusions, should get moderate score
        assert 30.0 <= score <= 100.0
    
    def test_calculate_coverage_score_comprehensive(
        self,
        policy_analyzer,
    ):
        """Test coverage score for comprehensive policy."""
        # Create policy with many inclusions
        comprehensive_policy = PolicyDocument(
            policy_id="comp123",
            provider_id="provider1",
            policy_name="Comprehensive Plan",
            policy_type="individual",
            version="1.0",
            effective_date=date.today(),
            coverage_amount=1000000.0,
            premium=20000.0,
            waiting_periods=WaitingPeriod(general=30, pre_existing=730, specific_conditions=[]),
            inclusions=[
                "Hospitalization expenses",
                "Surgical procedures",
                "Diagnostic tests",
                "Ambulance charges",
                "Day care procedures",
                "Maternity coverage",
                "Organ transplant",
                "Cancer treatment",
                "Cardiac procedures",
                "ICU charges",
                "Pre-hospitalization",
                "Post-hospitalization",
                "Home healthcare",
                "Mental health",
                "Physiotherapy",
            ],
            exclusions=["Cosmetic procedures"],
            ped_policy="Comprehensive PED coverage",
            claim_process="Standard",
            document_requirements=[
                DocumentRequirement(claim_type="hospitalization", documents=["Bills"]),
            ],
            full_text="Policy text",
            parsed_clauses=[
                ParsedClause(clause_type="coverage", text="Coverage", importance="high"),
            ],
        )
        
        score = policy_analyzer._calculate_coverage_score(comprehensive_policy)
        
        # Should get high score
        assert score >= 70.0
    
    def test_calculate_rejection_risk_no_peds(
        self,
        policy_analyzer,
        sample_policy,
    ):
        """Test rejection risk when user has no PEDs."""
        user_profile = UserProfile(
            user_id="user123",
            demographics=Demographics(age=25, gender="female", location="Delhi"),
            medical_history=MedicalHistory(),
            language_preference="en",
            consent_given=True,
        )
        
        risk = policy_analyzer._calculate_rejection_risk(
            sample_policy,
            user_profile,
            ped_score=100.0,
        )
        
        assert risk == "low"
    
    def test_calculate_rejection_risk_with_exclusions(
        self,
        policy_analyzer,
        sample_user_profile,
    ):
        """Test rejection risk when policy excludes user's conditions."""
        # Create policy that excludes both conditions
        policy = PolicyDocument(
            policy_id="policy123",
            provider_id="provider1",
            policy_name="Limited Plan",
            policy_type="individual",
            version="1.0",
            effective_date=date.today(),
            coverage_amount=300000.0,
            premium=8000.0,
            waiting_periods=WaitingPeriod(general=30, pre_existing=730, specific_conditions=[]),
            inclusions=["Hospitalization"],
            exclusions=["Diabetes", "Hypertension"],
            ped_policy="Limited",
            claim_process="Standard",
            document_requirements=[
                DocumentRequirement(claim_type="hospitalization", documents=["Bills"]),
            ],
            full_text="Policy text",
            parsed_clauses=[
                ParsedClause(clause_type="coverage", text="Coverage", importance="high"),
            ],
        )
        
        risk = policy_analyzer._calculate_rejection_risk(
            policy,
            sample_user_profile,
            ped_score=20.0,
        )
        
        assert risk == "high"
    
    def test_generate_pros_cons(
        self,
        policy_analyzer,
        sample_policy,
        sample_user_profile,
    ):
        """Test pros and cons generation."""
        scores = {
            'ped': 85.0,
            'cost': 75.0,
            'coverage': 70.0,
            'claim_ratio': 85.0,
        }
        
        pros, cons = policy_analyzer._generate_pros_cons(
            sample_policy,
            sample_user_profile,
            scores,
        )
        
        # Should have both pros and cons
        assert len(pros) > 0
        assert isinstance(pros, list)
        assert isinstance(cons, list)
        
        # Check for expected content
        assert any("compatibility" in pro.lower() or "coverage" in pro.lower() for pro in pros)
    
    def test_generate_policy_reasoning(
        self,
        policy_analyzer,
        sample_policy,
        sample_user_profile,
    ):
        """Test policy reasoning generation."""
        reasoning = policy_analyzer._generate_policy_reasoning(
            policy=sample_policy,
            user_profile=sample_user_profile,
            overall_score=75.0,
            ped_score=80.0,
            cost_score=70.0,
            rejection_risk="low",
        )
        
        # Should return non-empty string
        assert reasoning
        assert isinstance(reasoning, str)
        assert len(reasoning) > 50  # Should be substantial
        
        # Should mention key aspects
        assert "policy" in reasoning.lower()
    
    def test_extract_inclusions_from_content(
        self,
        policy_analyzer,
    ):
        """Test extraction of inclusions from policy content."""
        content = """
        This policy covers hospitalization expenses, surgical procedures,
        diagnostic tests, and ambulance charges. Day care procedures are
        also included in the coverage.
        """
        
        inclusions = policy_analyzer._extract_inclusions_from_content(content)
        
        assert len(inclusions) > 0
        assert any("hospitalization" in inc.lower() for inc in inclusions)
        assert any("surgical" in inc.lower() or "surgery" in inc.lower() for inc in inclusions)
    
    def test_extract_exclusions_from_content(
        self,
        policy_analyzer,
    ):
        """Test extraction of exclusions from policy content."""
        content = """
        This policy does not cover cosmetic procedures, dental treatment,
        or infertility treatment. War-related injuries and self-inflicted
        injuries are also excluded.
        """
        
        exclusions = policy_analyzer._extract_exclusions_from_content(content)
        
        assert len(exclusions) > 0
        assert any("cosmetic" in exc.lower() for exc in exclusions)
        assert any("dental" in exc.lower() for exc in exclusions)
    
    @pytest.mark.asyncio
    async def test_multilingual_support(
        self,
        policy_analyzer,
        sample_user_profile,
        sample_policy,
    ):
        """Test multilingual output support."""
        # Mock knowledge base
        policy_analyzer.knowledge_base.search_policies = AsyncMock(
            return_value=[
                {
                    'policy_id': sample_policy.policy_id,
                    'policy_name': sample_policy.policy_name,
                    'provider_id': sample_policy.provider_id,
                    'policy_type': sample_policy.policy_type,
                    'content': sample_policy.full_text,
                    'metadata': {
                        'coverage_amount': sample_policy.coverage_amount,
                        'premium': sample_policy.premium,
                        'version': sample_policy.version,
                    },
                }
            ]
        )
        
        # Mock translation service to return Hindi translations
        policy_analyzer.translation_service.translate = AsyncMock(
            side_effect=lambda text, **kwargs: MagicMock(
                translated_content=f"[HI] {text}"
            )
        )
        
        # Execute comparison in Hindi
        result = await policy_analyzer.compare_plans(
            user_profile=sample_user_profile,
            filters=None,
            language="hi",
        )
        
        # Verify translation was called
        assert policy_analyzer.translation_service.translate.called
        assert result.language == "hi"
    
    def test_extract_policy_citations(
        self,
        policy_analyzer,
        sample_policy,
    ):
        """Test extraction of policy citations."""
        policies = [sample_policy]
        
        citations = policy_analyzer._extract_policy_citations(policies)
        
        assert len(citations) == 1
        assert sample_policy.policy_id in citations[0]
        assert sample_policy.policy_name in citations[0]
        assert sample_policy.provider_id in citations[0]


class TestPolicyFilters:
    """Test suite for PolicyFilters model."""
    
    def test_policy_filters_creation(self):
        """Test creating policy filters."""
        filters = PolicyFilters(
            min_coverage=300000.0,
            max_premium=15000.0,
            policy_type="individual",
            required_benefits=["Hospitalization", "Surgery"],
        )
        
        assert filters.min_coverage == 300000.0
        assert filters.max_premium == 15000.0
        assert filters.policy_type == "individual"
        assert len(filters.required_benefits) == 2
    
    def test_policy_filters_optional_fields(self):
        """Test policy filters with optional fields."""
        filters = PolicyFilters()
        
        assert filters.min_coverage is None
        assert filters.max_coverage is None
        assert filters.min_premium is None
        assert filters.max_premium is None
        assert filters.policy_type is None
        assert filters.provider_id is None
        assert len(filters.required_benefits) == 0


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_compare_plans_single_policy(
        self,
        policy_analyzer,
        sample_user_profile,
        sample_policy,
    ):
        """Test comparison with only one policy."""
        policy_analyzer.knowledge_base.search_policies = AsyncMock(
            return_value=[
                {
                    'policy_id': sample_policy.policy_id,
                    'policy_name': sample_policy.policy_name,
                    'provider_id': sample_policy.provider_id,
                    'policy_type': sample_policy.policy_type,
                    'content': sample_policy.full_text,
                    'metadata': {
                        'coverage_amount': sample_policy.coverage_amount,
                        'premium': sample_policy.premium,
                        'version': sample_policy.version,
                    },
                }
            ]
        )
        
        policy_analyzer.translation_service.translate = AsyncMock(
            side_effect=lambda text, **kwargs: MagicMock(translated_content=text)
        )
        
        result = await policy_analyzer.compare_plans(
            user_profile=sample_user_profile,
            filters=None,
            language="en",
        )
        
        # Should still work with single policy
        assert len(result.compared_policies) == 1
        assert len(result.recommendations) > 0
    
    def test_score_policy_extreme_values(
        self,
        policy_analyzer,
        sample_user_profile,
    ):
        """Test scoring with extreme policy values."""
        # Create policy with extreme values
        extreme_policy = PolicyDocument(
            policy_id="extreme123",
            provider_id="provider1",
            policy_name="Extreme Plan",
            policy_type="individual",
            version="1.0",
            effective_date=date.today(),
            coverage_amount=10000000.0,  # Very high coverage
            premium=500000.0,  # Very high premium
            waiting_periods=WaitingPeriod(general=0, pre_existing=3650, specific_conditions=[]),
            inclusions=["Basic coverage"],
            exclusions=["Almost everything"],
            ped_policy="Limited",
            claim_process="Standard",
            document_requirements=[
                DocumentRequirement(claim_type="hospitalization", documents=["Bills"]),
            ],
            full_text="Policy text",
            parsed_clauses=[
                ParsedClause(clause_type="coverage", text="Coverage", importance="high"),
            ],
        )
        
        # Should not crash with extreme values
        score = policy_analyzer._calculate_cost_effectiveness_score(
            extreme_policy,
            sample_user_profile,
        )
        
        assert 0.0 <= score <= 100.0
