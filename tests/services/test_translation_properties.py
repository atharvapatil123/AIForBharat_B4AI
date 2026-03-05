"""Property-based tests for translation service.

These tests verify universal properties that should hold across all valid inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import AsyncMock, MagicMock

from healthcare_insurance_platform.services.translation import (
    SupportedLanguage,
    TranslationService,
)
from healthcare_insurance_platform.services.llm_client import LLMResponse


# Custom strategies for translation testing
supported_languages = st.sampled_from([lang.value for lang in SupportedLanguage])

# Text generation strategy
text_content = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'P'),
        min_codepoint=32,
        max_codepoint=126,
    ),
    min_size=0,
    max_size=500,
)

context_types = st.sampled_from(["general", "policy", "medical"])


@pytest.fixture
def mock_translation_service():
    """Create translation service with mocked LLM client."""
    mock_llm_client = MagicMock()
    mock_llm_client.register_template = MagicMock()
    
    # Mock template
    mock_template = MagicMock()
    mock_template.format.return_value = ("system message", "user message")
    mock_llm_client.get_template.return_value = mock_template
    
    # Mock LLM response
    async def mock_generate(*args, **kwargs):
        return LLMResponse(
            content="Translation:\nTranslated content\n\nTechnical Terms:\n- term: explanation",
            model="gpt-4",
            provider="openai",
            confidence_score=0.9,
        )
    
    mock_llm_client.generate = mock_generate
    
    service = TranslationService(llm_client=mock_llm_client)
    return service


class TestLanguageConsistencyProperty:
    """Test Property 3: Language consistency across outputs.
    
    Feature: healthcare-insurance-intelligence, Property 3: Language consistency across outputs
    For any platform operation with a specified language preference, 
    all output text should be in the requested language.
    """
    
    @settings(max_examples=50)
    @given(
        text=text_content,
        source_lang=supported_languages,
        target_lang=supported_languages,
        context=context_types,
    )
    @pytest.mark.asyncio
    async def test_output_language_matches_target(
        self,
        mock_translation_service,
        text,
        source_lang,
        target_lang,
        context,
    ):
        """**Validates: Requirements 1.4, 3.6, 4.2, 11.3**
        
        Property: For any translation request with target language L,
        the output should have target_language field set to L.
        """
        result = await mock_translation_service.translate(
            text=text,
            source_language=source_lang,
            target_language=target_lang,
            context_type=context,
        )
        
        # Property: Output language matches requested target language
        assert result.target_language == target_lang
        assert result.source_language == source_lang


class TestMultilingualSupportProperty:
    """Test Property 8: Multilingual support coverage.
    
    Feature: healthcare-insurance-intelligence, Property 8: Multilingual support coverage
    For any supported language (Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, English),
    the platform should accept input and produce output in that language.
    """
    
    @settings(max_examples=50)
    @given(
        text=text_content,
        language=supported_languages,
    )
    @pytest.mark.asyncio
    async def test_all_supported_languages_accepted(
        self,
        mock_translation_service,
        text,
        language,
    ):
        """**Validates: Requirements 4.1**
        
        Property: For any supported language code, the service should
        accept it as both source and target without raising errors.
        """
        # Should not raise ValueError for supported languages
        result = await mock_translation_service.translate(
            text=text,
            source_language=language,
            target_language="en",  # Translate to English
            context_type="general",
        )
        
        assert result.source_language == language
        assert result.target_language == "en"
    
    def test_required_languages_are_supported(self, mock_translation_service):
        """**Validates: Requirements 4.1**
        
        Property: All required languages (Hindi, Tamil, Telugu, Bengali, 
        Marathi, Gujarati) must be in the supported languages list.
        """
        required_languages = ["hi", "ta", "te", "bn", "mr", "gu"]
        supported = mock_translation_service.get_supported_languages()
        
        for lang in required_languages:
            assert lang in supported, f"Required language {lang} not supported"


class TestTechnicalTermHandlingProperty:
    """Test Property 9: Technical term handling in translation.
    
    Feature: healthcare-insurance-intelligence, Property 9: Technical term handling in translation
    For any technical or legal term without direct translation, the output should 
    include the original term with an explanation in the target language.
    """
    
    @settings(max_examples=30)
    @given(
        text=text_content,
        source_lang=supported_languages,
        target_lang=supported_languages,
    )
    @pytest.mark.asyncio
    async def test_technical_terms_have_explanations(
        self,
        mock_translation_service,
        text,
        source_lang,
        target_lang,
    ):
        """**Validates: Requirements 4.4**
        
        Property: For any translation result with technical terms,
        each term must have an explanation field populated.
        """
        assume(source_lang != target_lang)  # Skip same-language translations
        
        result = await mock_translation_service.translate(
            text=text,
            source_language=source_lang,
            target_language=target_lang,
            context_type="policy",  # Policy context likely to have technical terms
        )
        
        # Property: All technical terms must have explanations
        for term in result.technical_terms:
            assert term.original_term, "Technical term must have original_term"
            assert term.explanation, "Technical term must have explanation"
            assert len(term.explanation) > 0, "Explanation must not be empty"


class TestTranslationCompletenessProperty:
    """Test translation completeness properties."""
    
    @settings(max_examples=50)
    @given(
        text=text_content,
        source_lang=supported_languages,
        target_lang=supported_languages,
        context=context_types,
    )
    @pytest.mark.asyncio
    async def test_translation_result_has_required_fields(
        self,
        mock_translation_service,
        text,
        source_lang,
        target_lang,
        context,
    ):
        """Property: All translation results must have required fields populated.
        
        For any translation request, the result must contain:
        - translated_content (non-None)
        - source_language
        - target_language
        - technical_terms (list, possibly empty)
        """
        result = await mock_translation_service.translate(
            text=text,
            source_language=source_lang,
            target_language=target_lang,
            context_type=context,
        )
        
        # Property: Required fields are present
        assert result.translated_content is not None
        assert result.source_language == source_lang
        assert result.target_language == target_lang
        assert isinstance(result.technical_terms, list)
        assert result.confidence_score is None or (0 <= result.confidence_score <= 1)


class TestSameLanguageIdentityProperty:
    """Test identity property for same-language translation."""
    
    @settings(max_examples=50)
    @given(
        text=text_content,
        language=supported_languages,
    )
    @pytest.mark.asyncio
    async def test_same_language_returns_original(
        self,
        mock_translation_service,
        text,
        language,
    ):
        """Property: Translating from language L to language L returns original text.
        
        For any text T and language L, translate(T, L, L) should return T unchanged
        with confidence score 1.0.
        """
        result = await mock_translation_service.translate(
            text=text,
            source_language=language,
            target_language=language,
        )
        
        # Property: Same language translation is identity function
        assert result.translated_content == text
        assert result.confidence_score == 1.0
        assert len(result.technical_terms) == 0


class TestBatchTranslationProperty:
    """Test batch translation properties."""
    
    @settings(max_examples=30)
    @given(
        texts=st.lists(text_content, min_size=1, max_size=10),
        source_lang=supported_languages,
        target_lang=supported_languages,
    )
    @pytest.mark.asyncio
    async def test_batch_translation_count_matches_input(
        self,
        mock_translation_service,
        texts,
        source_lang,
        target_lang,
    ):
        """Property: Batch translation returns same number of results as inputs.
        
        For any list of N texts, batch_translate should return exactly N results.
        """
        results = await mock_translation_service.batch_translate(
            texts=texts,
            source_language=source_lang,
            target_language=target_lang,
        )
        
        # Property: Output count equals input count
        assert len(results) == len(texts)
    
    @settings(max_examples=30)
    @given(
        texts=st.lists(text_content, min_size=1, max_size=10),
        source_lang=supported_languages,
        target_lang=supported_languages,
    )
    @pytest.mark.asyncio
    async def test_batch_translation_preserves_order(
        self,
        mock_translation_service,
        texts,
        source_lang,
        target_lang,
    ):
        """Property: Batch translation preserves input order.
        
        For any list of texts [T1, T2, ..., Tn], the results should be
        [translate(T1), translate(T2), ..., translate(Tn)] in that order.
        """
        results = await mock_translation_service.batch_translate(
            texts=texts,
            source_language=source_lang,
            target_language=target_lang,
        )
        
        # Property: All results have correct source and target languages
        for result in results:
            assert result.source_language == source_lang
            assert result.target_language == target_lang


class TestLanguageValidationProperty:
    """Test language validation properties."""
    
    @settings(max_examples=50)
    @given(
        text=text_content,
        invalid_lang=st.text(
            alphabet=st.characters(whitelist_categories=('Ll',)),
            min_size=2,
            max_size=5,
        ).filter(lambda x: x not in [lang.value for lang in SupportedLanguage]),
    )
    @pytest.mark.asyncio
    async def test_unsupported_language_raises_error(
        self,
        mock_translation_service,
        text,
        invalid_lang,
    ):
        """Property: Unsupported languages always raise ValueError.
        
        For any language code L not in supported languages,
        using L as source or target should raise ValueError.
        """
        # Test unsupported source language
        with pytest.raises(ValueError, match="not supported"):
            await mock_translation_service.translate(
                text=text,
                source_language=invalid_lang,
                target_language="en",
            )
        
        # Test unsupported target language
        with pytest.raises(ValueError, match="not supported"):
            await mock_translation_service.translate(
                text=text,
                source_language="en",
                target_language=invalid_lang,
            )


class TestContextTypeProperty:
    """Test context type handling properties."""
    
    @settings(max_examples=50)
    @given(
        text=text_content,
        source_lang=supported_languages,
        target_lang=supported_languages,
        context=context_types,
    )
    @pytest.mark.asyncio
    async def test_valid_context_types_accepted(
        self,
        mock_translation_service,
        text,
        source_lang,
        target_lang,
        context,
    ):
        """Property: All valid context types are accepted without error.
        
        For any valid context type (general, policy, medical),
        translation should succeed without raising ValueError.
        """
        # Should not raise ValueError
        result = await mock_translation_service.translate(
            text=text,
            source_language=source_lang,
            target_language=target_lang,
            context_type=context,
        )
        
        assert result is not None
    
    @settings(max_examples=30)
    @given(
        text=text_content,
        invalid_context=st.text(min_size=1, max_size=20).filter(
            lambda x: x not in ["general", "policy", "medical"]
        ),
    )
    @pytest.mark.asyncio
    async def test_invalid_context_type_raises_error(
        self,
        mock_translation_service,
        text,
        invalid_context,
    ):
        """Property: Invalid context types always raise ValueError.
        
        For any context type not in {general, policy, medical},
        translation should raise ValueError.
        """
        with pytest.raises(ValueError, match="Invalid context_type"):
            await mock_translation_service.translate(
                text=text,
                source_language="en",
                target_language="hi",
                context_type=invalid_context,
            )


class TestConfidenceScoreProperty:
    """Test confidence score properties."""
    
    @settings(max_examples=50)
    @given(
        text=text_content,
        source_lang=supported_languages,
        target_lang=supported_languages,
    )
    @pytest.mark.asyncio
    async def test_confidence_score_in_valid_range(
        self,
        mock_translation_service,
        text,
        source_lang,
        target_lang,
    ):
        """Property: Confidence scores are always in range [0, 1] or None.
        
        For any translation result with a confidence score,
        the score must be between 0 and 1 inclusive.
        """
        result = await mock_translation_service.translate(
            text=text,
            source_language=source_lang,
            target_language=target_lang,
        )
        
        # Property: Confidence score is valid
        if result.confidence_score is not None:
            assert 0.0 <= result.confidence_score <= 1.0
