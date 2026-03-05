"""
Ombudsman Advisor Service.

This service provides guidance on insurance dispute resolution through
the Insurance Ombudsman, including eligibility checking, deadline calculation,
and complaint filing guidance.

Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid

from healthcare_insurance_platform.db.ombudsman_offices import ombudsman_db
from healthcare_insurance_platform.models.ombudsman import OmbudsmanOffice
from healthcare_insurance_platform.models.results import EligibilityResult, ComplaintGuide


class OmbudsmanAdvisor:
    """
    Service for providing Insurance Ombudsman guidance.
    
    This service helps users understand their options for dispute resolution
    through the Insurance Ombudsman system in India, including eligibility
    checking, deadline calculation, and complaint filing guidance.
    """
    
    # Ombudsman jurisdiction limit in rupees (₹20 lakh)
    JURISDICTION_LIMIT = 2000000.0
    
    # Filing deadline in days from rejection (1 year = 365 days)
    FILING_DEADLINE_DAYS = 365
    
    def __init__(self):
        """Initialize the Ombudsman Advisor service."""
        self.ombudsman_db = ombudsman_db
    
    def check_eligibility(
        self,
        claim_amount: float,
        rejection_date: Optional[str],
        user_location: str,
        claim_id: Optional[str] = None,
        language: str = "en"
    ) -> EligibilityResult:
        """
        Check eligibility for filing complaint with Insurance Ombudsman.
        
        This method validates:
        1. Claim amount is within ₹20 lakh jurisdiction limit
        2. Complaint is within 1-year filing deadline from rejection
        3. Appropriate regional office based on user location
        
        Args:
            claim_amount: Claim amount in rupees
            rejection_date: Date of claim rejection (ISO format YYYY-MM-DD), None if not rejected yet
            user_location: User's location (city or state)
            claim_id: Optional claim identifier
            language: Language for output (default: "en")
        
        Returns:
            EligibilityResult with eligibility determination and guidance
        
        Validates: Requirements 7.2, 7.3, 7.4
        """
        result_id = str(uuid.uuid4())
        
        # Validate jurisdiction (₹20 lakh limit)
        within_jurisdiction = self._check_jurisdiction(claim_amount)
        
        # Calculate deadline and check if within filing period
        deadline_info = self._calculate_deadline(rejection_date)
        within_deadline = deadline_info['within_deadline']
        filing_deadline = deadline_info['filing_deadline']
        days_remaining = deadline_info['days_remaining']
        
        # Determine appropriate regional office
        regional_office = self._get_regional_office(user_location)
        
        # Determine overall eligibility
        is_eligible = within_jurisdiction and within_deadline and regional_office is not None
        
        # Build eligibility reasons
        eligibility_reasons = self._build_eligibility_reasons(
            within_jurisdiction,
            within_deadline,
            regional_office,
            claim_amount,
            days_remaining
        )
        
        # Build explanation
        explanation = self._build_eligibility_explanation(
            is_eligible,
            within_jurisdiction,
            within_deadline,
            regional_office,
            claim_amount,
            days_remaining,
            language
        )
        
        # Build next steps
        next_steps = self._build_next_steps(
            is_eligible,
            within_jurisdiction,
            within_deadline,
            regional_office,
            days_remaining
        )
        
        # Build citations
        citations = [
            "Insurance Ombudsman Rules, 2017",
            "IRDAI (Insurance Ombudsman) Regulations",
            "Ombudsman jurisdiction: Claims up to ₹20 lakh"
        ]
        
        # Convert regional office to dict if available
        regional_office_dict = None
        if regional_office:
            regional_office_dict = {
                'office_id': regional_office.office_id,
                'name': regional_office.name,
                'region': regional_office.region,
                'address': regional_office.address,
                'jurisdiction': regional_office.jurisdiction,
                'contact_phone': regional_office.contact_phone,
                'contact_email': regional_office.contact_email,
                'website': regional_office.website
            }
        
        return EligibilityResult(
            result_id=result_id,
            claim_id=claim_id,
            is_eligible=is_eligible,
            eligibility_reasons=eligibility_reasons,
            claim_amount=claim_amount,
            jurisdiction_limit=self.JURISDICTION_LIMIT,
            within_jurisdiction=within_jurisdiction,
            rejection_date=rejection_date,
            filing_deadline=filing_deadline,
            days_remaining=days_remaining,
            within_deadline=within_deadline,
            user_location=user_location,
            regional_office=regional_office_dict,
            explanation=explanation,
            next_steps=next_steps,
            citations=citations,
            language=language
        )
    
    def _check_jurisdiction(self, claim_amount: float) -> bool:
        """
        Check if claim amount is within Ombudsman jurisdiction.
        
        Args:
            claim_amount: Claim amount in rupees
        
        Returns:
            True if claim amount <= ₹20 lakh, False otherwise
        
        Validates: Requirement 7.2
        """
        return claim_amount <= self.JURISDICTION_LIMIT
    
    def _calculate_deadline(self, rejection_date: Optional[str]) -> dict:
        """
        Calculate filing deadline from rejection date.
        
        Args:
            rejection_date: Date of claim rejection (ISO format YYYY-MM-DD)
        
        Returns:
            Dictionary with filing_deadline, days_remaining, and within_deadline
        
        Validates: Requirement 7.3
        """
        if rejection_date is None:
            # No rejection date provided - assume not yet rejected
            return {
                'filing_deadline': None,
                'days_remaining': None,
                'within_deadline': True  # Not rejected yet, so deadline doesn't apply
            }
        
        try:
            # Parse rejection date
            rejection_dt = datetime.fromisoformat(rejection_date.replace('Z', '+00:00'))
            
            # Calculate filing deadline (1 year from rejection)
            deadline_dt = rejection_dt + timedelta(days=self.FILING_DEADLINE_DAYS)
            
            # Calculate days remaining
            today = datetime.now(rejection_dt.tzinfo) if rejection_dt.tzinfo else datetime.now()
            days_remaining = (deadline_dt - today).days
            
            # Check if within deadline
            within_deadline = days_remaining >= 0
            
            return {
                'filing_deadline': deadline_dt.date().isoformat(),
                'days_remaining': days_remaining,
                'within_deadline': within_deadline
            }
        except (ValueError, AttributeError) as e:
            # Invalid date format - treat as no rejection date
            return {
                'filing_deadline': None,
                'days_remaining': None,
                'within_deadline': True
            }
    
    def _get_regional_office(self, user_location: str) -> Optional[OmbudsmanOffice]:
        """
        Determine appropriate regional Ombudsman office based on location.
        
        Args:
            user_location: User's location (city or state)
        
        Returns:
            OmbudsmanOffice if found, None otherwise
        
        Validates: Requirement 7.4
        """
        return self.ombudsman_db.get_office_by_location(user_location)
    
    def _build_eligibility_reasons(
        self,
        within_jurisdiction: bool,
        within_deadline: bool,
        regional_office: Optional[OmbudsmanOffice],
        claim_amount: float,
        days_remaining: Optional[int]
    ) -> list:
        """Build list of eligibility reasons."""
        reasons = []
        
        # Jurisdiction check
        if within_jurisdiction:
            reasons.append(
                f"Claim amount ₹{claim_amount:,.2f} is within Ombudsman jurisdiction (≤ ₹20 lakh)"
            )
        else:
            reasons.append(
                f"Claim amount ₹{claim_amount:,.2f} exceeds Ombudsman jurisdiction limit of ₹20 lakh"
            )
        
        # Deadline check
        if days_remaining is not None:
            if within_deadline:
                reasons.append(
                    f"Complaint is within filing deadline ({days_remaining} days remaining)"
                )
            else:
                reasons.append(
                    f"Complaint deadline has passed ({abs(days_remaining)} days overdue)"
                )
        else:
            reasons.append("No rejection date provided - deadline check not applicable")
        
        # Regional office check
        if regional_office:
            reasons.append(
                f"Appropriate regional office identified: {regional_office.name}"
            )
        else:
            reasons.append("Could not identify appropriate regional office for the provided location")
        
        return reasons
    
    def _build_eligibility_explanation(
        self,
        is_eligible: bool,
        within_jurisdiction: bool,
        within_deadline: bool,
        regional_office: Optional[OmbudsmanOffice],
        claim_amount: float,
        days_remaining: Optional[int],
        language: str
    ) -> str:
        """Build detailed eligibility explanation."""
        if is_eligible:
            explanation = (
                f"You are eligible to file a complaint with the Insurance Ombudsman. "
                f"Your claim amount of ₹{claim_amount:,.2f} is within the jurisdiction limit of ₹20 lakh. "
            )
            
            if days_remaining is not None:
                explanation += (
                    f"You have {days_remaining} days remaining to file your complaint. "
                )
            
            if regional_office:
                explanation += (
                    f"Your complaint should be filed with the {regional_office.name}, "
                    f"which has jurisdiction over {', '.join(regional_office.jurisdiction)}."
                )
            
            return explanation
        else:
            # Build explanation for ineligibility
            issues = []
            
            if not within_jurisdiction:
                issues.append(
                    f"your claim amount of ₹{claim_amount:,.2f} exceeds the ₹20 lakh jurisdiction limit"
                )
            
            if not within_deadline and days_remaining is not None:
                issues.append(
                    f"the filing deadline has passed by {abs(days_remaining)} days"
                )
            
            if not regional_office:
                issues.append(
                    "we could not identify the appropriate regional office for your location"
                )
            
            explanation = (
                f"Unfortunately, you are not eligible to file with the Insurance Ombudsman because "
                f"{' and '.join(issues)}. "
            )
            
            if not within_jurisdiction:
                explanation += (
                    "For claims exceeding ₹20 lakh, you may need to pursue legal remedies through "
                    "consumer courts or civil courts. "
                )
            
            return explanation
    
    def _build_next_steps(
        self,
        is_eligible: bool,
        within_jurisdiction: bool,
        within_deadline: bool,
        regional_office: Optional[OmbudsmanOffice],
        days_remaining: Optional[int]
    ) -> list:
        """Build list of recommended next steps."""
        next_steps = []
        
        if is_eligible:
            next_steps.append("Gather all relevant documents including policy, claim forms, and rejection letter")
            next_steps.append("Prepare a detailed complaint explaining why the rejection was unfair")
            
            if regional_office:
                next_steps.append(
                    f"Contact {regional_office.name} at {regional_office.contact_email} or "
                    f"{regional_office.contact_phone}"
                )
                next_steps.append(
                    f"Submit your complaint online at {regional_office.website} or by post to: "
                    f"{regional_office.address}"
                )
            
            if days_remaining is not None and days_remaining < 60:
                next_steps.append(
                    f"⚠️ URGENT: You have only {days_remaining} days remaining - file as soon as possible"
                )
        else:
            if not within_jurisdiction:
                next_steps.append("Consider filing a complaint with consumer court for claims exceeding ₹20 lakh")
                next_steps.append("Consult with a lawyer specializing in insurance disputes")
            
            if not within_deadline:
                next_steps.append("The Ombudsman filing deadline has passed")
                next_steps.append("Explore legal remedies through consumer courts or civil litigation")
            
            if not regional_office:
                next_steps.append("Verify your location details and try again")
                next_steps.append("Contact the nearest Ombudsman office for guidance")
        
        return next_steps
    
    def generate_complaint_guidance(
        self,
        claim_id: str,
        claim_details: dict,
        rejection_reason: str,
        policy_id: str,
        language: str = "en"
    ) -> ComplaintGuide:
        """
        Generate comprehensive complaint filing guidance.
        
        Args:
            claim_id: Claim identifier
            claim_details: Dictionary with claim information
            rejection_reason: Insurer's rejection explanation
            policy_id: Policy identifier
            language: Language for output (default: "en")
        
        Returns:
            ComplaintGuide with filing process and documentation requirements
        
        Validates: Requirement 7.5
        """
        guide_id = str(uuid.uuid4())
        
        # Build filing process steps
        filing_process = [
            "Ensure you have exhausted the insurer's internal grievance redressal mechanism",
            "Collect all relevant documents (policy, claim forms, rejection letter, medical records)",
            "Draft a detailed complaint letter explaining the issue and why rejection was unfair",
            "Fill out the Ombudsman complaint form (available on the Ombudsman website)",
            "Submit the complaint online through the Ombudsman portal or by post",
            "Keep copies of all submitted documents for your records",
            "Track your complaint status through the Ombudsman portal",
            "Attend the hearing if scheduled (can be in-person or virtual)",
            "Await the Ombudsman's decision (typically within 3 months)"
        ]
        
        # Build required documents list
        required_documents = [
            "Copy of insurance policy document",
            "Claim form and all supporting documents submitted to insurer",
            "Claim rejection letter from the insurance company",
            "Correspondence with the insurance company (emails, letters)",
            "Medical records and bills (for health insurance claims)",
            "Proof of premium payment",
            "Identity proof (Aadhaar, PAN card, etc.)",
            "Complaint form duly filled and signed"
        ]
        
        # Build argument points based on rejection reason
        argument_points = self._build_argument_points(rejection_reason, claim_details)
        
        # Expected timeline
        expected_timeline = (
            "The Ombudsman typically resolves complaints within 3 months from the date of filing. "
            "Complex cases may take longer. You will be notified of hearings and the final decision."
        )
        
        # Important deadlines
        important_deadlines = [
            "File complaint within 1 year of claim rejection",
            "Respond to any Ombudsman queries within the specified timeframe",
            "Attend scheduled hearings on the given date"
        ]
        
        # Tips and warnings
        tips_and_warnings = [
            "Be factual and avoid emotional language in your complaint",
            "Organize documents chronologically for easy reference",
            "Keep all communication professional and respectful",
            "Do not exaggerate or misrepresent facts",
            "The Ombudsman's decision is binding on the insurer if you accept it",
            "You can reject the Ombudsman's decision and pursue legal remedies",
            "Maintain copies of all submissions and correspondence"
        ]
        
        # Build explanation
        explanation = (
            f"This guide provides step-by-step instructions for filing a complaint with the "
            f"Insurance Ombudsman regarding your claim rejection. The Ombudsman is an independent "
            f"authority that can resolve insurance disputes up to ₹20 lakh without requiring legal "
            f"representation. The process is designed to be accessible and cost-effective for policyholders."
        )
        
        # Citations
        citations = [
            "Insurance Ombudsman Rules, 2017",
            "IRDAI (Insurance Ombudsman) Regulations",
            "Ombudsman complaint filing guidelines"
        ]
        
        return ComplaintGuide(
            guide_id=guide_id,
            claim_id=claim_id,
            filing_process=filing_process,
            required_documents=required_documents,
            argument_points=argument_points,
            expected_timeline=expected_timeline,
            important_deadlines=important_deadlines,
            tips_and_warnings=tips_and_warnings,
            explanation=explanation,
            citations=citations,
            language=language
        )
    
    def _build_argument_points(self, rejection_reason: str, claim_details: dict) -> list:
        """Build argument points based on rejection reason."""
        argument_points = []
        
        # Generic argument points
        argument_points.append(
            "The claim was filed in accordance with policy terms and conditions"
        )
        argument_points.append(
            "All required documentation was provided to the insurer"
        )
        argument_points.append(
            "The rejection reason is not supported by the policy document"
        )
        
        # Add specific points based on rejection reason
        rejection_lower = rejection_reason.lower()
        
        if "pre-existing" in rejection_lower or "ped" in rejection_lower:
            argument_points.append(
                "The condition was properly disclosed during policy purchase"
            )
            argument_points.append(
                "The waiting period for pre-existing diseases has been completed"
            )
        
        if "waiting period" in rejection_lower:
            argument_points.append(
                "The claim was filed after the applicable waiting period"
            )
            argument_points.append(
                "The waiting period clause does not apply to this specific condition"
            )
        
        if "exclusion" in rejection_lower:
            argument_points.append(
                "The treatment/condition is not listed in policy exclusions"
            )
            argument_points.append(
                "The exclusion clause is ambiguous and should be interpreted in favor of the policyholder"
            )
        
        if "documentation" in rejection_lower or "documents" in rejection_lower:
            argument_points.append(
                "All requested documents were submitted within the specified timeframe"
            )
            argument_points.append(
                "The insurer did not clearly communicate which documents were missing"
            )
        
        return argument_points
