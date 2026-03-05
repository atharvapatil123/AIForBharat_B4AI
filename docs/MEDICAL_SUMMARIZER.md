# Medical Summarizer Service

## Overview

The Medical Summarizer service provides comprehensive medical history summarization capabilities for clinical decision-making. It processes medical records and generates structured summaries with chronological timelines, abnormal result detection, and clinical insights.

## Features

### 1. Timeline Generation (Task 11.2)
Organizes medical events chronologically with intelligent significance classification.

**Capabilities:**
- Chronological organization of all medical events
- Automatic identification and highlighting of key events
- Condition status tracking over time
- Event classification by significance (critical, important, routine)

**Event Types:**
- `diagnosis`: New diagnoses and conditions
- `procedure`: Surgical and medical procedures
- `test`: Laboratory tests and diagnostic imaging
- `medication_change`: Medication additions or modifications

**Significance Levels:**
- `critical`: Life-threatening conditions (cancer, stroke, heart attack, etc.)
- `important`: Chronic conditions requiring management (diabetes, hypertension, etc.)
- `routine`: Standard care events and monitoring

### 2. Abnormal Result Detection (Task 11.3)
Identifies abnormal test results and tracks trends over time.

**Capabilities:**
- Automatic detection of abnormal test results
- Trend analysis across multiple test dates
- Identification of worsening, stable, or improving patterns
- Highlighting of significant changes requiring attention

**Trend Analysis:**
- `worsening`: Test results deteriorating over time (>10% change)
- `improving`: Test results getting better over time (>10% change)
- `stable`: Test results remaining relatively constant

**Supported Tests:**
- Blood glucose and HbA1c (diabetes monitoring)
- Cholesterol panels (cardiovascular risk)
- Hemoglobin (anemia detection)
- Creatinine (kidney function)
- Blood pressure (hypertension monitoring)
- And more...

### 3. Summary Generation (Task 11.4)
Generates concise medical summaries formatted for clinical decision-making.

**Components:**
- **Current Conditions**: Active medical diagnoses with status
- **Current Medications**: Active prescriptions with dosage and purpose
- **Allergies**: Known drug and substance allergies
- **Timeline Events**: Chronological medical history
- **Abnormal Findings**: Test results outside normal ranges
- **Risk Factors**: Identified health risk factors
- **Summary Text**: Narrative summary for quick review
- **Explanation**: Clinical interpretation of key findings
- **Citations**: Source references for all information

## Usage

### Basic Usage

```python
from healthcare_insurance_platform.services.medical_summarizer import MedicalSummarizer

# Initialize the summarizer
summarizer = MedicalSummarizer()

# Parse medical records
parsed_records = summarizer.parse_records(
    text_contents=[medical_record_text]
)

# Generate complete summary
summary = summarizer.generate_summary(
    patient_id="P12345",
    parsed_records=parsed_records,
    language='en'
)

# Access summary components
print(summary.summary_text)
print(f"Conditions: {len(summary.current_conditions)}")
print(f"Medications: {len(summary.current_medications)}")
print(f"Abnormal findings: {len(summary.abnormal_findings)}")
```

### Timeline Generation Only

```python
# Generate just the timeline
timeline = summarizer.generate_timeline(parsed_records)

# Filter by significance
critical_events = [e for e in timeline if e.significance == 'critical']
important_events = [e for e in timeline if e.significance == 'important']

# Display events
for event in timeline:
    print(f"{event.date}: {event.description} [{event.significance}]")
```

### Abnormal Result Detection Only

```python
# Detect abnormal results
abnormal_findings = summarizer.detect_abnormal_results(parsed_records)

# Filter by trend
worsening = [f for f in abnormal_findings if f.trend == 'worsening']

# Display findings
for finding in abnormal_findings:
    print(f"{finding.test_type}: {finding.finding}")
    print(f"Trend: {finding.trend}")
```

## Input Format

The service accepts medical records in various formats:

### Text Format
```
Patient Medical Record

Date: 2024-01-15

Diagnosis: Type 2 Diabetes Mellitus, Hypertension

Medications:
- Metformin 500mg twice daily
- Lisinopril 10mg once daily

Lab Results:
- Blood Sugar: 180 mg/dL (High)
- HbA1c: 8.5% (Elevated)

Allergies: Penicillin

Procedures:
- Cardiac stress test performed on 2024-01-10
```

### File Formats
- PDF medical records
- Plain text files
- Structured medical documents

## Output Models

### MedicalSummary
```python
{
    "summary_id": "summary_P12345_20240115120000",
    "patient_id": "P12345",
    "timeline_events": [...],
    "current_conditions": [...],
    "current_medications": [...],
    "allergies": ["Penicillin"],
    "abnormal_findings": [...],
    "risk_factors": ["Diabetes mellitus", "Hypertension"],
    "summary_text": "Current conditions: Type 2 Diabetes...",
    "explanation": "Patient has 2 active medical conditions...",
    "citations": ["Medical record 1"],
    "language": "en",
    "generated_at": "2024-01-15T12:00:00Z"
}
```

### TimelineEvent
```python
{
    "date": "2024-01-15",
    "event_type": "diagnosis",
    "description": "Diagnosed with Type 2 Diabetes Mellitus",
    "significance": "important"
}
```

### AbnormalFinding
```python
{
    "test_type": "Blood Sugar",
    "date": "2024-01-15",
    "finding": "Blood Sugar result of 180 mg/dL is outside normal range",
    "trend": "worsening"
}
```

### CurrentCondition
```python
{
    "condition": "Type 2 Diabetes Mellitus",
    "diagnosis_date": "2020-03-15",
    "status": "active",
    "treatments": ["Metformin", "Lifestyle modifications"]
}
```

### CurrentMedication
```python
{
    "name": "Metformin",
    "dosage": "500mg twice daily",
    "purpose": "Treatment",
    "start_date": "2020-03-15"
}
```

## Clinical Use Cases

### 1. Pre-Appointment Review
Quickly review patient history before appointments:
```python
summary = summarizer.generate_summary(patient_id, records)
print(summary.summary_text)  # Quick overview
print(f"Active conditions: {len(summary.current_conditions)}")
```

### 2. Trend Monitoring
Track patient progress over time:
```python
abnormal_findings = summarizer.detect_abnormal_results(records)
worsening = [f for f in abnormal_findings if f.trend == 'worsening']
if worsening:
    print("Alert: Worsening trends detected")
```

### 3. Medication Review
Review current medications and identify potential issues:
```python
summary = summarizer.generate_summary(patient_id, records)
for med in summary.current_medications:
    print(f"{med.name}: {med.dosage}")
```

### 4. Risk Assessment
Identify risk factors for treatment planning:
```python
summary = summarizer.generate_summary(patient_id, records)
print(f"Risk factors: {', '.join(summary.risk_factors)}")
```

## Requirements Validation

This implementation validates the following requirements:

- **Requirement 8.1**: Medical history summarization with key information extraction
- **Requirement 8.2**: Chronological organization with key event highlighting
- **Requirement 8.3**: Abnormal result detection with trend tracking
- **Requirement 8.4**: Clinical decision-making format with current conditions and medications

## Error Handling

The service handles various error conditions gracefully:

- **Empty records**: Returns empty summary structure
- **Malformed data**: Continues processing with available data
- **Missing dates**: Uses current date as fallback
- **Incomplete information**: Marks fields as "Not specified"

## Performance Considerations

- **Processing time**: ~1-2 seconds for typical medical records
- **Memory usage**: Minimal, suitable for batch processing
- **Scalability**: Can process multiple records concurrently

## Limitations

- Text-based parsing may miss complex medical terminology
- Trend analysis requires at least 2 data points
- Abnormal detection uses simplified reference ranges
- Does not replace professional medical judgment

## Future Enhancements

Potential improvements for future versions:

1. Integration with medical terminology databases (SNOMED, ICD-10)
2. Machine learning-based abnormal result detection
3. Predictive analytics for disease progression
4. Integration with electronic health record (EHR) systems
5. Support for medical imaging analysis
6. Natural language generation for patient-friendly summaries

## Examples

See `examples/medical_summarizer_example.py` for comprehensive usage examples demonstrating all three tasks:
- Timeline generation
- Abnormal result detection
- Complete summary generation

## API Reference

### MedicalSummarizer

#### `__init__()`
Initialize the medical summarizer service.

#### `parse_records(file_paths=None, text_contents=None) -> List[Dict]`
Parse medical records from files or text.

**Parameters:**
- `file_paths`: List of file paths to medical records
- `text_contents`: List of raw text contents

**Returns:** List of parsed medical record data

#### `generate_timeline(parsed_records) -> List[TimelineEvent]`
Generate chronological timeline of medical events.

**Parameters:**
- `parsed_records`: List of parsed medical record data

**Returns:** List of TimelineEvent objects sorted chronologically

**Validates:** Requirements 8.2

#### `detect_abnormal_results(parsed_records) -> List[AbnormalFinding]`
Identify abnormal test results and track trends.

**Parameters:**
- `parsed_records`: List of parsed medical record data

**Returns:** List of AbnormalFinding objects

**Validates:** Requirements 8.3

#### `generate_summary(patient_id, parsed_records, language='en') -> MedicalSummary`
Generate comprehensive medical summary.

**Parameters:**
- `patient_id`: Patient identifier
- `parsed_records`: List of parsed medical record data
- `language`: Language code for output (default: 'en')

**Returns:** MedicalSummary object with complete patient history

**Validates:** Requirements 8.1, 8.4

## Support

For issues or questions about the Medical Summarizer service, please refer to:
- Implementation: `healthcare_insurance_platform/services/medical_summarizer.py`
- Examples: `examples/medical_summarizer_example.py`
- Tests: `tests/services/test_medical_summarizer.py`
