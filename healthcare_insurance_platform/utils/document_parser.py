"""Document parsing utilities for policy documents."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import date

from healthcare_insurance_platform.core.logging import get_logger

logger = get_logger(__name__)


class DocumentParser:
    """Base class for document parsers."""
    
    def parse(self, file_path: Path) -> str:
        """
        Parse document and extract text content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file does not exist
        """
        raise NotImplementedError("Subclasses must implement parse method")


class TextFileParser(DocumentParser):
    """Parser for plain text files."""
    
    def parse(self, file_path: Path) -> str:
        """
        Parse text file and extract content.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Text content
            
        Raises:
            FileNotFoundError: If file does not exist
            UnicodeDecodeError: If file encoding is not supported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Successfully parsed text file: {file_path}")
            return content
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                logger.warning(f"Parsed text file with latin-1 encoding: {file_path}")
                return content
            except Exception as e:
                logger.error(f"Failed to parse text file: {file_path}", error=str(e))
                raise


class PDFParser(DocumentParser):
    """Parser for PDF files."""
    
    def __init__(self):
        """Initialize PDF parser."""
        try:
            import PyPDF2
            self.PyPDF2 = PyPDF2
        except ImportError:
            raise ImportError(
                "PyPDF2 is required for PDF parsing. "
                "Install it with: pip install PyPDF2"
            )
    
    def parse(self, file_path: Path) -> str:
        """
        Parse PDF file and extract text content.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If PDF is corrupted or cannot be read
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = self.PyPDF2.PdfReader(f)
                
                if len(pdf_reader.pages) == 0:
                    raise ValueError("PDF file has no pages")
                
                text_content = []
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                    except Exception as e:
                        logger.warning(
                            f"Failed to extract text from page {page_num + 1}: {str(e)}"
                        )
                
                if not text_content:
                    raise ValueError("No text content could be extracted from PDF")
                
                full_text = "\n\n".join(text_content)
                logger.info(
                    f"Successfully parsed PDF file: {file_path} "
                    f"({len(pdf_reader.pages)} pages)"
                )
                return full_text
                
        except Exception as e:
            logger.error(f"Failed to parse PDF file: {file_path}", error=str(e))
            raise ValueError(f"Failed to parse PDF: {str(e)}")


class PolicyInformationExtractor:
    """Extract key policy information from document text."""
    
    @staticmethod
    def extract_coverage_amount(text: str) -> Optional[float]:
        """
        Extract coverage amount from policy text.
        
        Args:
            text: Policy document text
            
        Returns:
            Coverage amount in rupees, or None if not found
        """
        # Look for patterns like "Sum Insured: Rs. 5,00,000" or "Coverage: ₹500000"
        patterns = [
            r'sum\s+insured[:\s]+(?:rs\.?|₹)\s*([\d,]+)',
            r'coverage[:\s]+(?:rs\.?|₹)\s*([\d,]+)',
            r'insured\s+amount[:\s]+(?:rs\.?|₹)\s*([\d,]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def extract_premium(text: str) -> Optional[float]:
        """
        Extract premium amount from policy text.
        
        Args:
            text: Policy document text
            
        Returns:
            Premium amount in rupees, or None if not found
        """
        # Look for patterns like "Premium: Rs. 15,000" or "Annual Premium: ₹15000"
        patterns = [
            r'(?:annual\s+)?premium[:\s]+(?:rs\.?|₹)\s*([\d,]+)',
            r'premium\s+amount[:\s]+(?:rs\.?|₹)\s*([\d,]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def extract_waiting_periods(text: str) -> Dict[str, int]:
        """
        Extract waiting period information from policy text.
        
        Args:
            text: Policy document text
            
        Returns:
            Dictionary with waiting period information
        """
        waiting_periods = {
            'general': 30,  # Default
            'pre_existing': 730,  # Default 2 years
        }
        
        # Look for general waiting period
        general_pattern = r'(?:initial|general)\s+waiting\s+period[:\s]+(\d+)\s+days'
        match = re.search(general_pattern, text, re.IGNORECASE)
        if match:
            waiting_periods['general'] = int(match.group(1))
        
        # Look for pre-existing disease waiting period
        ped_patterns = [
            r'pre[-\s]existing\s+(?:disease|condition)s?\s+waiting\s+period[:\s]+(\d+)\s+(?:days|months|years)',
            r'ped\s+waiting\s+period[:\s]+(\d+)\s+(?:days|months|years)',
        ]
        
        for pattern in ped_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                # Check if it's in months or years
                if 'month' in match.group(0).lower():
                    value *= 30
                elif 'year' in match.group(0).lower():
                    value *= 365
                waiting_periods['pre_existing'] = value
                break
        
        return waiting_periods
    
    @staticmethod
    def extract_exclusions(text: str) -> List[str]:
        """
        Extract exclusions from policy text.
        
        Args:
            text: Policy document text
            
        Returns:
            List of exclusions
        """
        exclusions = []
        
        # Find exclusions section
        exclusion_section_pattern = r'(?:exclusions?|not\s+covered)[:\s]+(.*?)(?=\n\n|\Z)'
        match = re.search(exclusion_section_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            section_text = match.group(1)
            # Split by bullet points or numbered lists
            items = re.split(r'[\n•\-\*]\s*', section_text)
            for item in items:
                item = item.strip()
                if item and len(item) > 10:  # Filter out very short items
                    exclusions.append(item)
        
        # If no structured section found, look for common exclusions
        if not exclusions:
            common_exclusions = [
                'cosmetic surgery', 'dental treatment', 'infertility',
                'war injuries', 'self-inflicted injuries', 'substance abuse'
            ]
            for exclusion in common_exclusions:
                if exclusion in text.lower():
                    exclusions.append(exclusion.title())
        
        return exclusions[:20]  # Limit to 20 exclusions
    
    @staticmethod
    def extract_inclusions(text: str) -> List[str]:
        """
        Extract inclusions/coverage from policy text.
        
        Args:
            text: Policy document text
            
        Returns:
            List of inclusions
        """
        inclusions = []
        
        # Find coverage/inclusions section
        inclusion_patterns = [
            r'(?:coverage|inclusions?|benefits?|covered\s+services)[:\s]+(.*?)(?=\n\n|\Z)',
            r'what\s+is\s+covered[:\s]+(.*?)(?=\n\n|\Z)',
        ]
        
        for pattern in inclusion_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                section_text = match.group(1)
                # Split by bullet points or numbered lists
                items = re.split(r'[\n•\-\*]\s*', section_text)
                for item in items:
                    item = item.strip()
                    if item and len(item) > 10:
                        inclusions.append(item)
                break
        
        # If no structured section found, look for common inclusions
        if not inclusions:
            common_inclusions = [
                'hospitalization', 'surgery', 'diagnostic tests',
                'ambulance charges', 'room rent', 'ICU charges'
            ]
            for inclusion in common_inclusions:
                if inclusion in text.lower():
                    inclusions.append(inclusion.title())
        
        return inclusions[:20]  # Limit to 20 inclusions


def get_parser(file_path: Path) -> DocumentParser:
    """
    Get appropriate parser for the file type.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        DocumentParser instance for the file type
        
    Raises:
        ValueError: If file format is not supported
    """
    suffix = file_path.suffix.lower()
    
    if suffix == '.txt':
        return TextFileParser()
    elif suffix == '.pdf':
        return PDFParser()
    else:
        raise ValueError(
            f"Unsupported file format: {suffix}. "
            f"Supported formats: .txt, .pdf"
        )
