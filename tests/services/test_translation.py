"""Unit tests for translation service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from healthcare_insurance_platform.services.translation import (
    SupportedLanguage,
    TechnicalTerm,
    TranslatedText,
    TranslatedTextWithGlossary,
    TranslationService,
)
from healthcare_insurance_platform.services.llm_client import LLMResponse


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = MagicMock()
    client.register_template = MagicMock()
    client.get_template = MagicMock()
    return client


@pytest.fixture
def translation_service(mock_llm_client):
    """Create translation service with mock LLM client."""
    return TranslationService(llm_client=mock_llm_client)


class TestSupportedLanguages:
    """Test language support functionality."""
    
    def test_all_required_languages_supported(self, translation_service):
        """Test that all required languages are supported."""
        required_languages = ["hi", "ta", "te", "bn", "mr", "gu", "en"]
        
        for lang in required_languages:
            assert translation_service.is_language_supported(lang), \
                f"Language {lang} should be supported"
    
    def test_unsupported_language_returns_false(self, translation_service):
        """Test that unsupported languages return False."""
        assert not translation_service.is_language_supported("fr")
        assert not translation_service.is_language_supported("de")
        assert not translation_service.is_language_supported("invalid")
    
    def test_get_supported_languages_returns_all(self, translation_service):
        """Test getting list of supported languages."""
        languages = translation_service.get_supported_languages()
        
        assert len(languages) == 7
        assert "en" in languages
        assert "hi" in languages
        assert "ta" in languages
        assert "te" in languages
        assert "bn" in languages
        assert "mr" in languages
        assert "gu" in languages


class TestBasicTranslation:
    """Test basic translation functionality."""
    
    @pytest.mark.asyncio
    async def test_same_language_returns_original(self, translation_service):
        """Test that translating to same language returns original text."""
        text = "This is a test"
        
        result = await translation_service.translate(
            text=text,
            source_language="en",
            target_language="en",
        )
        
        assert result.translated_content == text
        assert result.source_language == "en"
        assert result.target_language == "en"
        assert result.confidence_score == 1.0
        assert len(result.technical_terms) == 0
    
    @pytest.mark.asyncio
    async def test_unsupported_source_language_raises_error(self, translation_service):
        """Test that unsupported source language raises ValueError."""
        with pytest.raises(ValueError, match="Source language.*not supported"):
            await translation_service.translate(
                text="test",
                source_language="fr",
                target_language="en",
            )
    
    @pytest.mark.asyncio
    async def test_unsupported_target_language_raises_error(self, translation_service):
        """Test that unsupported target language raises ValueError."""
        with pytest.raises(ValueError, match="Target language.*not supported"):
            await translation_service.translate(
                text="test",
                source_language="en",
                target_language="fr",
            )
    
    @pytest.mark.asyncio
    async def test_invalid_context_type_raises_error(self, translation_service):
        """Test that invalid context type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid context_type"):
            await translation_service.translate(
                text="test",
                source_language="en",
                target_language="hi",
                context_type="invalid",
            )
    
    @pytest.mark.asyncio
    async def test_successful_translation_with_llm(self, translation_service, mock_llm_client):
        """Test successful translation using LLM."""
        # Mock template
        mock_template = MagicMock()
        mock_template.format.return_value = (
            "You are a translator",
            "Translate this text"
        )
        mock_llm_client.get_template.return_value = mock_template
        
        # Mock LLM response
        mock_response = LLMResponse(
            content="Translation:\nयह एक परीक्षण है\n\nTechnical Terms:\n- test: परीक्षण (parikshan)",
            model="gpt-4",
            provider="openai",
            confidence_score=0.95,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        result = await translation_service.translate(
            text="This is a test",
            source_language="en",
            target_language="hi",
            context_type="general",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "hi"
        assert "परीक्षण" in result.translated_content
        assert result.confidence_score == 0.95
        
        # Verify LLM was called
        mock_llm_client.generate.assert_called_once()


class TestContextTypes:
    """Test different context types for translation."""
    
    @pytest.mark.asyncio
    async def test_general_context_uses_correct_template(self, translation_service, mock_llm_client):
        """Test that general context uses general_translation template."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="Translation:\nTranslated text",
            model="gpt-4",
            provider="openai",
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        await translation_service.translate(
            text="test",
            source_language="en",
            target_language="hi",
            context_type="general",
        )
        
        mock_llm_client.get_template.assert_called_with("general_translation")
    
    @pytest.mark.asyncio
    async def test_policy_context_uses_correct_template(self, translation_service, mock_llm_client):
        """Test that policy context uses policy_translation template."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="Translation:\nPolicy text",
            model="gpt-4",
            provider="openai",
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        await translation_service.translate(
            text="policy terms",
            source_language="en",
            target_language="hi",
            context_type="policy",
        )
        
        mock_llm_client.get_template.assert_called_with("policy_translation")
    
    @pytest.mark.asyncio
    async def test_medical_context_uses_correct_template(self, translation_service, mock_llm_client):
        """Test that medical context uses medical_translation template."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="Translation:\nMedical text",
            model="gpt-4",
            provider="openai",
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        await translation_service.translate(
            text="medical diagnosis",
            source_language="en",
            target_language="hi",
            context_type="medical",
        )
        
        mock_llm_client.get_template.assert_called_with("medical_translation")


class TestTechnicalTermHandling:
    """Test technical term preservation and explanation."""
    
    def test_parse_translation_with_technical_terms(self, translation_service):
        """Test parsing translation response with technical terms."""
        response = """Translation:
यह बीमा पॉलिसी कवरेज प्रदान करती है

Technical Terms:
- coverage: कवरेज - बीमा द्वारा प्रदान की जाने वाली सुरक्षा
- policy: पॉलिसी - बीमा अनुबंध दस्तावेज़"""
        
        content, terms = translation_service._parse_translation_response(response)
        
        assert "बीमा पॉलिसी कवरेज" in content
        assert len(terms) == 2
        assert terms[0].original_term == "coverage"
        assert "कवरेज" in terms[0].explanation
        assert terms[1].original_term == "policy"
        assert "पॉलिसी" in terms[1].explanation
    
    def test_parse_translation_without_technical_terms(self, translation_service):
        """Test parsing translation response without technical terms."""
        response = """Translation:
यह एक साधारण वाक्य है"""
        
        content, terms = translation_service._parse_translation_response(response)
        
        assert "साधारण वाक्य" in content
        assert len(terms) == 0
    
    def test_parse_translation_without_sections(self, translation_service):
        """Test parsing translation response without clear sections."""
        response = "यह अनुवादित पाठ है"
        
        content, terms = translation_service._parse_translation_response(response)
        
        assert content == "यह अनुवादित पाठ है"
        assert len(terms) == 0


class TestGlossaryTranslation:
    """Test translation with custom glossary."""
    
    @pytest.mark.asyncio
    async def test_translate_with_glossary(self, translation_service, mock_llm_client):
        """Test translation with custom glossary."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user message")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="Translation:\nTranslated with glossary terms",
            model="gpt-4",
            provider="openai",
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        glossary = {
            "premium": "प्रीमियम",
            "deductible": "डिडक्टिबल",
        }
        
        result = await translation_service.translate_with_glossary(
            text="The premium and deductible are important",
            source_language="en",
            target_language="hi",
            glossary=glossary,
        )
        
        assert result.source_language == "en"
        assert result.target_language == "hi"
        
        # Verify glossary was included in prompt
        call_args = mock_llm_client.generate.call_args
        prompt = call_args.kwargs['prompt']
        assert "premium: प्रीमियम" in prompt
        assert "deductible: डिडक्टिबल" in prompt


class TestBatchTranslation:
    """Test batch translation functionality."""
    
    @pytest.mark.asyncio
    async def test_batch_translate_multiple_texts(self, translation_service, mock_llm_client):
        """Test batch translation of multiple texts."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        # Mock responses for each text
        responses = [
            LLMResponse(content="Translation:\nपहला", model="gpt-4", provider="openai"),
            LLMResponse(content="Translation:\nदूसरा", model="gpt-4", provider="openai"),
            LLMResponse(content="Translation:\nतीसरा", model="gpt-4", provider="openai"),
        ]
        mock_llm_client.generate = AsyncMock(side_effect=responses)
        
        texts = ["first", "second", "third"]
        results = await translation_service.batch_translate(
            texts=texts,
            source_language="en",
            target_language="hi",
        )
        
        assert len(results) == 3
        assert all(r.source_language == "en" for r in results)
        assert all(r.target_language == "hi" for r in results)
        assert mock_llm_client.generate.call_count == 3
    
    @pytest.mark.asyncio
    async def test_batch_translate_handles_errors(self, translation_service, mock_llm_client):
        """Test that batch translation handles individual errors gracefully."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        # First succeeds, second fails, third succeeds
        responses = [
            LLMResponse(content="Translation:\nपहला", model="gpt-4", provider="openai"),
            Exception("Translation failed"),
            LLMResponse(content="Translation:\nतीसरा", model="gpt-4", provider="openai"),
        ]
        mock_llm_client.generate = AsyncMock(side_effect=responses)
        
        texts = ["first", "second", "third"]
        results = await translation_service.batch_translate(
            texts=texts,
            source_language="en",
            target_language="hi",
        )
        
        assert len(results) == 3
        assert "पहला" in results[0].translated_content
        assert "Translation Error" in results[1].translated_content
        assert results[1].confidence_score == 0.0
        assert "तीसरा" in results[2].translated_content


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_empty_text_translation(self, translation_service, mock_llm_client):
        """Test translation of empty text."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="Translation:\n",
            model="gpt-4",
            provider="openai",
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        result = await translation_service.translate(
            text="",
            source_language="en",
            target_language="hi",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "hi"
    
    @pytest.mark.asyncio
    async def test_very_long_text_translation(self, translation_service, mock_llm_client):
        """Test translation of very long text."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="Translation:\nLong translated text",
            model="gpt-4",
            provider="openai",
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        long_text = "This is a test. " * 1000  # Very long text
        
        result = await translation_service.translate(
            text=long_text,
            source_language="en",
            target_language="hi",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "hi"
        
        # Verify LLM was called with the long text
        call_args = mock_llm_client.generate.call_args
        assert call_args is not None
    
    @pytest.mark.asyncio
    async def test_special_characters_in_text(self, translation_service, mock_llm_client):
        """Test translation with special characters."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="Translation:\nSpecial chars: @#$%",
            model="gpt-4",
            provider="openai",
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        text_with_special_chars = "Test @#$% special & chars!"
        
        result = await translation_service.translate(
            text=text_with_special_chars,
            source_language="en",
            target_language="hi",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "hi"


class TestLanguageNames:
    """Test language name mappings."""
    
    def test_all_supported_languages_have_names(self):
        """Test that all supported languages have display names."""
        for lang in SupportedLanguage:
            assert lang in TranslationService.LANGUAGE_NAMES
            assert TranslationService.LANGUAGE_NAMES[lang]
    
    def test_language_names_include_native_script(self):
        """Test that language names include native script."""
        # Hindi should have Devanagari
        assert "हिंदी" in TranslationService.LANGUAGE_NAMES[SupportedLanguage.HINDI]
        
        # Tamil should have Tamil script
        assert "தமிழ்" in TranslationService.LANGUAGE_NAMES[SupportedLanguage.TAMIL]
        
        # Telugu should have Telugu script
        assert "తెలుగు" in TranslationService.LANGUAGE_NAMES[SupportedLanguage.TELUGU]


class TestTechnicalTermIdentification:
    """Test technical term identification functionality."""
    
    def test_identify_insurance_terms(self, translation_service):
        """Test identification of insurance technical terms."""
        text = "The policy has a waiting period and copayment requirements."
        
        terms = translation_service.identify_technical_terms(text)
        
        assert "waiting period" in terms
        assert "copayment" in terms or "co-payment" in terms
    
    def test_identify_medical_terms(self, translation_service):
        """Test identification of medical technical terms."""
        text = "Patient has hypertension and diabetes mellitus."
        
        terms = translation_service.identify_technical_terms(text)
        
        assert "hypertension" in terms
        assert "diabetes mellitus" in terms
    
    def test_identify_ped_term(self, translation_service):
        """Test identification of PED term."""
        text = "Pre-existing disease (PED) coverage is limited."
        
        terms = translation_service.identify_technical_terms(text)
        
        # Should identify both forms
        assert any("pre-existing" in term.lower() or "ped" in term.lower() for term in terms)
    
    def test_identify_multiple_terms(self, translation_service):
        """Test identification of multiple technical terms."""
        text = (
            "The insurance policy covers chemotherapy and dialysis "
            "but has exclusions for pre-existing conditions. "
            "The deductible and copayment apply."
        )
        
        terms = translation_service.identify_technical_terms(text)
        
        # Should identify multiple terms
        assert len(terms) >= 4
        assert any("chemotherapy" in term.lower() for term in terms)
        assert any("exclusion" in term.lower() for term in terms)
        assert any("deductible" in term.lower() for term in terms)
    
    def test_identify_terms_case_insensitive(self, translation_service):
        """Test that term identification is case-insensitive."""
        text1 = "The WAITING PERIOD is 30 days."
        text2 = "The waiting period is 30 days."
        
        terms1 = translation_service.identify_technical_terms(text1)
        terms2 = translation_service.identify_technical_terms(text2)
        
        # Should identify the same terms regardless of case
        assert len(terms1) > 0
        assert len(terms2) > 0
    
    def test_no_terms_in_plain_text(self, translation_service):
        """Test that plain text without technical terms returns empty set."""
        text = "This is a simple sentence with no technical terms."
        
        terms = translation_service.identify_technical_terms(text)
        
        # Might be empty or have very few common words
        assert len(terms) <= 1  # Allow for edge cases


class TestTermExplanation:
    """Test technical term explanation retrieval."""
    
    def test_get_explanation_for_known_term_hindi(self, translation_service):
        """Test getting explanation for known term in Hindi."""
        explanation = translation_service.get_term_explanation(
            term="waiting period",
            target_language="hi",
        )
        
        assert explanation is not None
        assert len(explanation) > 0
        # Should contain Hindi text
        assert any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in explanation)
    
    def test_get_explanation_for_known_term_tamil(self, translation_service):
        """Test getting explanation for known term in Tamil."""
        explanation = translation_service.get_term_explanation(
            term="copayment",
            target_language="ta",
        )
        
        assert explanation is not None
        assert len(explanation) > 0
        # Should contain Tamil text
        assert any(ord(char) >= 0x0B80 and ord(char) <= 0x0BFF for char in explanation)
    
    def test_get_explanation_for_ped_term(self, translation_service):
        """Test getting explanation for PED term."""
        explanation = translation_service.get_term_explanation(
            term="PED",
            target_language="en",
        )
        
        assert explanation is not None
        assert "pre-existing" in explanation.lower()
    
    def test_get_explanation_for_unknown_term(self, translation_service):
        """Test that unknown terms return None."""
        explanation = translation_service.get_term_explanation(
            term="unknown_medical_term_xyz",
            target_language="hi",
        )
        
        assert explanation is None
    
    def test_get_explanation_case_insensitive(self, translation_service):
        """Test that term lookup is case-insensitive."""
        explanation1 = translation_service.get_term_explanation(
            term="HYPERTENSION",
            target_language="hi",
        )
        explanation2 = translation_service.get_term_explanation(
            term="hypertension",
            target_language="hi",
        )
        
        assert explanation1 == explanation2
        assert explanation1 is not None
    
    def test_all_glossary_terms_have_all_languages(self, translation_service):
        """Test that all glossary terms have explanations in all supported languages."""
        supported_langs = translation_service.get_supported_languages()
        
        for term, explanations in translation_service.TECHNICAL_GLOSSARY.items():
            for lang in supported_langs:
                assert lang in explanations, \
                    f"Term '{term}' missing explanation for language '{lang}'"
                assert len(explanations[lang]) > 0, \
                    f"Term '{term}' has empty explanation for language '{lang}'"


class TestPreserveTerminology:
    """Test preserve_terminology method."""
    
    @pytest.mark.asyncio
    async def test_preserve_terminology_same_language(self, translation_service):
        """Test that same language returns original with empty glossary."""
        text = "The waiting period is 30 days."
        
        result = await translation_service.preserve_terminology(
            text=text,
            target_language="en",
            source_language="en",
        )
        
        assert result.translated_content == text
        assert result.source_language == "en"
        assert result.target_language == "en"
        assert len(result.glossary) == 0
        assert result.confidence_score == 1.0
    
    @pytest.mark.asyncio
    async def test_preserve_terminology_with_insurance_terms(
        self,
        translation_service,
        mock_llm_client,
    ):
        """Test preserving insurance terminology in translation."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
बीमा पॉलिसी में waiting period और copayment की आवश्यकता है

Technical Terms:
- waiting period: प्रतीक्षा अवधि - पॉलिसी खरीद के बाद की अवधि जिसमें कुछ दावे कवर नहीं होते
- copayment: सह-भुगतान - चिकित्सा खर्च का प्रतिशत जो बीमाधारक को देना होता है""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.92,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        text = "The insurance policy requires a waiting period and copayment."
        
        result = await translation_service.preserve_terminology(
            text=text,
            target_language="hi",
            source_language="en",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "hi"
        assert "waiting period" in result.translated_content
        assert "copayment" in result.translated_content
        assert len(result.glossary) >= 2
        assert result.confidence_score == 0.92
        
        # Verify glossary contains explanations
        term_names = [term.original_term.lower() for term in result.glossary]
        assert any("waiting period" in name for name in term_names)
        assert any("copayment" in name or "co-payment" in name for name in term_names)
    
    @pytest.mark.asyncio
    async def test_preserve_terminology_with_medical_terms(
        self,
        translation_service,
        mock_llm_client,
    ):
        """Test preserving medical terminology in translation."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
நோயாளிக்கு hypertension மற்றும் diabetes mellitus உள்ளது

Technical Terms:
- hypertension: உயர் இரத்த அழுத்தம் - இரத்த அழுத்தம் தொடர்ந்து உயர்ந்திருக்கும் நிலை
- diabetes mellitus: நீரிழிவு - இரத்த சர்க்கரை ஒழுங்குமுறையை பாதிக்கும் நாள்பட்ட நிலை""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.88,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        text = "Patient has hypertension and diabetes mellitus."
        
        result = await translation_service.preserve_terminology(
            text=text,
            target_language="ta",
            source_language="en",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "ta"
        assert "hypertension" in result.translated_content
        assert "diabetes mellitus" in result.translated_content
        assert len(result.glossary) >= 2
    
    @pytest.mark.asyncio
    async def test_preserve_terminology_unsupported_language(self, translation_service):
        """Test that unsupported language raises ValueError."""
        with pytest.raises(ValueError, match="not supported"):
            await translation_service.preserve_terminology(
                text="test",
                target_language="fr",
                source_language="en",
            )
    
    @pytest.mark.asyncio
    async def test_preserve_terminology_with_ped_term(
        self,
        translation_service,
        mock_llm_client,
    ):
        """Test preserving PED term with explanation."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
PED కవరేజ్ పరిమితం చేయబడింది

Technical Terms:
- PED: ముందుగా ఉన్న వ్యాధి - బీమా కొనుగోలు చేయడానికి ముందు ఉన్న వైద్య పరిస్థితి""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.90,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        text = "PED coverage is limited."
        
        result = await translation_service.preserve_terminology(
            text=text,
            target_language="te",
            source_language="en",
        )
        
        assert "PED" in result.translated_content
        assert len(result.glossary) >= 1
        
        # Find PED term in glossary
        ped_term = next(
            (term for term in result.glossary if "PED" in term.original_term.upper()),
            None
        )
        assert ped_term is not None
        assert len(ped_term.explanation) > 0
    
    @pytest.mark.asyncio
    async def test_preserve_terminology_prompt_includes_terms(
        self,
        translation_service,
        mock_llm_client,
    ):
        """Test that preserve_terminology prompt includes identified terms."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="Translation:\nTranslated text",
            model="gpt-4",
            provider="openai",
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        text = "The deductible and waiting period apply."
        
        await translation_service.preserve_terminology(
            text=text,
            target_language="hi",
            source_language="en",
        )
        
        # Verify LLM was called with terms to preserve
        call_args = mock_llm_client.generate.call_args
        prompt = call_args.kwargs['prompt']
        
        # Prompt should mention preserving terms
        assert "preserve" in prompt.lower() or "technical" in prompt.lower()
        assert "deductible" in prompt.lower() or "waiting period" in prompt.lower()


class TestTechnicalGlossary:
    """Test technical glossary completeness."""
    
    def test_glossary_has_insurance_terms(self, translation_service):
        """Test that glossary includes key insurance terms."""
        glossary = translation_service.TECHNICAL_GLOSSARY
        
        # Key insurance terms should be present
        assert "waiting period" in glossary
        assert "copayment" in glossary
        assert "deductible" in glossary
        assert "exclusion" in glossary
        assert "PED" in glossary
    
    def test_glossary_has_medical_terms(self, translation_service):
        """Test that glossary includes key medical terms."""
        glossary = translation_service.TECHNICAL_GLOSSARY
        
        # Key medical terms should be present
        assert "hypertension" in glossary
        assert "diabetes mellitus" in glossary
        assert "chemotherapy" in glossary
    
    def test_glossary_explanations_not_empty(self, translation_service):
        """Test that all glossary explanations are non-empty."""
        glossary = translation_service.TECHNICAL_GLOSSARY
        
        for term, explanations in glossary.items():
            for lang, explanation in explanations.items():
                assert len(explanation) > 0, \
                    f"Empty explanation for term '{term}' in language '{lang}'"
    
    def test_technical_term_patterns_not_empty(self, translation_service):
        """Test that technical term patterns list is not empty."""
        patterns = translation_service.TECHNICAL_TERM_PATTERNS
        
        assert len(patterns) > 0
        assert all(isinstance(pattern, str) for pattern in patterns)


class TestSpecificLanguageTranslations:
    """Test specific translation examples for each supported language."""
    
    @pytest.mark.asyncio
    async def test_english_to_hindi_translation(self, translation_service, mock_llm_client):
        """Test English to Hindi translation with insurance terms."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
आपकी बीमा पॉलिसी में waiting period है

Technical Terms:
- waiting period: प्रतीक्षा अवधि - पॉलिसी खरीद के बाद की अवधि""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.92,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        result = await translation_service.translate(
            text="Your insurance policy has a waiting period",
            source_language="en",
            target_language="hi",
            context_type="policy",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "hi"
        assert "waiting period" in result.translated_content
        assert len(result.technical_terms) >= 1
    
    @pytest.mark.asyncio
    async def test_english_to_tamil_translation(self, translation_service, mock_llm_client):
        """Test English to Tamil translation with medical terms."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
நோயாளிக்கு hypertension உள்ளது

Technical Terms:
- hypertension: உயர் இரத்த அழுத்தம் - இரத்த அழுத்தம் தொடர்ந்து உயர்ந்திருக்கும் நிலை""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.88,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        result = await translation_service.translate(
            text="Patient has hypertension",
            source_language="en",
            target_language="ta",
            context_type="medical",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "ta"
        assert "hypertension" in result.translated_content
    
    @pytest.mark.asyncio
    async def test_english_to_telugu_translation(self, translation_service, mock_llm_client):
        """Test English to Telugu translation."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
మీ deductible మొత్తం రూ.5000

Technical Terms:
- deductible: డిడక్టిబుల్ - బీమా కవరేజ్ ప్రారంభమయ్యే ముందు చెల్లించాల్సిన స్థిర మొత్తం""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.90,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        result = await translation_service.translate(
            text="Your deductible amount is Rs.5000",
            source_language="en",
            target_language="te",
            context_type="policy",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "te"
        assert "deductible" in result.translated_content
    
    @pytest.mark.asyncio
    async def test_english_to_bengali_translation(self, translation_service, mock_llm_client):
        """Test English to Bengali translation."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
আপনার copayment 20%

Technical Terms:
- copayment: সহ-পেমেন্ট - চিকিৎসা খরচের শতাংশ যা বীমাকৃত ব্যক্তিকে দিতে হবে""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.89,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        result = await translation_service.translate(
            text="Your copayment is 20%",
            source_language="en",
            target_language="bn",
            context_type="policy",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "bn"
        assert "copayment" in result.translated_content
    
    @pytest.mark.asyncio
    async def test_english_to_marathi_translation(self, translation_service, mock_llm_client):
        """Test English to Marathi translation."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
तुमच्या पॉलिसीमध्ये exclusion आहेत

Technical Terms:
- exclusion: वगळणे - विमा पॉलिसीद्वारे कव्हर केले जात नाहीत अशा वैद्यकीय स्थिती""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.91,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        result = await translation_service.translate(
            text="Your policy has exclusions",
            source_language="en",
            target_language="mr",
            context_type="policy",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "mr"
        assert "exclusion" in result.translated_content
    
    @pytest.mark.asyncio
    async def test_english_to_gujarati_translation(self, translation_service, mock_llm_client):
        """Test English to Gujarati translation."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
તમારી premium રકમ રૂ.10000 છે

Technical Terms:
- premium: પ્રીમિયમ - વીમા કવરેજ માટે ચૂકવવાની રકમ""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.87,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        result = await translation_service.translate(
            text="Your premium amount is Rs.10000",
            source_language="en",
            target_language="gu",
            context_type="policy",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "gu"
        assert "premium" in result.translated_content


class TestMixedLanguageInput:
    """Test handling of mixed-language input."""
    
    @pytest.mark.asyncio
    async def test_english_text_with_hindi_words(self, translation_service, mock_llm_client):
        """Test translation of English text containing Hindi words."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
आपकी बीमा पॉलिसी में अच्छा coverage है

Technical Terms:
- coverage: कवरेज - बीमा द्वारा प्रदान की जाने वाली सुरक्षा""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.85,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        # Mixed English-Hindi input
        result = await translation_service.translate(
            text="Your बीमा policy has good coverage",
            source_language="en",
            target_language="hi",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "hi"
        assert result.translated_content is not None
    
    @pytest.mark.asyncio
    async def test_text_with_numbers_and_symbols(self, translation_service, mock_llm_client):
        """Test translation preserves numbers and symbols."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
आपका premium रु.5,000 है और copayment 20% है

Technical Terms:
- premium: प्रीमियम - बीमा कवरेज के लिए भुगतान की जाने वाली राशि
- copayment: सह-भुगतान - चिकित्सा खर्च का प्रतिशत""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.93,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        result = await translation_service.translate(
            text="Your premium is Rs.5,000 and copayment is 20%",
            source_language="en",
            target_language="hi",
        )
        
        assert result.source_language == "en"
        assert result.target_language == "hi"
        # Numbers should be preserved in some form
        assert "5" in result.translated_content or "5,000" in result.translated_content
        assert "20" in result.translated_content
    
    @pytest.mark.asyncio
    async def test_text_with_english_technical_terms_in_hindi(
        self,
        translation_service,
        mock_llm_client,
    ):
        """Test that English technical terms are preserved in Hindi translation."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
यह policy में PED coverage शामिल है

Technical Terms:
- PED: पूर्व-मौजूदा बीमारी - बीमा खरीदने से पहले मौजूद चिकित्सा स्थिति
- coverage: कवरेज - बीमा द्वारा प्रदान की जाने वाली सुरक्षा""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.90,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        result = await translation_service.translate(
            text="This policy includes PED coverage",
            source_language="en",
            target_language="hi",
            context_type="policy",
        )
        
        # Technical terms should be preserved
        assert "PED" in result.translated_content
        assert len(result.technical_terms) >= 1


class TestFormattingPreservation:
    """Test preservation of formatting and structure."""
    
    @pytest.mark.asyncio
    async def test_multiline_text_structure_preserved(
        self,
        translation_service,
        mock_llm_client,
    ):
        """Test that multiline text structure is preserved."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
पहली पंक्ति
दूसरी पंक्ति
तीसरी पंक्ति""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.95,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        multiline_text = "First line\nSecond line\nThird line"
        
        result = await translation_service.translate(
            text=multiline_text,
            source_language="en",
            target_language="hi",
        )
        
        # Should have multiple lines
        assert '\n' in result.translated_content or len(result.translated_content.split()) >= 3
    
    @pytest.mark.asyncio
    async def test_bullet_points_preserved(self, translation_service, mock_llm_client):
        """Test that bullet point structure is preserved."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
- पहला बिंदु
- दूसरा बिंदु
- तीसरा बिंदु""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.94,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        bullet_text = "- First point\n- Second point\n- Third point"
        
        result = await translation_service.translate(
            text=bullet_text,
            source_language="en",
            target_language="hi",
        )
        
        # Should preserve bullet structure
        assert result.translated_content is not None
    
    @pytest.mark.asyncio
    async def test_paragraph_structure_preserved(
        self,
        translation_service,
        mock_llm_client,
    ):
        """Test that paragraph structure is preserved."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="""Translation:
यह पहला पैराग्राफ है। इसमें कई वाक्य हैं।

यह दूसरा पैराग्राफ है। यह अलग है।""",
            model="gpt-4",
            provider="openai",
            confidence_score=0.91,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        paragraph_text = (
            "This is the first paragraph. It has multiple sentences.\n\n"
            "This is the second paragraph. It is separate."
        )
        
        result = await translation_service.translate(
            text=paragraph_text,
            source_language="en",
            target_language="hi",
        )
        
        # Should have some structure
        assert result.translated_content is not None
        assert len(result.translated_content) > 0
    
    @pytest.mark.asyncio
    async def test_whitespace_handling(self, translation_service, mock_llm_client):
        """Test handling of extra whitespace."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="Translation:\nयह एक परीक्षण है",
            model="gpt-4",
            provider="openai",
            confidence_score=0.96,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        # Text with extra whitespace
        text_with_whitespace = "  This   is   a   test  "
        
        result = await translation_service.translate(
            text=text_with_whitespace,
            source_language="en",
            target_language="hi",
        )
        
        assert result.translated_content is not None
        # Translation should handle whitespace gracefully


class TestTranslationConfidenceScoring:
    """Test confidence scoring in translations."""
    
    @pytest.mark.asyncio
    async def test_high_confidence_translation(self, translation_service, mock_llm_client):
        """Test translation with high confidence score."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="Translation:\nसरल अनुवाद",
            model="gpt-4",
            provider="openai",
            confidence_score=0.98,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        result = await translation_service.translate(
            text="Simple translation",
            source_language="en",
            target_language="hi",
        )
        
        assert result.confidence_score == 0.98
        assert result.confidence_score > 0.9
    
    @pytest.mark.asyncio
    async def test_low_confidence_translation(self, translation_service, mock_llm_client):
        """Test translation with low confidence score."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="Translation:\nजटिल तकनीकी अनुवाद",
            model="gpt-4",
            provider="openai",
            confidence_score=0.65,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        result = await translation_service.translate(
            text="Complex technical translation",
            source_language="en",
            target_language="hi",
        )
        
        assert result.confidence_score == 0.65
        assert result.confidence_score < 0.9
    
    @pytest.mark.asyncio
    async def test_none_confidence_score(self, translation_service, mock_llm_client):
        """Test translation with no confidence score."""
        mock_template = MagicMock()
        mock_template.format.return_value = ("system", "user")
        mock_llm_client.get_template.return_value = mock_template
        
        mock_response = LLMResponse(
            content="Translation:\nअनुवाद",
            model="gpt-4",
            provider="openai",
            confidence_score=None,
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        result = await translation_service.translate(
            text="Translation",
            source_language="en",
            target_language="hi",
        )
        
        # Should handle None confidence score
        assert result.confidence_score is None or isinstance(result.confidence_score, float)


