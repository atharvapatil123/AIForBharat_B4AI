"""
Example usage of the Medical Summarizer service.

This example demonstrates the three main functionalities:
1. Timeline generation (Task 11.2)
2. Abnormal result detection (Task 11.3)
3. Summary generation (Task 11.4)
"""

from healthcare_insurance_platform.services.medical_summarizer import MedicalSummarizer

# Sample medical record with comprehensive patient history
sample_medical_record = """
PATIENT MEDICAL RECORD
======================

Patient ID: P12345
Date: 2024-01-15

CHIEF COMPLAINT:
Follow-up for diabetes management and hypertension control

MEDICAL HISTORY:
Diagnosis: Type 2 Diabetes Mellitus (diagnosed 2020-03-15)
Diagnosis: Essential Hypertension (diagnosed 2019-06-20)
Diagnosis: Hyperlipidemia (diagnosed 2021-01-10)

CURRENT MEDICATIONS:
- Metformin 500mg twice daily (for diabetes)
- Lisinopril 10mg once daily (for hypertension)
- Atorvastatin 20mg once daily (for cholesterol)
- Aspirin 81mg once daily (cardiovascular protection)

ALLERGIES:
Penicillin (causes rash)

LABORATORY RESULTS (2024-01-15):
- Fasting Blood Sugar: 180 mg/dL (High - Normal: 70-100)
- HbA1c: 8.5% (Elevated - Target: <7%)
- Total Cholesterol: 220 mg/dL (High - Normal: <200)
- LDL Cholesterol: 145 mg/dL (High - Normal: <100)
- HDL Cholesterol: 42 mg/dL (Low - Normal: >40)
- Triglycerides: 165 mg/dL (Borderline High - Normal: <150)
- Creatinine: 1.1 mg/dL (Normal: 0.6-1.2)
- Hemoglobin: 11.5 g/dL (Low - Normal: 13-17)
- Blood Pressure: 145/95 mmHg (High - Normal: <120/80)

PREVIOUS LAB RESULTS (2023-10-15):
- Fasting Blood Sugar: 165 mg/dL
- HbA1c: 8.2%
- Cholesterol: 210 mg/dL
- Hemoglobin: 12.0 g/dL

PROCEDURES:
- Cardiac stress test performed on 2024-01-10 (Result: Normal)
- Retinal examination on 2023-12-05 (Result: No diabetic retinopathy)

VITAL SIGNS:
- Blood Pressure: 145/95 mmHg
- Heart Rate: 78 bpm
- Temperature: 98.6°F
- Respiratory Rate: 16/min
- Oxygen Saturation: 98%
- Weight: 85 kg
- Height: 170 cm
- BMI: 29.4 (Overweight)

ASSESSMENT:
1. Type 2 Diabetes - suboptimal control
2. Hypertension - not at goal
3. Hyperlipidemia - improving but not at target
4. Mild anemia - requires monitoring

PLAN:
- Increase Metformin to 1000mg twice daily
- Add Amlodipine 5mg daily for blood pressure control
- Continue current lipid management
- Recheck labs in 3 months
- Dietary counseling and exercise recommendations
"""


def example_timeline_generation():
    """Example: Generate chronological timeline of medical events."""
    print("=" * 70)
    print("EXAMPLE 1: Timeline Generation (Task 11.2)")
    print("=" * 70)
    print("\nGenerating chronological timeline of medical events...")
    
    summarizer = MedicalSummarizer()
    
    # Parse the medical record
    parsed_records = summarizer.parse_records(text_contents=[sample_medical_record])
    
    # Generate timeline
    timeline = summarizer.generate_timeline(parsed_records)
    
    print(f"\n✓ Generated timeline with {len(timeline)} events\n")
    print("CHRONOLOGICAL TIMELINE:")
    print("-" * 70)
    
    # Group events by significance
    critical_events = [e for e in timeline if e.significance == 'critical']
    important_events = [e for e in timeline if e.significance == 'important']
    routine_events = [e for e in timeline if e.significance == 'routine']
    
    if critical_events:
        print("\n🔴 CRITICAL EVENTS:")
        for event in critical_events:
            print(f"  • {event.date}: {event.description}")
    
    if important_events:
        print("\n🟡 IMPORTANT EVENTS:")
        for event in important_events[:5]:  # Show first 5
            print(f"  • {event.date}: {event.description}")
    
    if routine_events:
        print(f"\n🟢 ROUTINE EVENTS: {len(routine_events)} events")
        for event in routine_events[:3]:  # Show first 3
            print(f"  • {event.date}: {event.description}")
    
    print("\n" + "=" * 70)
    return timeline


def example_abnormal_detection():
    """Example: Detect abnormal test results and track trends."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Abnormal Result Detection (Task 11.3)")
    print("=" * 70)
    print("\nDetecting abnormal test results and tracking trends...")
    
    summarizer = MedicalSummarizer()
    
    # Parse the medical record
    parsed_records = summarizer.parse_records(text_contents=[sample_medical_record])
    
    # Detect abnormal results
    abnormal_findings = summarizer.detect_abnormal_results(parsed_records)
    
    print(f"\n✓ Detected {len(abnormal_findings)} abnormal findings\n")
    print("ABNORMAL TEST RESULTS:")
    print("-" * 70)
    
    # Group by trend
    worsening = [f for f in abnormal_findings if f.trend == 'worsening']
    stable = [f for f in abnormal_findings if f.trend == 'stable']
    improving = [f for f in abnormal_findings if f.trend == 'improving']
    
    if worsening:
        print("\n⚠️  WORSENING TRENDS (Requires Attention):")
        for finding in worsening:
            print(f"  • {finding.test_type}")
            print(f"    Finding: {finding.finding}")
            print(f"    Date: {finding.date}")
    
    if stable:
        print("\n📊 STABLE ABNORMAL RESULTS:")
        for finding in stable:
            print(f"  • {finding.test_type}: {finding.finding}")
    
    if improving:
        print("\n✅ IMPROVING TRENDS:")
        for finding in improving:
            print(f"  • {finding.test_type}: {finding.finding}")
    
    print("\n" + "=" * 70)
    return abnormal_findings


def example_summary_generation():
    """Example: Generate comprehensive medical summary."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Medical Summary Generation (Task 11.4)")
    print("=" * 70)
    print("\nGenerating comprehensive medical summary for clinical use...")
    
    summarizer = MedicalSummarizer()
    
    # Parse the medical record
    parsed_records = summarizer.parse_records(text_contents=[sample_medical_record])
    
    # Generate complete summary
    summary = summarizer.generate_summary(
        patient_id="P12345",
        parsed_records=parsed_records,
        language='en'
    )
    
    print(f"\n✓ Generated medical summary\n")
    print("MEDICAL SUMMARY FOR CLINICAL DECISION-MAKING:")
    print("=" * 70)
    
    # Summary metadata
    print(f"\nSummary ID: {summary.summary_id}")
    print(f"Patient ID: {summary.patient_id}")
    print(f"Generated: {summary.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Language: {summary.language.upper()}")
    
    # Executive summary
    print("\n" + "-" * 70)
    print("EXECUTIVE SUMMARY:")
    print("-" * 70)
    print(summary.summary_text)
    
    # Clinical explanation
    print("\n" + "-" * 70)
    print("CLINICAL EXPLANATION:")
    print("-" * 70)
    print(summary.explanation)
    
    # Current conditions
    print("\n" + "-" * 70)
    print(f"CURRENT CONDITIONS ({len(summary.current_conditions)}):")
    print("-" * 70)
    for i, condition in enumerate(summary.current_conditions, 1):
        print(f"{i}. {condition.condition}")
        print(f"   Status: {condition.status.upper()}")
        print(f"   Diagnosed: {condition.diagnosis_date}")
        if condition.treatments:
            print(f"   Treatments: {', '.join(condition.treatments)}")
    
    # Current medications
    print("\n" + "-" * 70)
    print(f"CURRENT MEDICATIONS ({len(summary.current_medications)}):")
    print("-" * 70)
    for i, med in enumerate(summary.current_medications, 1):
        print(f"{i}. {med.name} - {med.dosage}")
        print(f"   Purpose: {med.purpose}")
        print(f"   Started: {med.start_date}")
    
    # Allergies
    print("\n" + "-" * 70)
    print("ALLERGIES:")
    print("-" * 70)
    if summary.allergies:
        for allergy in summary.allergies:
            print(f"  ⚠️  {allergy}")
    else:
        print("  No known allergies")
    
    # Risk factors
    print("\n" + "-" * 70)
    print(f"RISK FACTORS ({len(summary.risk_factors)}):")
    print("-" * 70)
    if summary.risk_factors:
        for risk in summary.risk_factors:
            print(f"  • {risk}")
    else:
        print("  No significant risk factors identified")
    
    # Key timeline events
    print("\n" + "-" * 70)
    print(f"KEY TIMELINE EVENTS (Showing 5 of {len(summary.timeline_events)}):")
    print("-" * 70)
    for event in summary.timeline_events[:5]:
        icon = "🔴" if event.significance == "critical" else "🟡" if event.significance == "important" else "🟢"
        print(f"{icon} {event.date}: {event.description}")
    
    # Abnormal findings
    print("\n" + "-" * 70)
    print(f"ABNORMAL FINDINGS ({len(summary.abnormal_findings)}):")
    print("-" * 70)
    if summary.abnormal_findings:
        for finding in summary.abnormal_findings[:5]:
            trend_icon = "⬆️" if finding.trend == "worsening" else "⬇️" if finding.trend == "improving" else "➡️"
            print(f"{trend_icon} {finding.test_type}: {finding.finding}")
            print(f"   Trend: {finding.trend.upper()}")
    else:
        print("  No abnormal findings")
    
    # Citations
    print("\n" + "-" * 70)
    print("SOURCES:")
    print("-" * 70)
    for i, citation in enumerate(summary.citations, 1):
        print(f"{i}. {citation}")
    
    print("\n" + "=" * 70)
    return summary


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("MEDICAL SUMMARIZER SERVICE - COMPREHENSIVE EXAMPLES")
    print("Demonstrating Tasks 11.2, 11.3, and 11.4")
    print("=" * 70)
    
    try:
        # Example 1: Timeline generation
        timeline = example_timeline_generation()
        
        # Example 2: Abnormal result detection
        abnormal_findings = example_abnormal_detection()
        
        # Example 3: Complete summary generation
        summary = example_summary_generation()
        
        # Final summary
        print("\n" + "=" * 70)
        print("EXAMPLES COMPLETED SUCCESSFULLY ✓")
        print("=" * 70)
        print("\nKey Features Demonstrated:")
        print(f"  ✓ Timeline Generation: {len(timeline)} events organized chronologically")
        print(f"  ✓ Abnormal Detection: {len(abnormal_findings)} abnormal findings identified")
        print(f"  ✓ Summary Generation: Complete clinical summary with all components")
        print("\nThe Medical Summarizer service is ready for clinical use!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Example failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
