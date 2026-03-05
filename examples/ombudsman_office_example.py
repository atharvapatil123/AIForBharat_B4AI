"""
Example usage of the Ombudsman Office Database.

This example demonstrates how to use the Ombudsman office database
to find the appropriate regional office based on user location.
"""

from healthcare_insurance_platform.db.ombudsman_offices import ombudsman_db


def main():
    print("=" * 70)
    print("Insurance Ombudsman Office Lookup Examples")
    print("=" * 70)
    print()
    
    # Example 1: Find office by state
    print("Example 1: Find office by state")
    print("-" * 70)
    state = "Maharashtra"
    office = ombudsman_db.get_office_by_state(state)
    if office:
        print(f"State: {state}")
        print(f"Office: {office.name}")
        print(f"Address: {office.address}")
        print(f"Phone: {office.contact_phone}")
        print(f"Email: {office.contact_email}")
        print(f"Jurisdiction: {', '.join(office.jurisdiction)}")
    print()
    
    # Example 2: Find office by city
    print("Example 2: Find office by city")
    print("-" * 70)
    cities = ["Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad"]
    for city in cities:
        office = ombudsman_db.get_office_by_location(city)
        if office:
            print(f"{city:15} -> {office.region} Office")
    print()
    
    # Example 3: Find office by office ID
    print("Example 3: Find office by office ID")
    print("-" * 70)
    office_id = "DELHI"
    office = ombudsman_db.get_office_by_id(office_id)
    if office:
        print(f"Office ID: {office_id}")
        print(f"Name: {office.name}")
        print(f"Region: {office.region}")
        print(f"Jurisdiction: {', '.join(office.jurisdiction)}")
    print()
    
    # Example 4: Search offices by keyword
    print("Example 4: Search offices by keyword")
    print("-" * 70)
    keyword = "Tamil Nadu"
    results = ombudsman_db.search_offices(keyword)
    print(f"Search results for '{keyword}':")
    for office in results:
        print(f"  - {office.name} ({office.region})")
    print()
    
    # Example 5: List all offices
    print("Example 5: List all offices")
    print("-" * 70)
    all_offices = ombudsman_db.get_all_offices()
    print(f"Total offices: {len(all_offices)}")
    print("\nAll regional offices:")
    for i, office in enumerate(all_offices, 1):
        print(f"{i:2}. {office.region:15} - {', '.join(office.jurisdiction)}")
    print()
    
    # Example 6: Handle location not found
    print("Example 6: Handle location not found")
    print("-" * 70)
    unknown_location = "Unknown City"
    office = ombudsman_db.get_office_by_location(unknown_location)
    if office:
        print(f"Office found for {unknown_location}: {office.name}")
    else:
        print(f"No office found for '{unknown_location}'")
        print("Please provide a valid state, city, or region name.")
    print()
    
    # Example 7: Case-insensitive lookup
    print("Example 7: Case-insensitive lookup")
    print("-" * 70)
    test_cases = ["karnataka", "KARNATAKA", "Karnataka", "KaRnAtAkA"]
    print("Testing case-insensitive lookup:")
    for test in test_cases:
        office = ombudsman_db.get_office_by_state(test)
        if office:
            print(f"  '{test}' -> {office.region}")
    print()
    
    print("=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
