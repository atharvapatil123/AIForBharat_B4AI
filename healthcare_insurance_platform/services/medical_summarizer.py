"""Medical Summarizer service for parsing and summarizing medical records."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime, timezone

from healthcare_insurance_platform.core.logging import get_logger
from healthcare_insurance_platform.models.results import (
    MedicalSummary,
    TimelineEvent,
    CurrentCondition,
    CurrentMedication,
    AbnormalFinding,
)
from healthcare_insurance_platform.utils.document_parser import get_parser

logger = get_logger(__name__)


class MedicalRecordParser:
    """
    Parser for medical records that extracts structured information.
    
    Handles various medical record formats and extracts:
    - Diagnoses
    - Medications
    - Tests and procedures
    - Abnormal findings
    
    Validates: Requirements 8.1
    """
    
    def __init__(self):
        """Initialize the medical record parser."""
        self.logger = logger
    
    def parse_medical_record(
        self,
        file_path: Optional[Union[str, Path]] = None,
        text_content: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Parse medical record from file or text content.
        
        Args:
            file_path: Path to medical record file (PDF or text)
            text_content: Raw text content of medical record
            
        Returns:
            Dictionary containing extracted medical information:
            - diagnoses: List of diagnoses with dates
            - medications: List of medications with details
            - tests: List of tests/procedures with results
            - procedures: List of procedures performed
            - allergies: List of allergies
            - vital_signs: Dictionary of vital signs
            
        Raises:
            ValueError: If neither file_path nor text_content is provided
            FileNotFoundError: If file_path does not exist
        """
        if file_path is None and text_content is None:
            raise ValueError("Either file_path or text_content must be provided")
        
        # Extract text content from file if needed
        if text_content is None:
            file_path = Path(file_path)
            try:
                parser = get_parser(file_path)
                text_content = parser.parse(file_path)
                self.logger.info(f"Successfully parsed medical record file: {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to parse medical record file: {file_path}", error=str(e))
                raise
        
        # Handle empty or very short content
        if not text_content or len(text_content.strip()) < 10:
            self.logger.warning("Medical record content is empty or too short")
            return self._empty_record()
        
        # Extract structured information
        try:
            extracted_data = {
                'diagnoses': self._extract_diagnoses(text_content),
                'medications': self._extract_medications(text_content),
                'tests': self._extract_tests(text_content),
                'procedures': self._extract_procedures(text_content),
                'allergies': self._extract_allergies(text_content),
                'vital_signs': self._extract_vital_signs(text_content),
            }
            
            self.logger.info(
                f"Successfully extracted medical information: "
                f"{len(extracted_data['diagnoses'])} diagnoses, "
                f"{len(extracted_data['medications'])} medications, "
                f"{len(extracted_data['tests'])} tests"
            )
            
            return extracted_data
            
        except Exception as e:
            self.logger.error("Error extracting medical information", error=str(e))
            # Return partial data rather than failing completely
            return self._empty_record()
    
    def _empty_record(self) -> Dict[str, any]:
        """Return empty record structure."""
        return {
            'diagnoses': [],
            'medications': [],
            'tests': [],
            'procedures': [],
            'allergies': [],
            'vital_signs': {},
        }
    
    def _extract_diagnoses(self, text: str) -> List[Dict[str, str]]:
        """
        Extract diagnoses from medical record text.
        
        Args:
            text: Medical record text
            
        Returns:
            List of diagnoses with dates and descriptions
        """
        diagnoses = []
        
        # Look for diagnosis section
        diagnosis_patterns = [
            r'(?:diagnosis|diagnosed with|impression)[:\s]+(.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'(?:primary|secondary)\s+diagnosis[:\s]+(.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'ICD[-\s]?\d+[:\s]+(.*?)(?=\n|\Z)',
        ]
        
        for pattern in diagnosis_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                diagnosis_text = match.group(1).strip()
                
                # Try to extract date
                date_match = re.search(
                    r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})',
                    diagnosis_text
                )
                date_str = date_match.group(1) if date_match else None
                
                # Clean up diagnosis text
                diagnosis_text = re.sub(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', '', diagnosis_text)
                diagnosis_text = diagnosis_text.strip('.,;: \n')
                
                if diagnosis_text and len(diagnosis_text) > 3:
                    diagnoses.append({
                        'condition': diagnosis_text[:200],  # Limit length
                        'date': self._normalize_date(date_str) if date_str else None,
                        'type': 'diagnosis'
                    })
        
        # Look for common disease names if no structured diagnoses found
        if not diagnoses:
            common_conditions = [
                'diabetes', 'hypertension', 'asthma', 'copd', 'pneumonia',
                'bronchitis', 'arthritis', 'cancer', 'heart disease', 'stroke',
                'kidney disease', 'liver disease', 'thyroid', 'anemia'
            ]
            
            for condition in common_conditions:
                pattern = rf'\b{condition}\b'
                if re.search(pattern, text, re.IGNORECASE):
                    diagnoses.append({
                        'condition': condition.title(),
                        'date': None,
                        'type': 'diagnosis'
                    })
        
        return diagnoses[:20]  # Limit to 20 diagnoses
    
    def _extract_medications(self, text: str) -> List[Dict[str, str]]:
        """
        Extract medications from medical record text.
        
        Args:
            text: Medical record text
            
        Returns:
            List of medications with dosage and frequency
        """
        medications = []
        
        # Look for medication section - more flexible pattern
        med_patterns = [
            r'(?:medications?|prescriptions?|drugs?)[:\s]+(.*?)(?=\n\n[A-Z]|[A-Z][a-z]+:[^\n]|\Z)',
            r'(?:current|active)\s+medications?[:\s]+(.*?)(?=\n\n[A-Z]|[A-Z][a-z]+:[^\n]|\Z)',
            r'Rx[:\s]+(.*?)(?=\n\n[A-Z]|[A-Z][a-z]+:[^\n]|\Z)',
        ]
        
        for pattern in med_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                med_section = match.group(1)
                
                # Split by lines or bullet points
                lines = re.split(r'[\n•\-\*]\s*', med_section)
                
                for line in lines:
                    line = line.strip()
                    if not line or len(line) < 3:
                        continue
                    
                    # Try to extract medication name and dosage
                    # Pattern: "Medication Name 500mg twice daily"
                    med_match = re.match(
                        r'([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(\d+\s*(?:mg|mcg|g|ml|units?))\s*(.*)',
                        line
                    )
                    
                    if med_match:
                        name = med_match.group(1).strip()
                        dosage = med_match.group(2).strip()
                        frequency = med_match.group(3).strip() if med_match.group(3) else 'As directed'
                        
                        if len(name) > 2:
                            medications.append({
                                'name': name[:100],
                                'dosage': dosage[:50],
                                'frequency': frequency[:100] if frequency else 'As directed',
                            })
                    else:
                        # Try simpler pattern without dosage
                        simple_match = re.match(r'([A-Za-z]+(?:\s+[A-Za-z]+)?)', line)
                        if simple_match and len(simple_match.group(1)) > 2:
                            name = simple_match.group(1).strip()
                            medications.append({
                                'name': name[:100],
                                'dosage': 'Not specified',
                                'frequency': 'As directed',
                            })
        
        return medications[:30]  # Limit to 30 medications
    
    def _extract_tests(self, text: str) -> List[Dict[str, str]]:
        """
        Extract tests and lab results from medical record text.
        
        Args:
            text: Medical record text
            
        Returns:
            List of tests with results
        """
        tests = []
        
        # Look for lab results section
        test_patterns = [
            r'(?:lab(?:oratory)?\s+results?|test\s+results?)[:\s]+(.*?)(?=\n\n|\n[A-Z][a-z]+:|\Z)',
            r'(?:investigations?|diagnostics?)[:\s]+(.*?)(?=\n\n|\n[A-Z][a-z]+:|\Z)',
        ]
        
        for pattern in test_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                test_section = match.group(1)
                
                # Look for test name and value patterns
                # Pattern: "Test Name: Value" or "Test Name - Value"
                test_lines = re.finditer(
                    r'([A-Za-z\s]+?)[:\-]\s*([0-9.]+\s*[A-Za-z/%]*)',
                    test_section
                )
                
                for test_match in test_lines:
                    test_name = test_match.group(1).strip()
                    test_value = test_match.group(2).strip()
                    
                    if len(test_name) > 2:
                        tests.append({
                            'test_name': test_name[:100],
                            'result': test_value[:50],
                            'date': None,
                        })
        
        # Look for common test names
        if not tests:
            common_tests = [
                'CBC', 'hemoglobin', 'blood sugar', 'glucose', 'cholesterol',
                'creatinine', 'urea', 'liver function', 'thyroid', 'HbA1c',
                'X-ray', 'CT scan', 'MRI', 'ultrasound', 'ECG', 'EKG'
            ]
            
            for test in common_tests:
                pattern = rf'\b{test}\b'
                if re.search(pattern, text, re.IGNORECASE):
                    tests.append({
                        'test_name': test.upper() if len(test) <= 4 else test.title(),
                        'result': 'Performed',
                        'date': None,
                    })
        
        return tests[:30]  # Limit to 30 tests
    
    def _extract_procedures(self, text: str) -> List[Dict[str, str]]:
        """
        Extract procedures from medical record text.
        
        Args:
            text: Medical record text
            
        Returns:
            List of procedures performed
        """
        procedures = []
        
        # Look for procedure section
        proc_patterns = [
            r'(?:procedures?|surgery|surgeries|operations?)[:\s]+(.*?)(?=\n\n|\n[A-Z][a-z]+:|\Z)',
            r'(?:treatment|intervention)s?\s+performed[:\s]+(.*?)(?=\n\n|\n[A-Z][a-z]+:|\Z)',
        ]
        
        for pattern in proc_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                proc_section = match.group(1)
                
                # Split by lines or bullet points
                lines = re.split(r'[\n•\-\*]\s*', proc_section)
                
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 5:
                        # Try to extract date
                        date_match = re.search(
                            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})',
                            line
                        )
                        date_str = date_match.group(1) if date_match else None
                        
                        # Clean up procedure text
                        proc_text = re.sub(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', '', line)
                        proc_text = proc_text.strip('.,;: \n')
                        
                        if proc_text:
                            procedures.append({
                                'procedure': proc_text[:200],
                                'date': self._normalize_date(date_str) if date_str else None,
                            })
        
        return procedures[:20]  # Limit to 20 procedures
    
    def _extract_allergies(self, text: str) -> List[str]:
        """
        Extract allergies from medical record text.
        
        Args:
            text: Medical record text
            
        Returns:
            List of allergies
        """
        allergies = []
        
        # Look for allergy section
        allergy_patterns = [
            r'(?:allergies|allergic\s+to)[:\s]+(.*?)(?=\n\n|\n[A-Z][a-z]+:|\Z)',
            r'known\s+allergies[:\s]+(.*?)(?=\n\n|\n[A-Z][a-z]+:|\Z)',
        ]
        
        for pattern in allergy_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                allergy_section = match.group(1).strip()
                
                # Check for "None" or "NKDA"
                if re.search(r'\b(?:none|nil|nkda|no\s+known)\b', allergy_section, re.IGNORECASE):
                    continue
                
                # Split by commas or bullet points
                items = re.split(r'[,\n•\-\*]\s*', allergy_section)
                
                for item in items:
                    item = item.strip('.,;: \n')
                    if item and len(item) > 2 and len(item) < 100:
                        allergies.append(item)
        
        return allergies[:20]  # Limit to 20 allergies
    
    def _extract_vital_signs(self, text: str) -> Dict[str, str]:
        """
        Extract vital signs from medical record text.
        
        Args:
            text: Medical record text
            
        Returns:
            Dictionary of vital signs
        """
        vital_signs = {}
        
        # Blood pressure
        bp_match = re.search(r'(?:BP|blood\s+pressure)[:\s]*(\d{2,3})/(\d{2,3})', text, re.IGNORECASE)
        if bp_match:
            vital_signs['blood_pressure'] = f"{bp_match.group(1)}/{bp_match.group(2)}"
        
        # Heart rate / Pulse
        hr_match = re.search(r'(?:HR|heart\s+rate|pulse)[:\s]*(\d{2,3})', text, re.IGNORECASE)
        if hr_match:
            vital_signs['heart_rate'] = hr_match.group(1)
        
        # Temperature
        temp_match = re.search(r'(?:temp|temperature)[:\s]*(\d{2,3}(?:\.\d)?)', text, re.IGNORECASE)
        if temp_match:
            vital_signs['temperature'] = temp_match.group(1)
        
        # Respiratory rate
        rr_match = re.search(r'(?:RR|respiratory\s+rate)[:\s]*(\d{1,2})', text, re.IGNORECASE)
        if rr_match:
            vital_signs['respiratory_rate'] = rr_match.group(1)
        
        # Oxygen saturation
        o2_match = re.search(r'(?:O2|oxygen\s+saturation|SpO2)[:\s]*(\d{2,3})%?', text, re.IGNORECASE)
        if o2_match:
            vital_signs['oxygen_saturation'] = f"{o2_match.group(1)}%"
        
        # Weight
        weight_match = re.search(r'(?:weight)[:\s]*(\d{2,3}(?:\.\d)?)\s*(?:kg|kgs)?', text, re.IGNORECASE)
        if weight_match:
            vital_signs['weight'] = f"{weight_match.group(1)} kg"
        
        # Height
        height_match = re.search(r'(?:height)[:\s]*(\d{2,3}(?:\.\d)?)\s*(?:cm)?', text, re.IGNORECASE)
        if height_match:
            vital_signs['height'] = f"{height_match.group(1)} cm"
        
        return vital_signs
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """
        Normalize date string to ISO format.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            ISO format date string (YYYY-MM-DD) or None if parsing fails
        """
        if not date_str:
            return None
        
        # Try common date formats
        date_formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
            '%m/%d/%Y', '%m-%d-%Y', '%m.%d.%Y',
            '%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d',
            '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None


class MedicalSummarizer:
    """
    Service for summarizing patient medical history.
    
    Validates: Requirements 8.1, 8.2, 8.3, 8.4
    """
    
    def __init__(self):
        """Initialize the medical summarizer."""
        self.parser = MedicalRecordParser()
        self.logger = logger
    
    def parse_records(
        self,
        file_paths: Optional[List[Union[str, Path]]] = None,
        text_contents: Optional[List[str]] = None
    ) -> List[Dict[str, any]]:
        """
        Parse multiple medical records.
        
        Args:
            file_paths: List of paths to medical record files
            text_contents: List of raw text contents
            
        Returns:
            List of parsed medical record data
        """
        parsed_records = []
        
        if file_paths:
            for file_path in file_paths:
                try:
                    record_data = self.parser.parse_medical_record(file_path=file_path)
                    parsed_records.append(record_data)
                except Exception as e:
                    self.logger.error(f"Failed to parse record {file_path}", error=str(e))
                    # Continue with other records
        
        if text_contents:
            for text_content in text_contents:
                try:
                    record_data = self.parser.parse_medical_record(text_content=text_content)
                    parsed_records.append(record_data)
                except Exception as e:
                    self.logger.error("Failed to parse text content", error=str(e))
                    # Continue with other records
        
        return parsed_records
    
    def generate_timeline(self, parsed_records: List[Dict[str, any]]) -> List[TimelineEvent]:
        """
        Generate chronological timeline of medical events.
        
        Organizes events chronologically, identifies and highlights key events,
        and tracks condition status over time.
        
        Args:
            parsed_records: List of parsed medical record data
            
        Returns:
            List of TimelineEvent objects sorted chronologically
            
        Validates: Requirements 8.2
        """
        timeline_events = []
        
        for record in parsed_records:
            # Add diagnosis events
            for diagnosis in record.get('diagnoses', []):
                if diagnosis.get('condition'):
                    # Determine significance based on condition severity
                    significance = self._determine_significance(
                        diagnosis['condition'],
                        event_type='diagnosis'
                    )
                    
                    timeline_events.append(TimelineEvent(
                        date=diagnosis.get('date') or datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                        event_type='diagnosis',
                        description=f"Diagnosed with {diagnosis['condition']}",
                        significance=significance
                    ))
            
            # Add procedure events
            for procedure in record.get('procedures', []):
                if procedure.get('procedure'):
                    timeline_events.append(TimelineEvent(
                        date=procedure.get('date') or datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                        event_type='procedure',
                        description=procedure['procedure'],
                        significance='important'  # Procedures are generally important
                    ))
            
            # Add test events
            for test in record.get('tests', []):
                if test.get('test_name'):
                    # Determine if test result is abnormal
                    is_abnormal = self._is_abnormal_result(test)
                    significance = 'important' if is_abnormal else 'routine'
                    
                    description = f"{test['test_name']}: {test.get('result', 'Performed')}"
                    
                    timeline_events.append(TimelineEvent(
                        date=test.get('date') or datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                        event_type='test',
                        description=description,
                        significance=significance
                    ))
            
            # Add medication change events
            for medication in record.get('medications', []):
                if medication.get('name'):
                    timeline_events.append(TimelineEvent(
                        date=datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                        event_type='medication_change',
                        description=f"Started {medication['name']} {medication.get('dosage', '')}",
                        significance='routine'
                    ))
        
        # Sort events chronologically (most recent first)
        timeline_events.sort(key=lambda e: e.date, reverse=True)
        
        self.logger.info(f"Generated timeline with {len(timeline_events)} events")
        
        return timeline_events
    
    def detect_abnormal_results(self, parsed_records: List[Dict[str, any]]) -> List[AbnormalFinding]:
        """
        Identify abnormal test results and track trends over time.
        
        Identifies abnormal test results, tracks trends over time,
        and highlights significant changes.
        
        Args:
            parsed_records: List of parsed medical record data
            
        Returns:
            List of AbnormalFinding objects
            
        Validates: Requirements 8.3
        """
        abnormal_findings = []
        test_history = {}  # Track test results over time for trend analysis
        
        for record in parsed_records:
            for test in record.get('tests', []):
                test_name = test.get('test_name')
                result = test.get('result')
                test_date = test.get('date') or datetime.now(timezone.utc).strftime('%Y-%m-%d')
                
                if not test_name or not result:
                    continue
                
                # Check if result is abnormal
                if self._is_abnormal_result(test):
                    # Track test history for trend analysis
                    if test_name not in test_history:
                        test_history[test_name] = []
                    test_history[test_name].append({
                        'date': test_date,
                        'result': result
                    })
                    
                    # Determine trend
                    trend = self._determine_trend(test_name, test_history[test_name])
                    
                    # Create finding description
                    finding_desc = self._describe_abnormal_finding(test_name, result)
                    
                    abnormal_findings.append(AbnormalFinding(
                        test_type=test_name,
                        date=test_date,
                        finding=finding_desc,
                        trend=trend
                    ))
        
        self.logger.info(f"Detected {len(abnormal_findings)} abnormal findings")
        
        return abnormal_findings
    
    def generate_summary(
        self,
        patient_id: str,
        parsed_records: List[Dict[str, any]],
        language: str = 'en'
    ) -> MedicalSummary:
        """
        Generate concise medical summary for clinical decision-making.
        
        Generates concise medical summaries, extracts current conditions,
        medications, and allergies, and formats for clinical decision-making.
        
        Args:
            patient_id: Patient identifier
            parsed_records: List of parsed medical record data
            language: Language code for output (default: 'en')
            
        Returns:
            MedicalSummary object with complete patient history summary
            
        Validates: Requirements 8.1, 8.4
        """
        # Generate timeline
        timeline_events = self.generate_timeline(parsed_records)
        
        # Detect abnormal findings
        abnormal_findings = self.detect_abnormal_results(parsed_records)
        
        # Extract current conditions
        current_conditions = self._extract_current_conditions(parsed_records)
        
        # Extract current medications
        current_medications = self._extract_current_medications(parsed_records)
        
        # Extract allergies
        all_allergies = []
        for record in parsed_records:
            all_allergies.extend(record.get('allergies', []))
        # Remove duplicates
        allergies = list(set(all_allergies))
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(parsed_records, current_conditions)
        
        # Generate narrative summary
        summary_text = self._generate_summary_text(
            current_conditions,
            current_medications,
            allergies,
            timeline_events,
            abnormal_findings
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            current_conditions,
            abnormal_findings,
            risk_factors
        )
        
        # Generate citations
        citations = [f"Medical record {i+1}" for i in range(len(parsed_records))]
        
        # Create summary
        summary = MedicalSummary(
            summary_id=f"summary_{patient_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            patient_id=patient_id,
            timeline_events=timeline_events,
            current_conditions=current_conditions,
            current_medications=current_medications,
            allergies=allergies,
            abnormal_findings=abnormal_findings,
            risk_factors=risk_factors,
            summary_text=summary_text,
            explanation=explanation,
            citations=citations,
            language=language
        )
        
        self.logger.info(f"Generated medical summary for patient {patient_id}")
        
        return summary
    
    def _determine_significance(self, condition: str, event_type: str) -> str:
        """
        Determine significance level of a medical event.
        
        Args:
            condition: Condition or event description
            event_type: Type of event
            
        Returns:
            Significance level: critical, important, or routine
        """
        # Critical conditions
        critical_keywords = [
            'cancer', 'stroke', 'heart attack', 'myocardial infarction',
            'cardiac arrest', 'sepsis', 'respiratory failure', 'renal failure',
            'liver failure', 'coma', 'hemorrhage', 'embolism', 'aneurysm'
        ]
        
        condition_lower = condition.lower()
        
        for keyword in critical_keywords:
            if keyword in condition_lower:
                return 'critical'
        
        # Important conditions
        important_keywords = [
            'diabetes', 'hypertension', 'copd', 'asthma', 'pneumonia',
            'heart disease', 'kidney disease', 'liver disease', 'arthritis',
            'fracture', 'surgery', 'operation'
        ]
        
        for keyword in important_keywords:
            if keyword in condition_lower:
                return 'important'
        
        return 'routine'
    
    def _is_abnormal_result(self, test: Dict[str, str]) -> bool:
        """
        Check if a test result is abnormal.
        
        Args:
            test: Test data with test_name and result
            
        Returns:
            True if result appears abnormal
        """
        result = test.get('result', '').lower()
        test_name = test.get('test_name', '').lower()
        
        # Check for explicit abnormal indicators
        abnormal_indicators = ['abnormal', 'high', 'low', 'elevated', 'decreased', 'positive']
        
        for indicator in abnormal_indicators:
            if indicator in result:
                return True
        
        # Check for specific test ranges (simplified)
        try:
            # Extract numeric value
            numeric_match = re.search(r'(\d+(?:\.\d+)?)', result)
            if numeric_match:
                value = float(numeric_match.group(1))
                
                # Common test ranges
                if 'hemoglobin' in test_name or 'hb' in test_name:
                    return value < 12 or value > 17
                elif 'glucose' in test_name or 'blood sugar' in test_name:
                    return value < 70 or value > 140
                elif 'cholesterol' in test_name:
                    return value > 200
                elif 'creatinine' in test_name:
                    return value > 1.3
        except (ValueError, AttributeError):
            pass
        
        return False
    
    def _determine_trend(self, test_name: str, test_history: List[Dict]) -> str:
        """
        Determine trend for a test over time.
        
        Args:
            test_name: Name of the test
            test_history: List of test results with dates
            
        Returns:
            Trend: improving, worsening, or stable
        """
        if len(test_history) < 2:
            return 'stable'
        
        # Sort by date
        sorted_history = sorted(test_history, key=lambda x: x['date'])
        
        # Try to extract numeric values for comparison
        try:
            values = []
            for entry in sorted_history[-3:]:  # Look at last 3 results
                numeric_match = re.search(r'(\d+(?:\.\d+)?)', entry['result'])
                if numeric_match:
                    values.append(float(numeric_match.group(1)))
            
            if len(values) >= 2:
                # Check if values are increasing or decreasing
                if values[-1] > values[0] * 1.1:  # 10% increase
                    # For some tests, increase is bad
                    if any(keyword in test_name.lower() for keyword in ['glucose', 'cholesterol', 'creatinine']):
                        return 'worsening'
                    else:
                        return 'improving'
                elif values[-1] < values[0] * 0.9:  # 10% decrease
                    # For some tests, decrease is bad
                    if any(keyword in test_name.lower() for keyword in ['hemoglobin', 'albumin']):
                        return 'worsening'
                    else:
                        return 'improving'
        except (ValueError, AttributeError):
            pass
        
        return 'stable'
    
    def _describe_abnormal_finding(self, test_name: str, result: str) -> str:
        """
        Create a description for an abnormal finding.
        
        Args:
            test_name: Name of the test
            result: Test result
            
        Returns:
            Description of the abnormal finding
        """
        return f"{test_name} result of {result} is outside normal range"
    
    def _extract_current_conditions(self, parsed_records: List[Dict[str, any]]) -> List[CurrentCondition]:
        """
        Extract current medical conditions from parsed records.
        
        Args:
            parsed_records: List of parsed medical record data
            
        Returns:
            List of CurrentCondition objects
        """
        conditions_map = {}  # Use map to deduplicate
        
        for record in parsed_records:
            for diagnosis in record.get('diagnoses', []):
                condition_name = diagnosis.get('condition')
                if not condition_name:
                    continue
                
                # Use condition name as key to avoid duplicates
                if condition_name not in conditions_map:
                    conditions_map[condition_name] = CurrentCondition(
                        condition=condition_name,
                        diagnosis_date=diagnosis.get('date') or datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                        status='active',  # Assume active unless specified
                        treatments=[]
                    )
        
        return list(conditions_map.values())
    
    def _extract_current_medications(self, parsed_records: List[Dict[str, any]]) -> List[CurrentMedication]:
        """
        Extract current medications from parsed records.
        
        Args:
            parsed_records: List of parsed medical record data
            
        Returns:
            List of CurrentMedication objects
        """
        medications_map = {}  # Use map to deduplicate
        
        for record in parsed_records:
            for med in record.get('medications', []):
                med_name = med.get('name')
                if not med_name:
                    continue
                
                # Use medication name as key to avoid duplicates
                if med_name not in medications_map:
                    medications_map[med_name] = CurrentMedication(
                        name=med_name,
                        dosage=med.get('dosage', 'Not specified'),
                        purpose='Treatment',  # Default purpose
                        start_date=datetime.now(timezone.utc).strftime('%Y-%m-%d')
                    )
        
        return list(medications_map.values())
    
    def _identify_risk_factors(
        self,
        parsed_records: List[Dict[str, any]],
        current_conditions: List[CurrentCondition]
    ) -> List[str]:
        """
        Identify risk factors from medical history.
        
        Args:
            parsed_records: List of parsed medical record data
            current_conditions: List of current conditions
            
        Returns:
            List of identified risk factors
        """
        risk_factors = []
        
        # Check for chronic conditions that are risk factors
        risk_condition_keywords = {
            'diabetes': 'Diabetes mellitus',
            'hypertension': 'Hypertension',
            'obesity': 'Obesity',
            'smoking': 'Smoking history',
            'heart disease': 'Cardiovascular disease',
            'kidney disease': 'Chronic kidney disease',
            'copd': 'Chronic obstructive pulmonary disease'
        }
        
        for condition in current_conditions:
            condition_lower = condition.condition.lower()
            for keyword, risk_factor in risk_condition_keywords.items():
                if keyword in condition_lower and risk_factor not in risk_factors:
                    risk_factors.append(risk_factor)
        
        return risk_factors
    
    def _generate_summary_text(
        self,
        current_conditions: List[CurrentCondition],
        current_medications: List[CurrentMedication],
        allergies: List[str],
        timeline_events: List[TimelineEvent],
        abnormal_findings: List[AbnormalFinding]
    ) -> str:
        """
        Generate narrative summary text.
        
        Args:
            current_conditions: List of current conditions
            current_medications: List of current medications
            allergies: List of allergies
            timeline_events: List of timeline events
            abnormal_findings: List of abnormal findings
            
        Returns:
            Narrative summary text
        """
        summary_parts = []
        
        # Current conditions
        if current_conditions:
            conditions_text = ', '.join([c.condition for c in current_conditions[:5]])
            summary_parts.append(f"Current conditions: {conditions_text}")
        
        # Current medications
        if current_medications:
            meds_text = ', '.join([m.name for m in current_medications[:5]])
            summary_parts.append(f"Current medications: {meds_text}")
        
        # Allergies
        if allergies:
            allergies_text = ', '.join(allergies[:5])
            summary_parts.append(f"Known allergies: {allergies_text}")
        else:
            summary_parts.append("No known allergies")
        
        # Recent significant events
        critical_events = [e for e in timeline_events if e.significance == 'critical']
        if critical_events:
            summary_parts.append(f"Recent critical events: {len(critical_events)} identified")
        
        # Abnormal findings
        if abnormal_findings:
            summary_parts.append(f"Abnormal findings: {len(abnormal_findings)} test results outside normal range")
        
        return '. '.join(summary_parts) + '.'
    
    def _generate_explanation(
        self,
        current_conditions: List[CurrentCondition],
        abnormal_findings: List[AbnormalFinding],
        risk_factors: List[str]
    ) -> str:
        """
        Generate explanation of key findings and trends.
        
        Args:
            current_conditions: List of current conditions
            abnormal_findings: List of abnormal findings
            risk_factors: List of risk factors
            
        Returns:
            Explanation text
        """
        explanation_parts = []
        
        # Explain conditions
        if current_conditions:
            explanation_parts.append(
                f"Patient has {len(current_conditions)} active medical condition(s) requiring ongoing management"
            )
        
        # Explain abnormal findings
        if abnormal_findings:
            worsening = [f for f in abnormal_findings if f.trend == 'worsening']
            if worsening:
                explanation_parts.append(
                    f"{len(worsening)} test result(s) show worsening trend requiring attention"
                )
        
        # Explain risk factors
        if risk_factors:
            explanation_parts.append(
                f"Identified {len(risk_factors)} risk factor(s) that may impact treatment decisions"
            )
        
        if not explanation_parts:
            explanation_parts.append("No significant concerns identified in current medical history")
        
        return '. '.join(explanation_parts) + '.'
