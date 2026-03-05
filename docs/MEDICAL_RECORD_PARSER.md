# Medical Record Parser

## Overview

The Medical Record Parser is a component of the Medical Summarizer service that extracts structured information from various medical record formats. It handles text-based medical records (plain text, PDF) and extracts key clinical information including diagnoses, medications, tests, procedures, allergies, and vital signs.

**Validates Requirements:** 8.1

## Features

- **Multi-format Support**: Parses medical records from text files and PDF documents
- **Comprehensive Extraction**: Extracts diagnoses, medications, tests, procedures, allergies, and vital signs
- **Robust Parsing**: Handles incomplete, malformed, or poorly formatted records gracefully
- **Date Normalization**: Converts various date formats to ISO standard (YYYY-MM-DD)
- **Error Resilience**: Returns partial results rather than failing completely on errors

## Architecture

```
MedicalSummarizer
    └── MedicalRecordParser
            ├── parse_medical_record()
            ├── _extract_diagnoses()
            ├── _extract_medications()
            ├── _extract_tests()
            ├── _extract_procedures()
            ├── _extract_allergies()
            ├── _extract_vital_signs()
            └── _normalize_date()
```

## Usage

### Basic Usage

```python
from healthcare_insurance_platform.services.medical_summarizer import MedicalRecordParser

# Initialize parser
parser = MedicalRecordParser()

# Parse from text content
medical_record_text = """
Diagnosis: Type 2 Diabetes Mellitus
Medications: Metformin 500mg twice daily
Allergies: Penicillin
"""

result = parser.parse_medical_record(text_content=medical_record_text)

# Access extracted information
print(f"Diagnoses: {result['diagnoses']}")
print(f"Medications: {result['medications']}")
print(f"Allergies: {result['allergies']}")
```

### Parsing from File

```python
from pathlib import Path

# Parse from file (supports .txt and .pdf)
file_path = Path("patient_record.pdf")
result = parser.parse_medical_record(file_path=file_path)
```

### Parsing Multiple Records

```python
from healthcare_insurance_platform.services.medical_summarizer import MedicalSummarizer

summarizer = MedicalSummarizer()

# Parse multiple records at once
records = [
    "Diagnosis: Hypertension\nMedications: Lisinopril 10mg daily",
    "Diagnosis: Asthma\nMedications: Albuterol inhaler as needed"
]

results = summarizer.parse_records(text_contents=records)

for i, record in enumerate(results):
    print(f"Record {i+1}: {len(record['diagnoses'])} diagnoses found")
```

## Extracted Data Structure

The parser returns a dictionary with the following structure:

```python
{
    'diagnoses': [
        {
            'condition': str,  # Diagnosis name
            'date': str,       # ISO format date (YYYY-MM-DD) or None
            'type': str        # 'diagnosis'
        }
    ],
    'medications': [
        {
            'name': str,       # Medication name
            'dosage': str,     # Dosage (e.g., "500mg")
            'frequency': str   # Frequency (e.g., "twice daily")
        }
    ],
    'tests': [
        {
            'test_name': str,  # Test name
            'result': str,     # Test result
            'date': str        # ISO format date or None
        }
    ],
    'procedures': [
        {
            'procedure': str,  # Procedure description
            'date': str        # ISO format date or None
        }
    ],
    'allergies': [str],        # List of allergy names
    'vital_signs': {
        'blood_pressure': str,     # e.g., "140/90"
        'heart_rate': str,         # e.g., "78"
        'temperature': str,        # e.g., "98.6"
        'respiratory_rate': str,   # e.g., "18"
        'oxygen_saturation': str,  # e.g., "95%"
        'weight': str,             # e.g., "75 kg"
        'height': str              # e.g., "170 cm"
    }
}
```

## Supported Medical Record Formats

### Structured Format

The parser works best with structured medical records that have clear section headers:

```
Diagnosis: Type 2 Diabetes Mellitus

Medications:
- Metformin 500mg twice daily
- Lisinopril 10mg once daily

Lab Results:
HbA1c: 7.2%
Blood Sugar: 145 mg/dL

Allergies: Penicillin, Sulfa drugs

Vital Signs:
BP: 140/90
HR: 78
```

### Semi-Structured Format

The parser can also handle less structured formats:

```
Patient has diabetes and hypertension.
Taking metformin and lisinopril.
Allergic to penicillin.
Blood pressure was 140/90.
```

### Common Medical Abbreviations

The parser recognizes common medical abbreviations:
- BP (Blood Pressure)
- HR (Heart Rate)
- RR (Respiratory Rate)
- O2/SpO2 (Oxygen Saturation)
- CBC (Complete Blood Count)
- ECG/EKG (Electrocardiogram)
- HbA1c (Glycated Hemoglobin)

## Error Handling

### Empty or Short Content

```python
result = parser.parse_medical_record(text_content="")
# Returns empty structure with all fields as empty lists/dicts
```

### Malformed Records

```python
result = parser.parse_medical_record(text_content="Random text")
# Returns structure with whatever information could be extracted
# Does not raise exceptions
```

### Missing Sections

If a medical record is missing certain sections (e.g., no medications listed), those fields will be empty lists:

```python
result = parser.parse_medical_record(text_content="Diagnosis: Diabetes")
# result['diagnoses'] will have entries
# result['medications'] will be []
```

## Extraction Patterns

### Diagnoses

Looks for patterns like:
- "Diagnosis: [condition]"
- "Diagnosed with [condition]"
- "Primary/Secondary Diagnosis: [condition]"
- Common disease names (diabetes, hypertension, asthma, etc.)

### Medications

Looks for patterns like:
- "Medications: [list]"
- "Prescriptions: [list]"
- "[Drug name] [dosage] [frequency]"
- Bullet points or numbered lists

### Tests

Looks for patterns like:
- "Lab Results: [list]"
- "Test Results: [list]"
- "[Test name]: [value]"
- Common test names (CBC, HbA1c, X-ray, etc.)

### Allergies

Looks for patterns like:
- "Allergies: [list]"
- "Allergic to: [list]"
- Comma-separated or bullet-pointed lists
- Filters out "None", "NKDA" (No Known Drug Allergies)

### Vital Signs

Extracts specific patterns:
- Blood Pressure: "BP: 120/80" or "Blood Pressure: 120/80"
- Heart Rate: "HR: 72" or "Pulse: 72"
- Temperature: "Temp: 98.6" or "Temperature: 98.6"
- Weight: "Weight: 75 kg"
- Height: "Height: 170 cm"

## Limitations

1. **Language**: Currently optimized for English medical records
2. **Format**: Works best with text-based records; cannot extract from images or handwritten notes
3. **Accuracy**: Extraction accuracy depends on record structure and formatting
4. **Context**: Does not understand medical context or relationships between findings
5. **Validation**: Does not validate medical accuracy of extracted information

## Best Practices

1. **Structured Input**: Provide well-structured medical records with clear section headers for best results
2. **Multiple Records**: When parsing multiple records, use `MedicalSummarizer.parse_records()` for batch processing
3. **Error Checking**: Always check if extracted lists are empty before processing
4. **Date Validation**: Verify extracted dates are in expected format (YYYY-MM-DD)
5. **Manual Review**: Use parser output as a starting point; always review extracted information

## Examples

See `examples/medical_record_parser_example.py` for comprehensive usage examples including:
- Basic parsing
- Multiple record parsing
- Handling incomplete records
- Handling malformed records
- Comprehensive record parsing

## Integration with Medical Summarizer

The Medical Record Parser is designed to be used as part of the larger Medical Summarizer service, which will:
1. Parse medical records (using this parser)
2. Generate chronological timelines
3. Identify abnormal findings
4. Create clinical summaries
5. Support multilingual output

## Future Enhancements

Planned improvements include:
- Support for additional languages
- OCR integration for scanned documents
- Medical entity recognition using NLP
- Relationship extraction between diagnoses and treatments
- Integration with medical ontologies (ICD-10, SNOMED CT)
- Confidence scores for extracted information

## Related Components

- **MedicalSummarizer**: Parent service that uses this parser
- **DocumentParser**: Base document parsing utilities
- **LLM Engine**: Used for advanced medical text understanding
- **Translation Service**: For multilingual medical record support

## Testing

Run the test suite:

```bash
# Simple logic tests
python test_medical_parser_simple.py

# Full integration tests (requires dependencies)
python test_medical_record_parser.py
```

## API Reference

### MedicalRecordParser

#### `parse_medical_record(file_path=None, text_content=None)`

Parse medical record from file or text content.

**Parameters:**
- `file_path` (str | Path, optional): Path to medical record file
- `text_content` (str, optional): Raw text content of medical record

**Returns:**
- `dict`: Dictionary containing extracted medical information

**Raises:**
- `ValueError`: If neither file_path nor text_content is provided
- `FileNotFoundError`: If file_path does not exist

### MedicalSummarizer

#### `parse_records(file_paths=None, text_contents=None)`

Parse multiple medical records.

**Parameters:**
- `file_paths` (List[str | Path], optional): List of file paths
- `text_contents` (List[str], optional): List of text contents

**Returns:**
- `List[dict]`: List of parsed medical record data

## Support

For issues or questions about the Medical Record Parser:
1. Check the examples in `examples/medical_record_parser_example.py`
2. Review the test cases in `test_medical_parser_simple.py`
3. Consult the design document at `.kiro/specs/healthcare-insurance-intelligence/design.md`
