"""
Database of Insurance Ombudsman offices in India.

This module contains the complete list of 17 regional Insurance Ombudsman offices
with their jurisdictions and contact information.
"""

from typing import Dict, List, Optional
from healthcare_insurance_platform.models.ombudsman import OmbudsmanOffice


# Complete database of 17 regional Insurance Ombudsman offices in India
OMBUDSMAN_OFFICES: List[OmbudsmanOffice] = [
    OmbudsmanOffice(
        office_id="AHMEDABAD",
        name="Office of the Insurance Ombudsman, Ahmedabad",
        region="Ahmedabad",
        address="2nd Floor, Ambica House, Near C.U. Shah College, Ashram Road, Ahmedabad - 380 014",
        jurisdiction=["Gujarat", "Dadra and Nagar Haveli", "Daman and Diu"],
        contact_phone="079-27546150",
        contact_email="bimalokpal.ahmedabad@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="BENGALURU",
        name="Office of the Insurance Ombudsman, Bengaluru",
        region="Bengaluru",
        address="Jeevan Soudha Building, Ground Floor, PID No. 57-27-N-19, 19/19, 24th Main Road, JP Nagar, 1st Phase, Bengaluru - 560 078",
        jurisdiction=["Karnataka"],
        contact_phone="080-26652048",
        contact_email="bimalokpal.bengaluru@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="BHOPAL",
        name="Office of the Insurance Ombudsman, Bhopal",
        region="Bhopal",
        address="Janak Vihar Complex, 2nd Floor, 6, Malviya Nagar, Opp. Airtel Office, Near New Market, Bhopal - 462 003",
        jurisdiction=["Madhya Pradesh", "Chhattisgarh"],
        contact_phone="0755-2769201",
        contact_email="bimalokpal.bhopal@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="BHUBANESWAR",
        name="Office of the Insurance Ombudsman, Bhubaneswar",
        region="Bhubaneswar",
        address="62, Forest Park, Bhubaneswar - 751 009",
        jurisdiction=["Odisha"],
        contact_phone="0674-2596461",
        contact_email="bimalokpal.bhubaneswar@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="CHANDIGARH",
        name="Office of the Insurance Ombudsman, Chandigarh",
        region="Chandigarh",
        address="S.C.O. No. 101-103, 2nd Floor, Batra Building, Sector 17-D, Chandigarh - 160 017",
        jurisdiction=["Punjab", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Ladakh", "Chandigarh"],
        contact_phone="0172-2706196",
        contact_email="bimalokpal.chandigarh@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="CHENNAI",
        name="Office of the Insurance Ombudsman, Chennai",
        region="Chennai",
        address="Fatima Akhtar Court, 4th Floor, 453 (old 312), Anna Salai, Teynampet, Chennai - 600 018",
        jurisdiction=["Tamil Nadu", "Puducherry", "Andaman and Nicobar Islands"],
        contact_phone="044-24333668",
        contact_email="bimalokpal.chennai@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="DELHI",
        name="Office of the Insurance Ombudsman, Delhi",
        region="Delhi",
        address="2/2 A, Universal Insurance Building, Asaf Ali Road, New Delhi - 110 002",
        jurisdiction=["Delhi"],
        contact_phone="011-23239633",
        contact_email="bimalokpal.delhi@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="GUWAHATI",
        name="Office of the Insurance Ombudsman, Guwahati",
        region="Guwahati",
        address="Jeevan Nivesh, 5th Floor, Near Panbazar Overbridge, S.S. Road, Guwahati - 781 001",
        jurisdiction=["Assam", "Meghalaya", "Manipur", "Mizoram", "Arunachal Pradesh", "Nagaland", "Tripura"],
        contact_phone="0361-2132204",
        contact_email="bimalokpal.guwahati@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="HYDERABAD",
        name="Office of the Insurance Ombudsman, Hyderabad",
        region="Hyderabad",
        address="6-2-46, 1st Floor, Moin Court, Lane Opp. Saleem Function Palace, A.C. Guards, Lakdi-Ka-Pool, Hyderabad - 500 004",
        jurisdiction=["Telangana", "Andhra Pradesh"],
        contact_phone="040-65504123",
        contact_email="bimalokpal.hyderabad@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="JAIPUR",
        name="Office of the Insurance Ombudsman, Jaipur",
        region="Jaipur",
        address="Jeevan Nidhi - II Building, Ground Floor, Bhawani Singh Marg, Jaipur - 302 005",
        jurisdiction=["Rajasthan"],
        contact_phone="0141-2740363",
        contact_email="bimalokpal.jaipur@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="ERNAKULAM",
        name="Office of the Insurance Ombudsman, Ernakulam",
        region="Ernakulam",
        address="2nd Floor, Pulinat Building, Opp. Cochin Shipyard, M.G. Road, Ernakulam - 682 015",
        jurisdiction=["Kerala", "Lakshadweep"],
        contact_phone="0484-2358759",
        contact_email="bimalokpal.ernakulam@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="KOLKATA",
        name="Office of the Insurance Ombudsman, Kolkata",
        region="Kolkata",
        address="Hindustan Building, 4th Floor, 4, C.R. Avenue, Kolkata - 700 072",
        jurisdiction=["West Bengal", "Sikkim", "Andaman and Nicobar Islands"],
        contact_phone="033-22124339",
        contact_email="bimalokpal.kolkata@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="LUCKNOW",
        name="Office of the Insurance Ombudsman, Lucknow",
        region="Lucknow",
        address="6th Floor, Jeevan Bhawan, Phase-II, Nawal Kishore Road, Hazratganj, Lucknow - 226 001",
        jurisdiction=["Uttar Pradesh", "Uttarakhand"],
        contact_phone="0522-2231330",
        contact_email="bimalokpal.lucknow@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="MUMBAI",
        name="Office of the Insurance Ombudsman, Mumbai",
        region="Mumbai",
        address="3rd Floor, Jeevan Seva Annexe, S.V. Road, Santacruz (W), Mumbai - 400 054",
        jurisdiction=["Maharashtra", "Goa"],
        contact_phone="022-26106552",
        contact_email="bimalokpal.mumbai@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="NOIDA",
        name="Office of the Insurance Ombudsman, Noida",
        region="Noida",
        address="Bhagwan Sahai Palace, 4th Floor, Main Road, Naya Bans, Sector-15, Distt: Gautam Buddh Nagar, U.P. - 201 301",
        jurisdiction=["Uttar Pradesh (Noida, Greater Noida, Ghaziabad, Gautam Budh Nagar)"],
        contact_phone="0120-2514250",
        contact_email="bimalokpal.noida@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="PATNA",
        name="Office of the Insurance Ombudsman, Patna",
        region="Patna",
        address="1st Floor, Kalpana Arcade Building, Bazar Samiti Road, Bahadurpur, Patna - 800 006",
        jurisdiction=["Bihar", "Jharkhand"],
        contact_phone="0612-2680952",
        contact_email="bimalokpal.patna@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
    OmbudsmanOffice(
        office_id="PUNE",
        name="Office of the Insurance Ombudsman, Pune",
        region="Pune",
        address="Jeevan Darshan Building, 3rd Floor, C.T.S. No. 195 to 198, N.C. Kelkar Road, Narayan Peth, Pune - 411 030",
        jurisdiction=["Maharashtra (excluding Mumbai Metropolitan Region)", "Goa"],
        contact_phone="020-41312555",
        contact_email="bimalokpal.pune@gbic.co.in",
        website="https://www.cioins.co.in"
    ),
]


class OmbudsmanOfficeDatabase:
    """
    Database manager for Insurance Ombudsman offices.
    
    Provides methods to search and retrieve Ombudsman office information
    based on location, state, or office ID.
    """
    
    def __init__(self):
        """Initialize the database with all 17 regional offices."""
        self.offices = OMBUDSMAN_OFFICES
        self._build_indices()
    
    def _build_indices(self):
        """Build lookup indices for efficient searching."""
        # Index by office ID
        self.offices_by_id: Dict[str, OmbudsmanOffice] = {
            office.office_id: office for office in self.offices
        }
        
        # Index by state/UT jurisdiction
        self.offices_by_state: Dict[str, OmbudsmanOffice] = {}
        for office in self.offices:
            for state in office.jurisdiction:
                # Normalize state name for lookup
                normalized_state = state.strip().lower()
                self.offices_by_state[normalized_state] = office
    
    def get_office_by_id(self, office_id: str) -> Optional[OmbudsmanOffice]:
        """
        Get an Ombudsman office by its ID.
        
        Args:
            office_id: Office identifier (e.g., "MUMBAI", "DELHI")
        
        Returns:
            OmbudsmanOffice if found, None otherwise
        """
        return self.offices_by_id.get(office_id.upper())
    
    def get_office_by_state(self, state: str) -> Optional[OmbudsmanOffice]:
        """
        Get the appropriate Ombudsman office for a given state/UT.
        
        Args:
            state: State or Union Territory name
        
        Returns:
            OmbudsmanOffice if found, None otherwise
        """
        normalized_state = state.strip().lower()
        return self.offices_by_state.get(normalized_state)
    
    def get_office_by_location(self, location: str) -> Optional[OmbudsmanOffice]:
        """
        Get the appropriate Ombudsman office for a given location.
        
        This method attempts to match the location string against:
        1. Office regions (e.g., "Mumbai", "Delhi")
        2. States/UTs in jurisdiction
        3. Common city names mapped to states
        
        Args:
            location: Location string (city, state, or region)
        
        Returns:
            OmbudsmanOffice if found, None otherwise
        """
        normalized_location = location.strip().lower()
        
        # First, try to match against office regions
        for office in self.offices:
            if office.region.lower() == normalized_location:
                return office
        
        # Try to match against states
        office = self.get_office_by_state(location)
        if office:
            return office
        
        # Try common city-to-state mappings
        city_to_state = self._get_city_to_state_mapping()
        if normalized_location in city_to_state:
            state = city_to_state[normalized_location]
            return self.get_office_by_state(state)
        
        return None
    
    def _get_city_to_state_mapping(self) -> Dict[str, str]:
        """
        Get mapping of major cities to their states.
        
        Returns:
            Dictionary mapping city names to state names
        """
        return {
            # Major cities
            "mumbai": "Maharashtra",
            "pune": "Maharashtra",
            "nagpur": "Maharashtra",
            "delhi": "Delhi",
            "new delhi": "Delhi",
            "bengaluru": "Karnataka",
            "bangalore": "Karnataka",
            "mysore": "Karnataka",
            "chennai": "Tamil Nadu",
            "madras": "Tamil Nadu",
            "coimbatore": "Tamil Nadu",
            "hyderabad": "Telangana",
            "secunderabad": "Telangana",
            "kolkata": "West Bengal",
            "calcutta": "West Bengal",
            "ahmedabad": "Gujarat",
            "surat": "Gujarat",
            "vadodara": "Gujarat",
            "jaipur": "Rajasthan",
            "jodhpur": "Rajasthan",
            "udaipur": "Rajasthan",
            "lucknow": "Uttar Pradesh",
            "kanpur": "Uttar Pradesh",
            "varanasi": "Uttar Pradesh",
            "agra": "Uttar Pradesh",
            "noida": "Uttar Pradesh",
            "greater noida": "Uttar Pradesh",
            "ghaziabad": "Uttar Pradesh",
            "chandigarh": "Chandigarh",
            "amritsar": "Punjab",
            "ludhiana": "Punjab",
            "gurgaon": "Haryana",
            "gurugram": "Haryana",
            "faridabad": "Haryana",
            "bhopal": "Madhya Pradesh",
            "indore": "Madhya Pradesh",
            "gwalior": "Madhya Pradesh",
            "patna": "Bihar",
            "gaya": "Bihar",
            "bhubaneswar": "Odisha",
            "cuttack": "Odisha",
            "guwahati": "Assam",
            "dispur": "Assam",
            "kochi": "Kerala",
            "cochin": "Kerala",
            "thiruvananthapuram": "Kerala",
            "trivandrum": "Kerala",
            "ernakulam": "Kerala",
            "visakhapatnam": "Andhra Pradesh",
            "vijayawada": "Andhra Pradesh",
            "raipur": "Chhattisgarh",
            "ranchi": "Jharkhand",
            "jamshedpur": "Jharkhand",
            "dehradun": "Uttarakhand",
            "shimla": "Himachal Pradesh",
            "srinagar": "Jammu and Kashmir",
            "jammu": "Jammu and Kashmir",
            "leh": "Ladakh",
            "panaji": "Goa",
            "imphal": "Manipur",
            "aizawl": "Mizoram",
            "shillong": "Meghalaya",
            "agartala": "Tripura",
            "itanagar": "Arunachal Pradesh",
            "kohima": "Nagaland",
            "gangtok": "Sikkim",
            "port blair": "Andaman and Nicobar Islands",
            "puducherry": "Puducherry",
            "pondicherry": "Puducherry",
            "silvassa": "Dadra and Nagar Haveli",
            "daman": "Daman and Diu",
            "kavaratti": "Lakshadweep",
        }
    
    def get_all_offices(self) -> List[OmbudsmanOffice]:
        """
        Get all Ombudsman offices.
        
        Returns:
            List of all OmbudsmanOffice objects
        """
        return self.offices.copy()
    
    def search_offices(self, query: str) -> List[OmbudsmanOffice]:
        """
        Search for offices matching a query string.
        
        Searches across office names, regions, and jurisdictions.
        
        Args:
            query: Search query string
        
        Returns:
            List of matching OmbudsmanOffice objects
        """
        query_lower = query.strip().lower()
        results = []
        
        for office in self.offices:
            # Search in name, region, and jurisdiction
            if (query_lower in office.name.lower() or
                query_lower in office.region.lower() or
                any(query_lower in state.lower() for state in office.jurisdiction)):
                results.append(office)
        
        return results


# Global instance for easy access
ombudsman_db = OmbudsmanOfficeDatabase()
