"""Example demonstrating technical term handling in translation service.

This example shows how the translation service:
1. Identifies technical terms in text
2. Preserves them during translation
3. Provides explanations in the target language
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from healthcare_insurance_platform.services.translation import (
    TranslationService,
    SupportedLanguage,
)
from healthcare_insurance_platform.services.llm_client import LLMResponse


async def demonstrate_technical_term_handling():
    """Demonstrate technical term handling functionality."""
    
    print("=" * 70)
    print("TECHNICAL TERM HANDLING DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Create translation service with mock LLM client
    mock_llm_client = MagicMock()
    mock_llm_client.register_template = MagicMock()
    mock_llm_client.get_template = MagicMock()
    
    service = TranslationService(llm_client=mock_llm_client)
    
    # Example 1: Identify technical terms in insurance text
    print("EXAMPLE 1: Identifying Technical Terms")
    print("-" * 70)
    
    insurance_text = """
    The insurance policy has a waiting period of 30 days for general 
    hospitalization and 2 years for pre-existing diseases (PED). 
    The copayment is 20% and the deductible is ₹25,000. 
    Exclusions include cosmetic surgery and experimental treatments.
    """
    
    print(f"Text:\n{insurance_text}")
    print()
    
    identified_terms = service.identify_technical_terms(insurance_text)
    print(f"Identified Technical Terms ({len(identified_terms)}):")
    for term in sorted(identified_terms):
        print(f"  • {term}")
    print()
    
    # Example 2: Get explanations for terms
    print("\nEXAMPLE 2: Getting Term Explanations")
    print("-" * 70)
    
    terms_to_explain = ["waiting period", "copayment", "PED", "exclusion"]
    
    for term in terms_to_explain:
        print(f"\nTerm: '{term}'")
        
        # Get explanation in English
        exp_en = service.get_term_explanation(term, "en")
        print(f"  English: {exp_en}")
        
        # Get explanation in Hindi
        exp_hi = service.get_term_explanation(term, "hi")
        print(f"  Hindi: {exp_hi}")
        
        # Get explanation in Tamil
        exp_ta = service.get_term_explanation(term, "ta")
        print(f"  Tamil: {exp_ta}")
    
    # Example 3: Preserve terminology during translation
    print("\n\nEXAMPLE 3: Preserving Terminology in Translation")
    print("-" * 70)
    
    # Mock LLM response for translation
    mock_response = LLMResponse(
        content="""Translation:
बीमा पॉलिसी में सामान्य अस्पताल में भर्ती के लिए 30 दिनों की waiting period 
और pre-existing diseases (PED) के लिए 2 साल की अवधि है। 
copayment 20% है और deductible ₹25,000 है।

Technical Terms:
- waiting period: प्रतीक्षा अवधि - पॉलिसी खरीद के बाद की अवधि जिसमें कुछ दावे कवर नहीं होते
- pre-existing diseases: पूर्व-मौजूदा बीमारियां - बीमा खरीदने से पहले मौजूद चिकित्सा स्थितियां
- PED: पूर्व-मौजूदा बीमारी - बीमा खरीदने से पहले मौजूद चिकित्सा स्थिति
- copayment: सह-भुगतान - चिकित्सा खर्च का प्रतिशत जो बीमाधारक को अपनी जेब से देना होता है
- deductible: कटौती योग्य राशि - निश्चित राशि जो बीमाधारक को बीमा कवरेज शुरू होने से पहले देनी होती है""",
        model="gpt-4",
        provider="openai",
        confidence_score=0.93,
    )
    mock_llm_client.generate = AsyncMock(return_value=mock_response)
    
    policy_text = """
    The insurance policy has a waiting period of 30 days for general 
    hospitalization and 2 years for pre-existing diseases (PED). 
    The copayment is 20% and the deductible is ₹25,000.
    """
    
    print(f"Original Text (English):\n{policy_text}")
    print()
    
    result = await service.preserve_terminology(
        text=policy_text,
        target_language="hi",
        source_language="en",
    )
    
    print(f"Translated Text (Hindi with preserved terms):")
    print(result.translated_content)
    print()
    
    print(f"Glossary ({len(result.glossary)} terms):")
    for term in result.glossary:
        print(f"\n  Term: {term.original_term}")
        if term.translated_term:
            print(f"  Translation: {term.translated_term}")
        print(f"  Explanation: {term.explanation}")
    
    print(f"\nConfidence Score: {result.confidence_score:.2f}")
    
    # Example 4: Medical terminology
    print("\n\nEXAMPLE 4: Medical Terminology")
    print("-" * 70)
    
    medical_text = """
    Patient has hypertension and diabetes mellitus. 
    Treatment includes chemotherapy for cardiovascular disease.
    """
    
    print(f"Medical Text:\n{medical_text}")
    print()
    
    medical_terms = service.identify_technical_terms(medical_text)
    print(f"Identified Medical Terms ({len(medical_terms)}):")
    for term in sorted(medical_terms):
        print(f"  • {term}")
        exp = service.get_term_explanation(term, "en")
        if exp:
            print(f"    → {exp}")
    
    # Example 5: Glossary coverage
    print("\n\nEXAMPLE 5: Glossary Coverage")
    print("-" * 70)
    
    glossary = service.TECHNICAL_GLOSSARY
    supported_langs = service.get_supported_languages()
    
    print(f"Total Terms in Glossary: {len(glossary)}")
    print(f"Supported Languages: {len(supported_langs)}")
    print(f"Languages: {', '.join(supported_langs)}")
    print()
    
    print("Sample Terms:")
    sample_terms = list(glossary.keys())[:10]
    for term in sample_terms:
        print(f"  • {term}")
    
    print(f"\nTotal Pattern Definitions: {len(service.TECHNICAL_TERM_PATTERNS)}")
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ Automatic identification of technical terms")
    print("  ✓ Multi-language explanations for terms")
    print("  ✓ Preservation of terms during translation")
    print("  ✓ Comprehensive glossary with explanations")
    print("  ✓ Support for insurance and medical terminology")
    print("  ✓ Case-insensitive term matching")
    print()


if __name__ == "__main__":
    asyncio.run(demonstrate_technical_term_handling())
