"""Example usage of the Translation Service.

This example demonstrates how to use the Translation Service
for multilingual content translation in the healthcare insurance platform.
"""

import asyncio
from healthcare_insurance_platform.services.translation import (
    TranslationService,
    SupportedLanguage,
)


async def basic_translation_example():
    """Example 1: Basic translation."""
    print("=" * 60)
    print("Example 1: Basic Translation")
    print("=" * 60)
    
    service = TranslationService()
    
    # Translate a simple message
    text = "Your insurance claim has been approved"
    
    result = await service.translate(
        text=text,
        source_language="en",
        target_language="hi",
    )
    
    print(f"Original (English): {text}")
    print(f"Translated (Hindi): {result.translated_content}")
    print(f"Confidence: {result.confidence_score}")
    print()


async def policy_translation_example():
    """Example 2: Policy document translation with term preservation."""
    print("=" * 60)
    print("Example 2: Policy Document Translation")
    print("=" * 60)
    
    service = TranslationService()
    
    policy_text = """
    This health insurance policy provides coverage for hospitalization expenses
    up to the sum insured amount. Pre-existing diseases are covered after
    a waiting period of 48 months. The policyholder must pay a deductible
    of Rs. 10,000 for each claim.
    """
    
    result = await service.translate(
        text=policy_text,
        source_language="en",
        target_language="hi",
        context_type="policy",  # Use policy context for legal terms
    )
    
    print("Original Policy Text:")
    print(policy_text)
    print("\nTranslated Policy Text:")
    print(result.translated_content)
    
    if result.technical_terms:
        print("\nTechnical Terms Preserved:")
        for term in result.technical_terms:
            print(f"  • {term.original_term}")
            print(f"    Explanation: {term.explanation}")
    print()


async def medical_translation_example():
    """Example 3: Medical content translation."""
    print("=" * 60)
    print("Example 3: Medical Content Translation")
    print("=" * 60)
    
    service = TranslationService()
    
    medical_text = """
    Patient presents with hypertension and type 2 diabetes mellitus.
    Current medications include metformin 500mg twice daily and
    lisinopril 10mg once daily. Blood pressure is 140/90 mmHg.
    """
    
    result = await service.translate(
        text=medical_text,
        source_language="en",
        target_language="ta",  # Tamil
        context_type="medical",
    )
    
    print("Original Medical Text:")
    print(medical_text)
    print("\nTranslated Medical Text (Tamil):")
    print(result.translated_content)
    print()


async def multilingual_example():
    """Example 4: Translate to multiple languages."""
    print("=" * 60)
    print("Example 4: Multilingual Translation")
    print("=" * 60)
    
    service = TranslationService()
    
    message = "Your claim is under review. We will notify you within 7 days."
    
    # Translate to all supported languages
    target_languages = ["hi", "ta", "te", "bn", "mr", "gu"]
    language_names = {
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati",
    }
    
    print(f"Original (English): {message}\n")
    
    for lang_code in target_languages:
        result = await service.translate(
            text=message,
            source_language="en",
            target_language=lang_code,
        )
        print(f"{language_names[lang_code]}: {result.translated_content}")
    print()


async def glossary_translation_example():
    """Example 5: Translation with custom glossary."""
    print("=" * 60)
    print("Example 5: Translation with Custom Glossary")
    print("=" * 60)
    
    service = TranslationService()
    
    # Define custom translations for specific terms
    glossary = {
        "premium": "प्रीमियम",
        "deductible": "डिडक्टिबल",
        "copayment": "सह-भुगतान",
        "network hospital": "नेटवर्क अस्पताल",
    }
    
    text = """
    Your annual premium is Rs. 15,000. The policy has a deductible of Rs. 5,000
    and requires a copayment of 20% for treatment at non-network hospitals.
    """
    
    result = await service.translate_with_glossary(
        text=text,
        source_language="en",
        target_language="hi",
        glossary=glossary,
        context_type="policy",
    )
    
    print("Original Text:")
    print(text)
    print("\nTranslated with Custom Glossary:")
    print(result.translated_content)
    print("\nGlossary Used:")
    for term, translation in glossary.items():
        print(f"  • {term} → {translation}")
    print()


async def batch_translation_example():
    """Example 6: Batch translation."""
    print("=" * 60)
    print("Example 6: Batch Translation")
    print("=" * 60)
    
    service = TranslationService()
    
    # Multiple messages to translate
    messages = [
        "Your claim has been received",
        "Please submit additional documents",
        "Claim approved successfully",
        "Payment will be processed in 3-5 business days",
        "Thank you for choosing our insurance",
    ]
    
    results = await service.batch_translate(
        texts=messages,
        source_language="en",
        target_language="hi",
    )
    
    print("Batch Translation Results:\n")
    for i, (original, result) in enumerate(zip(messages, results), 1):
        print(f"{i}. Original: {original}")
        print(f"   Translated: {result.translated_content}")
        print()


async def language_validation_example():
    """Example 7: Language validation."""
    print("=" * 60)
    print("Example 7: Language Validation")
    print("=" * 60)
    
    service = TranslationService()
    
    # Check supported languages
    print("Supported Languages:")
    for lang_code in service.get_supported_languages():
        lang_name = TranslationService.LANGUAGE_NAMES[SupportedLanguage(lang_code)]
        print(f"  • {lang_code}: {lang_name}")
    
    print("\nLanguage Validation:")
    
    # Valid language
    if service.is_language_supported("hi"):
        print("  ✓ Hindi (hi) is supported")
    
    # Invalid language
    if not service.is_language_supported("fr"):
        print("  ✗ French (fr) is not supported")
    
    # Try translating with unsupported language
    print("\nAttempting translation with unsupported language:")
    try:
        await service.translate(
            text="test",
            source_language="fr",  # French not supported
            target_language="en",
        )
    except ValueError as e:
        print(f"  Error caught: {e}")
    print()


async def context_type_example():
    """Example 8: Different context types."""
    print("=" * 60)
    print("Example 8: Context Types")
    print("=" * 60)
    
    service = TranslationService()
    
    text = "The patient requires immediate hospitalization for treatment"
    
    print(f"Original: {text}\n")
    
    # General context
    result_general = await service.translate(
        text=text,
        source_language="en",
        target_language="hi",
        context_type="general",
    )
    print(f"General Context: {result_general.translated_content}")
    
    # Medical context
    result_medical = await service.translate(
        text=text,
        source_language="en",
        target_language="hi",
        context_type="medical",
    )
    print(f"Medical Context: {result_medical.translated_content}")
    
    # Policy context
    result_policy = await service.translate(
        text=text,
        source_language="en",
        target_language="hi",
        context_type="policy",
    )
    print(f"Policy Context: {result_policy.translated_content}")
    print()


async def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Translation Service Examples" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    # Run examples
    await basic_translation_example()
    await policy_translation_example()
    await medical_translation_example()
    await multilingual_example()
    await glossary_translation_example()
    await batch_translation_example()
    await language_validation_example()
    await context_type_example()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Note: These examples use mock LLM responses
    # In production, configure with actual LLM credentials
    asyncio.run(main())
