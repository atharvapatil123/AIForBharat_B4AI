"""
Data models for Insurance Ombudsman offices.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class OmbudsmanOffice(BaseModel):
    """
    Represents a regional Insurance Ombudsman office in India.
    
    Attributes:
        office_id: Unique identifier for the office
        name: Official name of the office
        region: Region name (e.g., "Mumbai", "Delhi", etc.)
        address: Complete office address
        jurisdiction: List of states/union territories under jurisdiction
        contact_phone: Contact phone number
        contact_email: Contact email address
        website: Official website URL
    """
    office_id: str = Field(..., description="Unique identifier for the office")
    name: str = Field(..., description="Official name of the office")
    region: str = Field(..., description="Region name")
    address: str = Field(..., description="Complete office address")
    jurisdiction: List[str] = Field(..., description="List of states/UTs under jurisdiction")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    contact_email: Optional[str] = Field(None, description="Contact email address")
    website: Optional[str] = Field(None, description="Official website URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "office_id": "MUMBAI",
                "name": "Office of the Insurance Ombudsman, Mumbai",
                "region": "Mumbai",
                "address": "3rd Floor, Jeevan Seva Annexe, S.V. Road, Santacruz (W), Mumbai - 400 054",
                "jurisdiction": ["Maharashtra", "Goa"],
                "contact_phone": "022-26106552",
                "contact_email": "bimalokpal.mumbai@gbic.co.in",
                "website": "https://www.cioins.co.in"
            }
        }
