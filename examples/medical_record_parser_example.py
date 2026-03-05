"""
Example demonstrating the Medical Record Parser functionality.

This example shows how to:
1. Parse medical records from text content
2. Extract structured information (diagnoses, medications, tests, procedures)
3. Handle various medical record formats
4. Deal with incomplete or malformed records
"""

from healthcare_insurance_platform.services.medical_summarizer import (
    MedicalRecordParser,
    MedicalSummarizer
)


def example_basic_parsing():
    """Example: Basic medical record parsing."""
    print("=" * 70)
    print("Example 1: Basic Medical Record Parsing")
    print("=" * 70)
    
    parser = MedicalRecordParser()
    
    # Sample medical record
    medical_record = """
    Patient Medical Record
    Date: 15/03/2023
    Patient ID: PAT12345
    
    Chief Complaint: Fatigue and increased thirst
    
    Diagnosis: Type 2 Diabetes Mellitus, Hypertension
    
    Current Medications:
    - Metformin 500mg twice daily
    - Lisinopril 10mg once daily
    - Aspirin 75mg once daily
    
    Lab Results:
    HbA1c: 7.2%
    Blood Sugar (Fasting): 145 mg/dL
    Cholesterol: 220 mg/dL
    Creatinine: 1.1 mg/dL
    
    Allergies: Penicillin, Sulfa drugs
    
    Vital Signs:
    BP: 140/90
    HR: 78 bpm
    Temp: 98.6°F
    Weight: 75 kg
    Height: 170 cm
    """
    
    # Parse the record
    result = parser.parse_medical_record(text_content=medical_record)
    
    # Display extracted information
    print("\n📋 Extracted Information:\n")
    
    print(f"Diagnoses ({len(result['diagnoses'])}):")
    for diagnosis in result['diagnoses']:
        print(f"  • {diagnosis['condition']}")
        if diagnosis['date']:
            print(f"    Date: {diagnosis['date']}")
    
    print(f"\n💊 Medications ({len(result['medications'])}):")
    for med in result['medications']:
        print(f"  • {med['name']} - {med['dosage']} - {med['frequency']}")
    
    print(f"\n🧪 Tests ({len(result['tests'])}):")
    for test in result['tests']:
        print(f"  • {test['test_name']}: {test['result']}")
    
    print(f"\n⚠️  Allergies ({len(result['allergies'])}):")
    for allergy in result['allergies']:
        print(f"  • {allergy}")
    
    print(f"\n📊 Vital Signs ({len(result['vital_signs'])}):")
    for sign, value in result['vital_signs'].items():
        print(f"  • {sign.replace('_', ' ').title()}: {value}")
    
    print("\n✅ Successfully parsed medical record!\n")


def example_multiple_records():
    """Example: Parsing multiple medical records."""
    print("=" * 70)
    print("Example 2: Parsing Multiple Medical Records")
    print("=" * 70)
    
    summarizer = MedicalSummarizer()
    
    # Multiple medical records
    records = [
        """
        Visit Date: 01/01/2023
        Diagnosis: Pneumonia
        Medications: Amoxicillin 500mg three times daily
        Procedures: Chest X-ray performed
        """,
        """
        Visit Date: 15/02/2023
        Diagnosis: Asthma exacerbation
        Medications: Albuterol inhaler as needed, Prednisone 20mg daily for 5 days
        Allergies: None known
        """,
        """
        Visit Date: 10/03/2023
        Diagnosis: Hypertension
        Medications: Amlodipine 5mg once daily
        Vital Signs: BP: 150/95, HR: 82
        """
    ]
    
    # Parse all records
    parsed_records = summarizer.parse_records(text_contents=records)
    
    print(f"\n📚 Parsed {len(parsed_records)} medical records:\n")
    
    for i, record in enumerate(parsed_records, 1):
        print(f"Record {i}:")
        print(f"  Diagnoses: {len(record['diagnoses'])}")
        print(f"  Medications: {len(record['medications'])}")
        print(f"  Tests: {len(record['tests'])}")
        print(f"  Procedures: {len(record['procedures'])}")
        
        if record['diagnoses']:
            print(f"  Primary diagnosis: {record['diagnoses'][0]['condition']}")
        print()
    
    print("✅ Successfully parsed multiple records!\n")


def example_incomplete_record():
    """Example: Handling incomplete medical records."""
    print("=" * 70)
    print("Example 3: Handling Incomplete Medical Records")
    print("=" * 70)
    
    parser = MedicalRecordParser()
    
    # Incomplete record with only some information
    incomplete_record = """
    Patient presents with chest pain.
    
    Diagnosis: Angina
    
    ECG performed - shows ST segment changes.
    """
    
    result = parser.parse_medical_record(text_content=incomplete_record)
    
    print("\n📋 Parsed Incomplete Record:\n")
    print(f"Diagnoses: {len(result['diagnoses'])} found")
    print(f"Medications: {len(result['medications'])} found")
    print(f"Tests: {len(result['tests'])} found")
    print(f"Procedures: {len(result['procedures'])} found")
    print(f"Allergies: {len(result['allergies'])} found")
    print(f"Vital Signs: {len(result['vital_signs'])} found")
    
    if result['diagnoses']:
        print(f"\nExtracted diagnosis: {result['diagnoses'][0]['condition']}")
    
    print("\n✅ Gracefully handled incomplete record!\n")


def example_malformed_record():
    """Example: Handling malformed medical records."""
    print("=" * 70)
    print("Example 4: Handling Malformed Medical Records")
    print("=" * 70)
    
    parser = MedicalRecordParser()
    
    # Malformed record with poor formatting
    malformed_record = """
    patient has diabetes and high blood pressure
    taking some pills for sugar
    allergic to penicillin
    bp was 150/90 last time
    """
    
    result = parser.parse_medical_record(text_content=malformed_record)
    
    print("\n📋 Parsed Malformed Record:\n")
    
    # The parser should still extract some information
    if result['diagnoses']:
        print("Diagnoses found:")
        for diagnosis in result['diagnoses']:
            print(f"  • {diagnosis['condition']}")
    
    if result['allergies']:
        print("\nAllergies found:")
        for allergy in result['allergies']:
            print(f"  • {allergy}")
    
    if result['vital_signs']:
        print("\nVital signs found:")
        for sign, value in result['vital_signs'].items():
            print(f"  • {sign.replace('_', ' ').title()}: {value}")
    
    print("\n✅ Handled malformed record without errors!\n")


def example_comprehensive_record():
    """Example: Comprehensive medical record with all sections."""
    print("=" * 70)
    print("Example 5: Comprehensive Medical Record")
    print("=" * 70)
    
    parser = MedicalRecordParser()
    
    comprehensive_record = """
    PATIENT MEDICAL RECORD
    =====================
    
    Patient ID: PAT67890
    Date: 20/03/2023
    
    CHIEF COMPLAINT:
    Shortness of breath and chest tightness
    
    DIAGNOSIS:
    Primary Diagnosis: Chronic Obstructive Pulmonary Disease (COPD)
    Secondary Diagnosis: Coronary Artery Disease
    
    CURRENT MEDICATIONS:
    - Tiotropium 18mcg inhaler once daily
    - Salmeterol/Fluticasone 50/250mcg inhaler twice daily
    - Atorvastatin 40mg at bedtime
    - Aspirin 81mg once daily
    - Metoprolol 25mg twice daily
    
    LABORATORY RESULTS:
    Spirometry: FEV1 55% predicted
    Chest X-ray: Hyperinflation, flattened diaphragm
    ECG: Normal sinus rhythm
    Troponin: Negative
    BNP: 85 pg/mL
    
    PROCEDURES PERFORMED:
    - Pulmonary function test on 20/03/2023
    - Chest X-ray on 20/03/2023
    - ECG on 20/03/2023
    
    ALLERGIES:
    Penicillin (rash), Codeine (nausea)
    
    VITAL SIGNS:
    Blood Pressure: 135/85 mmHg
    Heart Rate: 88 bpm
    Respiratory Rate: 22 breaths/min
    Oxygen Saturation: 92% on room air
    Temperature: 98.2°F
    Weight: 68 kg
    Height: 165 cm
    
    PAST MEDICAL HISTORY:
    - Hypertension (diagnosed 2015)
    - Type 2 Diabetes (diagnosed 2018)
    - Former smoker (quit 2020)
    """
    
    result = parser.parse_medical_record(text_content=comprehensive_record)
    
    print("\n📋 Comprehensive Record Analysis:\n")
    
    print(f"✓ Diagnoses: {len(result['diagnoses'])} extracted")
    for diagnosis in result['diagnoses'][:3]:  # Show first 3
        print(f"    • {diagnosis['condition']}")
    
    print(f"\n✓ Medications: {len(result['medications'])} extracted")
    for med in result['medications'][:3]:  # Show first 3
        print(f"    • {med['name']} ({med['dosage']})")
    
    print(f"\n✓ Tests: {len(result['tests'])} extracted")
    for test in result['tests'][:3]:  # Show first 3
        print(f"    • {test['test_name']}")
    
    print(f"\n✓ Procedures: {len(result['procedures'])} extracted")
    for proc in result['procedures'][:3]:  # Show first 3
        print(f"    • {proc['procedure']}")
    
    print(f"\n✓ Allergies: {len(result['allergies'])} extracted")
    for allergy in result['allergies']:
        print(f"    • {allergy}")
    
    print(f"\n✓ Vital Signs: {len(result['vital_signs'])} extracted")
    for sign, value in list(result['vital_signs'].items())[:3]:  # Show first 3
        print(f"    • {sign.replace('_', ' ').title()}: {value}")
    
    print("\n✅ Successfully parsed comprehensive medical record!\n")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("MEDICAL RECORD PARSER EXAMPLES")
    print("=" * 70 + "\n")
    
    try:
        example_basic_parsing()
        example_multiple_records()
        example_incomplete_record()
        example_malformed_record()
        example_comprehensive_record()
        
        print("=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
