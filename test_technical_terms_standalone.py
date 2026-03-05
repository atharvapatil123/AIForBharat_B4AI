"""Standalone test for technical term handling functionality."""

import sys
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Add project to path
sys.path.insert(0, '.')

from healthcare_insurance_platform.services.translation import (
    TranslationService,
    TranslatedTextWithGlossary,
)
from healthcare_insurance_platform.services.llm_client import LLMResponse


def test_identify_technical_terms():
    """Test technical term identification."""
    print("Testing technical term identification...")
    
    # Create service with mock LLM client
    mock_llm_client = MagicMock()
    mock_llm_client.register_template = MagicMock()
    service = TranslationService(llm_client=mock_llm_client)
    
    # Test 1: Insurance terms
    text1 = "The policy has a waiting period and copayment requirements."
    terms1 = service.identify_technical_terms(text1)
    print(f"  Insurance text: {text1}")
    print(f"  Identified terms: {terms1}")
    assert len(terms1) > 0, "Should identify insurance terms"
    assert any("waiting period" in term.lower() for term in terms1)
    print("  ✓ Insurance terms identified correctly")
    
    # Test 2: Medical terms
    text2 = "Patient has hypertension and diabetes mellitus."
    terms2 = service.identify_technical_terms(text2)
    print(f"\n  Medical text: {text2}")
    print(f"  Identified terms: {terms2}")
    assert len(terms2) > 0, "Should identify medical terms"
    assert "hypertension" in terms2
    assert "diabetes mellitus" in terms2
    print("  ✓ Medical terms identified correctly")
    
    # Test 3: PED term
    text3 = "Pre-existing disease (PED) coverage is limited."
    terms3 = service.identify_technical_terms(text3)
    print(f"\n  PED text: {text3}")
    print(f"  Identified terms: {terms3}")
    assert len(terms3) > 0, "Should identify PED term"
    print("  ✓ PED term identified correctly")
    
    # Test 4: Multiple terms
    text4 = (
        "The insurance policy covers chemotherapy and dialysis "
        "but has exclusions for pre-existing conditions. "
        "The deductible and copayment apply."
    )
    terms4 = service.identify_technical_terms(text4)
    print(f"\n  Complex text with multiple terms")
    print(f"  Identified terms: {terms4}")
    assert len(terms4) >= 4, "Should identify multiple terms"
    print("  ✓ Multiple terms identified correctly")
    
    print("\n✓ All technical term identification tests passed!\n")


def test_get_term_explanation():
    """Test term explanation retrieval."""
    print("Testing term explanation retrieval...")
    
    mock_llm_client = MagicMock()
    mock_llm_client.register_template = MagicMock()
    service = TranslationService(llm_client=mock_llm_client)
    
    # Test 1: Known term in Hindi
    explanation_hi = service.get_term_explanation("waiting period", "hi")
    print(f"  'waiting period' in Hindi: {explanation_hi}")
    assert explanation_hi is not None, "Should have Hindi explanation"
    assert len(explanation_hi) > 0
    print("  ✓ Hindi explanation retrieved")
    
    # Test 2: Known term in Tamil
    explanation_ta = service.get_term_explanation("copayment", "ta")
    print(f"  'copayment' in Tamil: {explanation_ta}")
    assert explanation_ta is not None, "Should have Tamil explanation"
    assert len(explanation_ta) > 0
    print("  ✓ Tamil explanation retrieved")
    
    # Test 3: PED term
    explanation_ped = service.get_term_explanation("PED", "en")
    print(f"  'PED' in English: {explanation_ped}")
    assert explanation_ped is not None, "Should have PED explanation"
    assert "pre-existing" in explanation_ped.lower()
    print("  ✓ PED explanation retrieved")
    
    # Test 4: Unknown term
    explanation_unknown = service.get_term_explanation("unknown_term_xyz", "hi")
    print(f"  'unknown_term_xyz': {explanation_unknown}")
    assert explanation_unknown is None, "Unknown term should return None"
    print("  ✓ Unknown term handled correctly")
    
    # Test 5: Case insensitive
    explanation_upper = service.get_term_explanation("HYPERTENSION", "hi")
    explanation_lower = service.get_term_explanation("hypertension", "hi")
    print(f"  Case insensitive check: {explanation_upper == explanation_lower}")
    assert explanation_upper == explanation_lower
    print("  ✓ Case insensitive lookup works")
    
    print("\n✓ All term explanation tests passed!\n")


async def test_preserve_terminology():
    """Test preserve_terminology method."""
    print("Testing preserve_terminology method...")
    
    # Create service with mock LLM client
    mock_llm_client = MagicMock()
    mock_llm_client.register_template = MagicMock()
    mock_llm_client.get_template = MagicMock()
    
    service = TranslationService(llm_client=mock_llm_client)
    
    # Test 1: Same language
    text1 = "The waiting period is 30 days."
    result1 = await service.preserve_terminology(
        text=text1,
        target_language="en",
        source_language="en",
    )
    print(f"  Same language test:")
    print(f"    Input: {text1}")
    print(f"    Output: {result1.translated_content}")
    assert result1.translated_content == text1
    assert len(result1.glossary) == 0
    assert result1.confidence_score == 1.0
    print("  ✓ Same language returns original")
    
    # Test 2: With insurance terms
    mock_response = LLMResponse(
        content="""Translation:
बीमा पॉलिसी में waiting period और copayment की आवश्यकता है

Technical Terms:
- waiting period: प्रतीक्षा अवधि - पॉलिसी खरीद के बाद की अवधि
- copayment: सह-भुगतान - चिकित्सा खर्च का प्रतिशत""",
        model="gpt-4",
        provider="openai",
        confidence_score=0.92,
    )
    mock_llm_client.generate = AsyncMock(return_value=mock_response)
    
    text2 = "The insurance policy requires a waiting period and copayment."
    result2 = await service.preserve_terminology(
        text=text2,
        target_language="hi",
        source_language="en",
    )
    print(f"\n  Insurance terms test:")
    print(f"    Input: {text2}")
    print(f"    Output: {result2.translated_content}")
    print(f"    Glossary size: {len(result2.glossary)}")
    assert "waiting period" in result2.translated_content
    assert "copayment" in result2.translated_content
    assert len(result2.glossary) >= 2
    print("  ✓ Insurance terms preserved with glossary")
    
    # Test 3: Unsupported language
    try:
        await service.preserve_terminology(
            text="test",
            target_language="fr",
            source_language="en",
        )
        assert False, "Should raise ValueError for unsupported language"
    except ValueError as e:
        print(f"\n  Unsupported language test:")
        print(f"    Error: {str(e)}")
        assert "not supported" in str(e)
        print("  ✓ Unsupported language raises ValueError")
    
    print("\n✓ All preserve_terminology tests passed!\n")


def test_glossary_completeness():
    """Test technical glossary completeness."""
    print("Testing glossary completeness...")
    
    mock_llm_client = MagicMock()
    mock_llm_client.register_template = MagicMock()
    service = TranslationService(llm_client=mock_llm_client)
    
    glossary = service.TECHNICAL_GLOSSARY
    supported_langs = service.get_supported_languages()
    
    print(f"  Glossary has {len(glossary)} terms")
    print(f"  Supported languages: {supported_langs}")
    
    # Check key terms exist
    key_terms = [
        "waiting period", "copayment", "deductible", "exclusion", "PED",
        "hypertension", "diabetes mellitus", "chemotherapy"
    ]
    
    for term in key_terms:
        assert term in glossary, f"Key term '{term}' missing from glossary"
    print(f"  ✓ All {len(key_terms)} key terms present")
    
    # Check all terms have all languages
    missing_explanations = []
    for term, explanations in glossary.items():
        for lang in supported_langs:
            if lang not in explanations:
                missing_explanations.append(f"{term} - {lang}")
            elif len(explanations[lang]) == 0:
                missing_explanations.append(f"{term} - {lang} (empty)")
    
    if missing_explanations:
        print(f"  ✗ Missing explanations:")
        for missing in missing_explanations[:5]:  # Show first 5
            print(f"    - {missing}")
        assert False, f"Found {len(missing_explanations)} missing explanations"
    
    print(f"  ✓ All terms have explanations in all {len(supported_langs)} languages")
    
    # Check patterns exist
    patterns = service.TECHNICAL_TERM_PATTERNS
    print(f"  ✓ {len(patterns)} term patterns defined")
    
    print("\n✓ Glossary completeness tests passed!\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("TECHNICAL TERM HANDLING TESTS")
    print("=" * 60)
    print()
    
    try:
        # Synchronous tests
        test_identify_technical_terms()
        test_get_term_explanation()
        test_glossary_completeness()
        
        # Async tests
        asyncio.run(test_preserve_terminology())
        
        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
