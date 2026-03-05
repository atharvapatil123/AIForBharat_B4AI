"""Simple test runner for translation unit tests without conftest dependencies."""

import sys
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Add parent directory to path
sys.path.insert(0, '.')

from healthcare_insurance_platform.services.translation import (
    TranslationService,
    SupportedLanguage,
)
from healthcare_insurance_platform.services.llm_client import LLMResponse


def create_mock_translation_service():
    """Create translation service with mocked LLM client."""
    mock_llm_client = MagicMock()
    mock_llm_client.register_template = MagicMock()
    
    # Mock template
    mock_template = MagicMock()
    mock_template.format.return_value = ("system message", "user message")
    mock_llm_client.get_template.return_value = mock_template
    
    service = TranslationService(llm_client=mock_llm_client)
    return service, mock_llm_client


async def test_english_to_hindi():
    """Test English to Hindi translation."""
    service, mock_llm_client = create_mock_translation_service()
    
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
    
    result = await service.translate(
        text="Your insurance policy has a waiting period",
        source_language="en",
        target_language="hi",
        context_type="policy",
    )
    
    assert result.source_language == "en"
    assert result.target_language == "hi"
    assert "waiting period" in result.translated_content
    assert len(result.technical_terms) >= 1
    print("✓ English to Hindi translation test passed")


async def test_mixed_language_input():
    """Test mixed language input handling."""
    service, mock_llm_client = create_mock_translation_service()
    
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
    
    result = await service.translate(
        text="Your premium is Rs.5,000 and copayment is 20%",
        source_language="en",
        target_language="hi",
    )
    
    assert result.source_language == "en"
    assert result.target_language == "hi"
    assert "5" in result.translated_content or "5,000" in result.translated_content
    assert "20" in result.translated_content
    print("✓ Mixed language input test passed")


async def test_formatting_preservation():
    """Test multiline text structure preservation."""
    service, mock_llm_client = create_mock_translation_service()
    
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
    
    result = await service.translate(
        text=multiline_text,
        source_language="en",
        target_language="hi",
    )
    
    assert '\n' in result.translated_content or len(result.translated_content.split()) >= 3
    print("✓ Formatting preservation test passed")


def test_all_languages_supported():
    """Test that all required languages are supported."""
    service, _ = create_mock_translation_service()
    
    required_languages = ["hi", "ta", "te", "bn", "mr", "gu", "en"]
    
    for lang in required_languages:
        assert service.is_language_supported(lang), \
            f"Language {lang} should be supported"
    
    print("✓ All required languages supported test passed")


def test_technical_term_identification():
    """Test technical term identification."""
    service, _ = create_mock_translation_service()
    
    text = "The policy has a waiting period and copayment requirements."
    terms = service.identify_technical_terms(text)
    
    assert "waiting period" in terms
    assert "copayment" in terms or "co-payment" in terms
    print("✓ Technical term identification test passed")


def test_term_explanation_retrieval():
    """Test term explanation retrieval."""
    service, _ = create_mock_translation_service()
    
    explanation = service.get_term_explanation(
        term="waiting period",
        target_language="hi",
    )
    
    assert explanation is not None
    assert len(explanation) > 0
    # Should contain Hindi text
    assert any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in explanation)
    print("✓ Term explanation retrieval test passed")


async def main():
    """Run all tests."""
    print("Running Translation Service Unit Tests\n")
    print("=" * 50)
    
    # Synchronous tests
    test_all_languages_supported()
    test_technical_term_identification()
    test_term_explanation_retrieval()
    
    # Async tests
    await test_english_to_hindi()
    await test_mixed_language_input()
    await test_formatting_preservation()
    
    print("=" * 50)
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
