"""Standalone test script for translation service."""

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock

# Add parent directory to path
sys.path.insert(0, '.')

from healthcare_insurance_platform.services.translation import (
    SupportedLanguage,
    TranslationService,
)
from healthcare_insurance_platform.services.llm_client import LLMResponse


def test_supported_languages():
    """Test that all required languages are supported."""
    print("Testing supported languages...")
    
    mock_llm_client = MagicMock()
    mock_llm_client.register_template = MagicMock()
    service = TranslationService(llm_client=mock_llm_client)
    
    required_languages = ["hi", "ta", "te", "bn", "mr", "gu", "en"]
    
    for lang in required_languages:
        assert service.is_language_supported(lang), f"Language {lang} should be supported"
    
    print("✓ All required languages are supported")


async def test_same_language_translation():
    """Test that same language translation returns original."""
    print("Testing same language translation...")
    
    mock_llm_client = MagicMock()
    mock_llm_client.register_template = MagicMock()
    service = TranslationService(llm_client=mock_llm_client)
    
    text = "This is a test"
    result = await service.translate(
        text=text,
        source_language="en",
        target_language="en",
    )
    
    assert result.translated_content == text
    assert result.source_language == "en"
    assert result.target_language == "en"
    assert result.confidence_score == 1.0
    
    print("✓ Same language translation works correctly")


async def test_translation_with_llm():
    """Test translation using LLM."""
    print("Testing translation with LLM...")
    
    mock_llm_client = MagicMock()
    mock_llm_client.register_template = MagicMock()
    
    # Mock template
    mock_template = MagicMock()
    mock_template.format.return_value = ("system", "user")
    mock_llm_client.get_template.return_value = mock_template
    
    # Mock LLM response
    mock_response = LLMResponse(
        content="Translation:\nयह एक परीक्षण है\n\nTechnical Terms:\n- test: परीक्षण",
        model="gpt-4",
        provider="openai",
        confidence_score=0.95,
    )
    mock_llm_client.generate = AsyncMock(return_value=mock_response)
    
    service = TranslationService(llm_client=mock_llm_client)
    
    result = await service.translate(
        text="This is a test",
        source_language="en",
        target_language="hi",
    )
    
    assert result.source_language == "en"
    assert result.target_language == "hi"
    assert "परीक्षण" in result.translated_content
    assert result.confidence_score == 0.95
    assert len(result.technical_terms) > 0
    
    print("✓ Translation with LLM works correctly")


async def test_unsupported_language():
    """Test that unsupported language raises error."""
    print("Testing unsupported language handling...")
    
    mock_llm_client = MagicMock()
    mock_llm_client.register_template = MagicMock()
    service = TranslationService(llm_client=mock_llm_client)
    
    try:
        await service.translate(
            text="test",
            source_language="fr",  # French not supported
            target_language="en",
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not supported" in str(e)
    
    print("✓ Unsupported language raises appropriate error")


async def test_context_types():
    """Test different context types."""
    print("Testing context types...")
    
    mock_llm_client = MagicMock()
    mock_llm_client.register_template = MagicMock()
    
    mock_template = MagicMock()
    mock_template.format.return_value = ("system", "user")
    mock_llm_client.get_template.return_value = mock_template
    
    mock_response = LLMResponse(
        content="Translation:\nTranslated text",
        model="gpt-4",
        provider="openai",
    )
    mock_llm_client.generate = AsyncMock(return_value=mock_response)
    
    service = TranslationService(llm_client=mock_llm_client)
    
    # Test each context type
    for context in ["general", "policy", "medical"]:
        result = await service.translate(
            text="test",
            source_language="en",
            target_language="hi",
            context_type=context,
        )
        assert result is not None
    
    # Test invalid context
    try:
        await service.translate(
            text="test",
            source_language="en",
            target_language="hi",
            context_type="invalid",
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid context_type" in str(e)
    
    print("✓ Context types work correctly")


async def test_batch_translation():
    """Test batch translation."""
    print("Testing batch translation...")
    
    mock_llm_client = MagicMock()
    mock_llm_client.register_template = MagicMock()
    
    mock_template = MagicMock()
    mock_template.format.return_value = ("system", "user")
    mock_llm_client.get_template.return_value = mock_template
    
    responses = [
        LLMResponse(content="Translation:\nपहला", model="gpt-4", provider="openai"),
        LLMResponse(content="Translation:\nदूसरा", model="gpt-4", provider="openai"),
        LLMResponse(content="Translation:\nतीसरा", model="gpt-4", provider="openai"),
    ]
    mock_llm_client.generate = AsyncMock(side_effect=responses)
    
    service = TranslationService(llm_client=mock_llm_client)
    
    texts = ["first", "second", "third"]
    results = await service.batch_translate(
        texts=texts,
        source_language="en",
        target_language="hi",
    )
    
    assert len(results) == 3
    assert all(r.source_language == "en" for r in results)
    assert all(r.target_language == "hi" for r in results)
    
    print("✓ Batch translation works correctly")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Running Translation Service Tests")
    print("=" * 60)
    print()
    
    try:
        # Synchronous tests
        test_supported_languages()
        
        # Async tests
        await test_same_language_translation()
        await test_translation_with_llm()
        await test_unsupported_language()
        await test_context_types()
        await test_batch_translation()
        
        print()
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
