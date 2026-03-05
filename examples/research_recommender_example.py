"""Example usage of the Medical Research Recommender service."""

from healthcare_insurance_platform.services.research_recommender import ResearchRecommender


def main():
    """Demonstrate research recommender functionality."""
    
    # Initialize the research recommender
    # Note: For production use, provide NCBI API key and email
    recommender = ResearchRecommender(
        pubmed_api_key=None,  # Set your NCBI API key here
        pubmed_email=None     # Set your email here
    )
    
    # Example 1: Simple case with hypertension
    print("=" * 80)
    print("Example 1: Research recommendations for hypertension case")
    print("=" * 80)
    
    case_description = """
    Patient is a 55-year-old male with uncontrolled hypertension.
    Current BP readings: 160/95 mmHg despite medication.
    Looking for evidence-based treatment approaches.
    """
    
    patient_conditions = ["hypertension", "cardiovascular disease"]
    
    try:
        recommendations = recommender.recommend_research(
            case_description=case_description,
            patient_conditions=patient_conditions,
            max_papers=5,
            min_year=2020,
            language='en'
        )
        
        print(f"\nRecommendation ID: {recommendations.recommendation_id}")
        print(f"Case: {recommendations.case_description.strip()}")
        print(f"\nFound {len(recommendations.papers)} relevant papers:")
        print(f"\nOverall Explanation: {recommendations.explanation}")
        print("\n" + "-" * 80)
        
        for i, paper in enumerate(recommendations.papers, 1):
            print(f"\nPaper {i}:")
            print(f"  Title: {paper.title}")
            print(f"  Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
            print(f"  Journal: {paper.journal}")
            print(f"  Publication Date: {paper.publication_date}")
            print(f"  PubMed ID: {paper.paper_id}")
            if paper.doi:
                print(f"  DOI: {paper.doi}")
            print(f"  Relevance Score: {paper.relevance_score:.2f}")
            print(f"  Relevance Explanation: {paper.relevance_explanation}")
            print(f"  Abstract: {paper.abstract[:200]}...")
            if paper.key_findings:
                print(f"  Key Findings:")
                for finding in paper.key_findings:
                    print(f"    - {finding[:150]}...")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Complex case with multiple conditions
    print("\n\n" + "=" * 80)
    print("Example 2: Research recommendations for diabetes with complications")
    print("=" * 80)
    
    case_description_2 = """
    Patient is a 62-year-old female with Type 2 diabetes mellitus and
    diabetic nephropathy. HbA1c: 8.5%. Creatinine: 2.1 mg/dL.
    Seeking latest research on managing diabetic kidney disease.
    """
    
    patient_conditions_2 = ["diabetes mellitus type 2", "diabetic nephropathy", "chronic kidney disease"]
    
    try:
        recommendations_2 = recommender.recommend_research(
            case_description=case_description_2,
            patient_conditions=patient_conditions_2,
            max_papers=3,
            min_year=2021,
            language='en'
        )
        
        print(f"\nRecommendation ID: {recommendations_2.recommendation_id}")
        print(f"Case: {recommendations_2.case_description.strip()}")
        print(f"\nFound {len(recommendations_2.papers)} relevant papers")
        print(f"\nOverall Explanation: {recommendations_2.explanation}")
        
        # Get top papers
        top_papers = recommendations_2.get_top_papers(n=2)
        print(f"\n\nTop {len(top_papers)} papers by relevance:")
        for i, paper in enumerate(top_papers, 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Relevance: {paper.relevance_score:.2f} - {paper.relevance_explanation}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Demonstrate error handling
    print("\n\n" + "=" * 80)
    print("Example 3: Error handling with empty case description")
    print("=" * 80)
    
    try:
        recommendations_3 = recommender.recommend_research(
            case_description="",
            patient_conditions=None,
            max_papers=5,
            language='en'
        )
        
        print(f"\nExplanation: {recommendations_3.explanation}")
        print(f"Papers found: {len(recommendations_3.papers)}")
        
    except Exception as e:
        print(f"Handled error gracefully: {e}")


if __name__ == "__main__":
    main()
