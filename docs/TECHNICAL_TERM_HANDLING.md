# Technical Term Handling in Translation Service

## Overview

The Translation Service includes sophisticated technical term handling that ensures medical and insurance terminology is properly preserved and explained during translation. This addresses **Requirement 4.4**: "WHEN technical terms have no direct translation, THE Platform SHALL provide the original term with an explanation in the target language."

## Features

### 1. Automatic Term Identification

The service automatically identifies technical terms in text using:
- **Pattern matching**: Regular expressions for common term patterns
- **Glossary lookup**: Direct matching against a comprehensive glossary
- **Case-insensitive matching**: Works regardless of capitalization

**Supported Term Categories:**
- Insurance terms (waiting period, copayment, deductible, PED, exclusions, etc.)
- Medical terms (hypertension, diabetes mellitus, chemotherapy, etc.)
- Legal terms (policy holder, nominee, claim settlement ratio, etc.)

### 2. Multi-Language Glossary

A comprehensive glossary provides explanations for technical terms in all supported languages:
- English (en)
- Hindi (hi)
- Tamil (ta)
- Telugu (te)
- Bengali (bn)
- Marathi (mr)
- Gujarati (gu)

Each term includes:
- Original term in source language
- Clear explanation in target language
- Context-appropriate definitions

### 3. Terminology Preservation

The `preserve_terminology()` method:
1. Identifies all technical terms in the source text
2. Translates the surrounding text while keeping technical terms in original language
3. Provides a glossary with explanations for each preserved term
4. Returns both translated content and comprehensive glossary

## API Reference

### `identify_technical_terms(text: str) -> Set[str]`

Identifies technical terms in the given text.

**Parameters:**
- `text`: Text to analyze

**Returns:**
- Set of identified technical terms

**Example:**
```python
service = TranslationService()
text = "The policy has a waiting period and copayment."
terms = service.identify_technical_terms(text)
# Returns: {'waiting period', 'copayment'}
```

### `get_term_explanation(term: str, target_language: str) -> Optional[str]`

Retrieves explanation for a technical term in the target language.

**Parameters:**
- `term`: Technical term to explain
- `target_language`: ISO language code (e.g., 'hi', 'ta')

**Returns:**
- Explanation in target language, or None if term not in glossary

**Example:**
```python
explanation = service.get_term_explanation("waiting period", "hi")
# Returns: "पॉलिसी खरीद के बाद की अवधि जिसमें कुछ दावे कवर नहीं होते"
```

### `preserve_terminology(text: str, target_language: str, source_language: str = "en") -> TranslatedTextWithGlossary`

Translates text while preserving technical terminology.

**Parameters:**
- `text`: Text to translate
- `target_language`: Target language ISO code
- `source_language`: Source language ISO code (default: "en")

**Returns:**
- `TranslatedTextWithGlossary` object containing:
  - `translated_content`: Translated text with preserved terms
  - `source_language`: Source language code
  - `target_language`: Target language code
  - `glossary`: List of TechnicalTerm objects with explanations
  - `confidence_score`: Translation confidence (0-1)

**Example:**
```python
result = await service.preserve_terminology(
    text="The insurance policy has a waiting period.",
    target_language="hi",
    source_language="en",
)

print(result.translated_content)
# "बीमा पॉलिसी में waiting period है"

for term in result.glossary:
    print(f"{term.original_term}: {term.explanation}")
# "waiting period: पॉलिसी खरीद के बाद की अवधि..."
```

## Data Models

### `TechnicalTerm`

Represents a technical term with its explanation.

**Fields:**
- `original_term` (str): Original term in source language
- `translated_term` (Optional[str]): Translated term if available
- `explanation` (str): Explanation in target language

### `TranslatedTextWithGlossary`

Translation result with comprehensive glossary.

**Fields:**
- `translated_content` (str): Translated text with preserved terms
- `source_language` (str): Source language code
- `target_language` (str): Target language code
- `glossary` (List[TechnicalTerm]): Glossary of preserved terms
- `confidence_score` (Optional[float]): Translation confidence

## Technical Glossary

The service includes a comprehensive glossary covering:

### Insurance Terms
- **pre-existing disease / PED**: Medical condition existing before insurance purchase
- **waiting period**: Time after policy purchase when certain claims aren't covered
- **copayment**: Percentage of expenses insured must pay
- **deductible**: Fixed amount paid before coverage begins
- **exclusion**: Conditions/treatments not covered
- **claim settlement ratio**: Percentage of claims approved and paid
- **sum insured**: Maximum coverage amount
- **premium**: Insurance cost
- **cashless treatment**: Direct payment to hospital
- **reimbursement**: Payment back to insured

### Medical Terms
- **hypertension**: High blood pressure
- **diabetes mellitus**: Chronic blood sugar condition
- **cardiovascular disease**: Heart and blood vessel diseases
- **chemotherapy**: Cancer treatment using drugs
- **radiotherapy**: Cancer treatment using radiation
- **dialysis**: Kidney function replacement treatment
- **angioplasty**: Procedure to open blocked arteries
- **chronic**: Long-lasting condition
- **acute**: Sudden, severe condition

## Usage Examples

### Example 1: Basic Term Identification

```python
from healthcare_insurance_platform.services.translation import TranslationService

service = TranslationService()

text = """
The insurance policy covers hospitalization but has exclusions 
for pre-existing diseases. The waiting period is 30 days and 
copayment is 20%.
"""

terms = service.identify_technical_terms(text)
print(f"Found {len(terms)} technical terms:")
for term in terms:
    print(f"  - {term}")
```

### Example 2: Get Explanations in Multiple Languages

```python
term = "waiting period"

# Get explanation in different languages
for lang in ["en", "hi", "ta", "te"]:
    explanation = service.get_term_explanation(term, lang)
    print(f"{lang}: {explanation}")
```

### Example 3: Translate with Terminology Preservation

```python
policy_text = """
This policy covers hospitalization expenses after the waiting period.
Pre-existing diseases (PED) have a 2-year waiting period.
Copayment of 20% applies to all claims.
"""

result = await service.preserve_terminology(
    text=policy_text,
    target_language="hi",
    source_language="en",
)

print("Translated Text:")
print(result.translated_content)

print("\nGlossary:")
for term in result.glossary:
    print(f"\n{term.original_term}")
    print(f"  {term.explanation}")
```

### Example 4: Medical Content Translation

```python
medical_text = """
Patient diagnosed with hypertension and diabetes mellitus.
Requires chemotherapy for cardiovascular disease treatment.
"""

result = await service.preserve_terminology(
    text=medical_text,
    target_language="ta",
    source_language="en",
)

# Medical terms preserved with Tamil explanations
print(result.translated_content)
for term in result.glossary:
    print(f"{term.original_term}: {term.explanation}")
```

## Implementation Details

### Term Identification Algorithm

1. **Pattern Matching**: Text is scanned using regex patterns for common term structures
2. **Glossary Lookup**: Direct string matching against glossary keys (case-insensitive)
3. **Deduplication**: Identified terms are deduplicated and normalized

### Translation Process

1. **Pre-processing**: Identify all technical terms in source text
2. **Context Assembly**: Build glossary entries for identified terms
3. **LLM Translation**: Use specialized prompt that instructs LLM to preserve terms
4. **Post-processing**: Parse LLM response to extract translation and glossary
5. **Validation**: Ensure all identified terms are in the glossary

### Glossary Management

The glossary is maintained as a static dictionary in the service:
- **Centralized**: Single source of truth for all term definitions
- **Versioned**: Changes tracked through code version control
- **Extensible**: New terms can be added easily
- **Validated**: All terms must have explanations in all supported languages

## Best Practices

### When to Use `preserve_terminology()`

Use this method when:
- Translating insurance policy documents
- Translating medical records or reports
- Translating legal or technical content
- Accuracy of technical terms is critical

### When to Use Regular `translate()`

Use regular translation when:
- Translating general conversational text
- Technical accuracy is less critical
- You want more natural-sounding translations

### Adding New Terms

To add a new technical term to the glossary:

1. Add entry to `TECHNICAL_GLOSSARY` dictionary
2. Provide explanations in ALL supported languages
3. Add regex pattern to `TECHNICAL_TERM_PATTERNS` if needed
4. Test identification and explanation retrieval
5. Update documentation

Example:
```python
TECHNICAL_GLOSSARY = {
    # ... existing terms ...
    "new_term": {
        "en": "English explanation",
        "hi": "Hindi explanation",
        "ta": "Tamil explanation",
        "te": "Telugu explanation",
        "bn": "Bengali explanation",
        "mr": "Marathi explanation",
        "gu": "Gujarati explanation",
    },
}
```

## Testing

The technical term handling includes comprehensive tests:

### Unit Tests
- Term identification accuracy
- Explanation retrieval for all languages
- Case-insensitive matching
- Glossary completeness
- Edge cases (empty text, unknown terms)

### Integration Tests
- End-to-end translation with term preservation
- Multi-language glossary generation
- LLM integration for term explanation

### Property Tests
- **Property 9**: Technical term handling in translation
  - Validates: Requirement 4.4

Run tests:
```bash
pytest tests/services/test_translation.py::TestTechnicalTermIdentification -v
pytest tests/services/test_translation.py::TestTermExplanation -v
pytest tests/services/test_translation.py::TestPreserveTerminology -v
```

## Limitations and Future Enhancements

### Current Limitations
- Glossary is static and requires code changes to update
- Limited to predefined terms and patterns
- May miss domain-specific terms not in glossary

### Planned Enhancements
- Dynamic glossary updates from admin interface
- Machine learning-based term identification
- Context-aware term disambiguation
- User-contributed term definitions
- Automatic glossary expansion from policy documents

## Related Documentation

- [Translation Service Overview](TRANSLATION_SERVICE.md)
- [LLM Integration Guide](LLM_INTEGRATION.md)
- [Multilingual Support](../README.md#multilingual-support)
- [Requirements Document](../.kiro/specs/healthcare-insurance-intelligence/requirements.md)

## Support

For questions or issues related to technical term handling:
1. Check this documentation
2. Review test cases in `tests/services/test_translation.py`
3. See examples in `examples/technical_term_example.py`
4. Consult the design document for requirements
