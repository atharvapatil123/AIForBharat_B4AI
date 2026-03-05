"""Simple test to verify medical record parser implementation."""

from healthcare_insurance_platform.services.medical_summarizer import (
    MedicalRecordParser,
    MedicalSummarizer
)


def test_medical_record_parser_basic():
    """Test basic medical record parsing functionality."""
    parser = MedicalRecordParser()
    
    # Test with sample medical record text
    sample_record = """
    Patient Medical Record
    
    Date: 15/03/2023
    
    Diagnosis: Type 2 Diabetes Mellitus, Hypertension
    
    Medications:
    - Metformin 500mg twice daily
    - Lisinopril 10mg once daily
    - Aspirin 75mg once daily
    
    Lab Results:
    HbA1c: 7.2%
    Blood Sugar (Fasting): 145 mg/dL
    Blood Pressure: 140/90
    Cholesterol: 220 mg/dL
    
    Allergies: Penicillin, Sulfa drugs
    
    Procedures:
    - ECG performed on 15/03/2023
    
    Vital Signs:
    BP: 140/90
    HR: 78
    Temp: 98.6
    Weight: 75 kg
    Height: 170 cm
    """
    
    # Parse the record
    result = parser.parse_medical_record(text_content=sample_record)
    
    # Verify diagnoses were extracted
    print(f"✓ Extracted {len(result['diagnoses'])} diagnoses")
    assert len(result['diagnoses']) > 0, "Should extract at least one diagnosis"
    print(f"  Diagnoses: {[d['condition'] for d in result['diagnoses']]}")
    
    # Verify medications were extracted
    print(f"✓ Extracted {len(result['medications'])} medications")
    assert len(result['medications']) > 0, "Should extract at least one medication"
    print(f"  Medications: {[m['name'] for m in result['medications']]}")
    
    # Verify tests were extracted
    print(f"✓ Extracted {len(result['tests'])} tests")
    assert len(result['tests']) > 0, "Should extract at least one test"
    print(f"  Tests: {[t['test_name'] for t in result['tests']]}")
    
    # Verify allergies were extracted
    print(f"✓ Extracted {len(result['allergies'])} allergies")
    assert len(result['allergies']) > 0, "Should extract at least one allergy"
    print(f"  Allergies: {result['allergies']}")
    
    # Verify vital signs were extracted
    print(f"✓ Extracted {len(result['vital_signs'])} vital signs")
    assert len(result['vital_signs']) > 0, "Should extract at least one vital sign"
    print(f"  Vital Signs: {result['vital_signs']}")
    
    # Verify procedures were extracted
    print(f"✓ Extracted {len(result['procedures'])} procedures")
    print(f"  Procedures: {[p['procedure'] for p in result['procedures']]}")
    
    print("\n✅ All basic parsing tests passed!")


def test_empty_record_handling():
    """Test handling of empty or malformed records."""
    parser = MedicalRecordParser()
    
    # Test with empty content
    result = parser.parse_medical_record(text_content="")
    assert result is not None, "Should return empty structure for empty content"
    assert len(result['diagnoses']) == 0, "Empty record should have no diagnoses"
    print("✓ Empty record handled correctly")
    
    # Test with very short content
    result = parser.parse_medical_record(text_content="Test")
    assert result is not None, "Should return empty structure for short content"
    print("✓ Short content handled correctly")
    
    # Test with malformed content
    result = parser.parse_medical_record(text_content="Random text without medical information")
    assert result is not None, "Should return structure for malformed content"
    print("✓ Malformed content handled correctly")
    
    print("\n✅ All error handling tests passed!")


def test_medical_summarizer():
    """Test MedicalSummarizer service."""
    summarizer = MedicalSummarizer()
    
    sample_records = [
        """
        Diagnosis: Pneumonia
        Medications: Amoxicillin 500mg three times daily
        """,
        """
        Diagnosis: Asthma
        Medications: Albuterol inhaler as needed
        Allergies: None
        """
    ]
    
    # Parse multiple records
    results = summarizer.parse_records(text_contents=sample_records)
    
    assert len(results) == 2, "Should parse both records"
    print(f"✓ Parsed {len(results)} records")
    
    # Verify first record
    assert len(results[0]['diagnoses']) > 0, "First record should have diagnoses"
    assert len(results[0]['medications']) > 0, "First record should have medications"
    print(f"  Record 1: {len(results[0]['diagnoses'])} diagnoses, {len(results[0]['medications'])} medications")
    
    # Verify second record
    assert len(results[1]['diagnoses']) > 0, "Second record should have diagnoses"
    assert len(results[1]['medications']) > 0, "Second record should have medications"
    print(f"  Record 2: {len(results[1]['diagnoses'])} diagnoses, {len(results[1]['medications'])} medications")
    
    print("\n✅ All MedicalSummarizer tests passed!")


def test_date_normalization():
    """Test date normalization functionality."""
    parser = MedicalRecordParser()
    
    # Test various date formats
    test_dates = [
        ("15/03/2023", "2023-03-15"),
        ("15-03-2023", "2023-03-15"),
        ("2023/03/15", "2023-03-15"),
        ("2023-03-15", "2023-03-15"),
        ("15/03/23", "2023-03-15"),
    ]
    
    for input_date, expected_output in test_dates:
        result = parser._normalize_date(input_date)
        assert result == expected_output, f"Date {input_date} should normalize to {expected_output}, got {result}"
        print(f"✓ {input_date} → {result}")
    
    # Test invalid date
    result = parser._normalize_date("invalid")
    assert result is None, "Invalid date should return None"
    print("✓ Invalid date handled correctly")
    
    print("\n✅ All date normalization tests passed!")


def test_incomplete_records():
    """Test handling of incomplete medical records."""
    parser = MedicalRecordParser()
    
    # Record with only diagnoses
    record1 = "Diagnosis: Diabetes"
    result1 = parser.parse_medical_record(text_content=record1)
    assert len(result1['diagnoses']) > 0, "Should extract diagnosis"
    assert len(result1['medications']) == 0, "Should have no medications"
    print("✓ Record with only diagnosis handled correctly")
    
    # Record with only medications
    record2 = "Medications: Aspirin 75mg daily"
    result2 = parser.parse_medical_record(text_content=record2)
    assert len(result2['medications']) > 0, "Should extract medication"
    print("✓ Record with only medications handled correctly")
    
    # Record with only tests
    record3 = "Lab Results: Hemoglobin: 12.5 g/dL"
    result3 = parser.parse_medical_record(text_content=record3)
    assert len(result3['tests']) > 0, "Should extract test"
    print("✓ Record with only tests handled correctly")
    
    print("\n✅ All incomplete record tests passed!")


if __name__ == "__main__":
    print("Testing Medical Record Parser Implementation\n")
    print("=" * 60)
    
    try:
        test_medical_record_parser_basic()
        print("\n" + "=" * 60)
        
        test_empty_record_handling()
        print("\n" + "=" * 60)
        
        test_medical_summarizer()
        print("\n" + "=" * 60)
        
        test_date_normalization()
        print("\n" + "=" * 60)
        
        test_incomplete_records()
        print("\n" + "=" * 60)
        
        print("\n🎉 ALL TESTS PASSED! Medical record parser is working correctly.")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
