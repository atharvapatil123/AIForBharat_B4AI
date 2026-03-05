# Ombudsman Office Database

## Overview

The Ombudsman Office Database provides a comprehensive repository of all 17 regional Insurance Ombudsman offices in India, along with their jurisdictions and contact information. This database enables the platform to route users to the appropriate regional office based on their location.

## Features

- **Complete Coverage**: All 17 regional Insurance Ombudsman offices
- **Jurisdiction Mapping**: Each office mapped to its states/union territories
- **Location-based Lookup**: Find offices by state, city, or region
- **Search Functionality**: Search offices by keywords
- **Case-insensitive**: All lookups are case-insensitive for user convenience

## Data Model

### OmbudsmanOffice

```python
class OmbudsmanOffice(BaseModel):
    office_id: str              # Unique identifier (e.g., "MUMBAI", "DELHI")
    name: str                   # Official office name
    region: str                 # Region name
    address: str                # Complete office address
    jurisdiction: List[str]     # States/UTs under jurisdiction
    contact_phone: Optional[str]  # Contact phone number
    contact_email: Optional[str]  # Contact email address
    website: Optional[str]        # Official website URL
```

## Usage

### Import the Database

```python
from healthcare_insurance_platform.db.ombudsman_offices import ombudsman_db
```

### Find Office by State

```python
office = ombudsman_db.get_office_by_state("Maharashtra")
if office:
    print(f"Office: {office.name}")
    print(f"Address: {office.address}")
    print(f"Phone: {office.contact_phone}")
```

### Find Office by City

```python
office = ombudsman_db.get_office_by_location("Mumbai")
if office:
    print(f"Office: {office.name}")
    print(f"Region: {office.region}")
```

### Find Office by ID

```python
office = ombudsman_db.get_office_by_id("DELHI")
if office:
    print(f"Office: {office.name}")
    print(f"Jurisdiction: {', '.join(office.jurisdiction)}")
```

### Search Offices

```python
results = ombudsman_db.search_offices("Tamil Nadu")
for office in results:
    print(f"- {office.name}")
```

### Get All Offices

```python
all_offices = ombudsman_db.get_all_offices()
print(f"Total offices: {len(all_offices)}")
```

## Regional Offices

The database includes the following 17 regional offices:

1. **Ahmedabad** - Gujarat, Dadra and Nagar Haveli, Daman and Diu
2. **Bengaluru** - Karnataka
3. **Bhopal** - Madhya Pradesh, Chhattisgarh
4. **Bhubaneswar** - Odisha
5. **Chandigarh** - Punjab, Haryana, Himachal Pradesh, Jammu and Kashmir, Ladakh, Chandigarh
6. **Chennai** - Tamil Nadu, Puducherry, Andaman and Nicobar Islands
7. **Delhi** - Delhi
8. **Guwahati** - Assam, Meghalaya, Manipur, Mizoram, Arunachal Pradesh, Nagaland, Tripura
9. **Hyderabad** - Telangana, Andhra Pradesh
10. **Jaipur** - Rajasthan
11. **Ernakulam** - Kerala, Lakshadweep
12. **Kolkata** - West Bengal, Sikkim, Andaman and Nicobar Islands
13. **Lucknow** - Uttar Pradesh, Uttarakhand
14. **Mumbai** - Maharashtra, Goa
15. **Noida** - Uttar Pradesh (Noida, Greater Noida, Ghaziabad, Gautam Budh Nagar)
16. **Patna** - Bihar, Jharkhand
17. **Pune** - Maharashtra (excluding Mumbai Metropolitan Region), Goa

## Location Mapping

The database includes intelligent location mapping for major cities across India. When a user provides a city name, the system automatically maps it to the appropriate state and returns the corresponding Ombudsman office.

### Supported Cities

The database supports location lookup for 50+ major cities including:
- Mumbai, Pune, Nagpur (Maharashtra)
- Delhi, New Delhi
- Bengaluru, Mysore (Karnataka)
- Chennai, Coimbatore (Tamil Nadu)
- Hyderabad, Secunderabad (Telangana)
- Kolkata (West Bengal)
- Ahmedabad, Surat, Vadodara (Gujarat)
- And many more...

## Implementation Details

### Database Structure

The `OmbudsmanOfficeDatabase` class provides:
- **In-memory storage**: Fast access to all office data
- **Multiple indices**: Optimized lookups by ID, state, and location
- **Normalization**: Case-insensitive matching for user convenience

### Lookup Methods

1. **get_office_by_id(office_id)**: Direct lookup by office identifier
2. **get_office_by_state(state)**: Lookup by state/UT name
3. **get_office_by_location(location)**: Smart lookup by city, state, or region
4. **search_offices(query)**: Full-text search across all fields
5. **get_all_offices()**: Retrieve complete list of offices

### City-to-State Mapping

The database includes a comprehensive city-to-state mapping that handles:
- Common city name variations (e.g., "Bangalore" and "Bengaluru")
- Historical names (e.g., "Calcutta" and "Kolkata", "Madras" and "Chennai")
- Case-insensitive matching
- Major cities across all states and union territories

## Integration with Ombudsman Advisor Service

This database is used by the Ombudsman Advisor service to:
1. Identify the appropriate regional office based on user location
2. Provide contact information for filing complaints
3. Verify jurisdiction for claim amounts and locations
4. Generate guidance for the complaint filing process

## Example Use Cases

### Use Case 1: User in Mumbai with Rejected Claim

```python
# User location: Mumbai
office = ombudsman_db.get_office_by_location("Mumbai")

# Display office information
print(f"Your regional Ombudsman office:")
print(f"Name: {office.name}")
print(f"Address: {office.address}")
print(f"Phone: {office.contact_phone}")
print(f"Email: {office.contact_email}")
```

### Use Case 2: User Provides State Name

```python
# User provides state: Karnataka
office = ombudsman_db.get_office_by_state("Karnataka")

# Display jurisdiction
print(f"Office: {office.name}")
print(f"This office covers: {', '.join(office.jurisdiction)}")
```

### Use Case 3: Search for Offices Covering Multiple States

```python
# Search for offices covering Maharashtra
results = ombudsman_db.search_offices("Maharashtra")

# Display all matching offices
print(f"Offices covering Maharashtra:")
for office in results:
    print(f"- {office.name} ({office.region})")
```

## Data Source

The office information is based on the official Insurance Ombudsman offices as recognized by the Insurance Regulatory and Development Authority of India (IRDAI). The data includes:
- Official office names and addresses
- Contact information (phone and email)
- Jurisdiction mapping to states and union territories
- Official website (https://www.cioins.co.in)

## Maintenance

The database is maintained as a static list in the codebase. When office information changes (new offices, address updates, jurisdiction changes), the `OMBUDSMAN_OFFICES` list in `healthcare_insurance_platform/db/ombudsman_offices.py` should be updated accordingly.

## Testing

The database includes comprehensive verification tests to ensure:
- All 17 offices are loaded correctly
- Lookup methods work as expected
- Case-insensitive matching functions properly
- Location mapping covers major cities
- Jurisdiction coverage is complete

Run the verification script:
```bash
python verify_ombudsman_db.py
```

Run the example script:
```bash
python examples/ombudsman_office_example.py
```

## Related Components

- **OmbudsmanOffice Model**: Data model for office information
- **Ombudsman Advisor Service**: Uses this database for routing and guidance
- **Claim Predictor Service**: Integrates with Ombudsman guidance for rejected claims

## Future Enhancements

Potential improvements for future versions:
1. Dynamic loading from external data source
2. Automatic updates from IRDAI website
3. Historical tracking of office changes
4. Multi-language support for office information
5. Integration with mapping services for directions
6. Office hours and holiday information
7. Queue status and appointment booking
