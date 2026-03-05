"""Verification script for Medical Research Recommender implementation."""

import sys
from healthcare_insurance_platform.services.research_recommender import (
    ResearchRecommender,
    PubMedClient
)


def verify_pubmed_client():
    """Verify PubMedClient basic functionality."""
    print("=" * 80)
    print("Verifying PubMedClient...")
    print("=" * 80)
    
    client = PubMedClient()
    
    # Test 1: Client initialization
    print("\n✓ Test 1: Client initialization")
    assert client is not None
    assert client.BASE_URL == "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    print("  - Client initialized successfully")
    print("  - Base URL configured correctly")
    
    # Test 2: Rate limiting configuration
    print("\n✓ Test 2: Rate limiting configuration")
    assert client.rate_limit_delay > 0
    print(f"  - Rate limit delay: {client.rate_limit_delay}s")
    
    # Test 3: Search method exists
    print("\n✓ Test 3: Search method exists")
    assert hasattr(client, 'search')
    assert callable(client.search)
    print("  - Search method available")
    
    # Test 4: Fetch methods exist
    print("\n✓ Test 4: Fetch methods exist")
    assert hasattr(client, 'fetch_summaries')
    assert hasattr(client, 'fetch_abstracts')
    assert callable(client.fetch_summaries)
    assert callable(client.fetch_abstracts)
    print("  - Fetch summaries method available")
    print("  - Fetch abstracts method available")
    
    print("\n✅ PubMedClient verification passed!")
    return True


def verify_research_recommender():
    """Verify ResearchRecommender basic functionality."""
    print("\n" + "=" * 80)
    print("Verifying ResearchRecommender...")
    print("=" * 80)
    
    recommender = ResearchRecommender()
    
    # Test 1: Service initialization
    print("\n✓ Test 1: Service initialization")
    assert recommender is not None
    assert recommender.pubmed_client is not None
    print("  - Service initialized successfully")
    print("  - PubMed client attached")
    
    # Test 2: Main method exists
    print("\n✓ Test 2: Main method exists")
    assert hasattr(recommender, 'recommend_research')
    assert callable(recommender.recommend_research)
    print("  - recommend_research method available")
    
    # Test 3: Helper methods exist
    print("\n✓ Test 3: Helper methods exist")
    helper_methods = [
        '_generate_search_query',
        '_extract_medical_terms',
        '_rank_papers',
        '_apply_filters',
        '_format_papers',
        '_extract_key_findings',
        '_generate_relevance_explanation',
        '_generate_explanation'
    ]
    
    for method in helper_methods:
        assert hasattr(recommender, method)
        assert callable(getattr(recommender, method))
        print(f"  - {method} available")
    
    print("\n✅ ResearchRecommender verification passed!")
    return True


def verify_query_generation():
    """Verify search query generation."""
    print("\n" + "=" * 80)
    print("Verifying Query Generation...")
    print("=" * 80)
    
    recommender = ResearchRecommender()
    
    # Test 1: Simple case description
    print("\n✓ Test 1: Simple case description")
    case = "Patient with hypertension"
    conditions = ["hypertension"]
    query = recommender._generate_search_query(case, conditions)
    assert query is not None
    assert len(query) > 0
    assert "hypertension" in query.lower()
    print(f"  - Generated query: {query[:100]}...")
    
    # Test 2: Multiple conditions
    print("\n✓ Test 2: Multiple conditions")
    case = "Patient with diabetes and kidney disease"
    conditions = ["diabetes", "chronic kidney disease"]
    query = recommender._generate_search_query(case, conditions)
    assert query is not None
    assert "diabetes" in query.lower() or "kidney" in query.lower()
    print(f"  - Generated query: {query[:100]}...")
    
    # Test 3: Medical term extraction
    print("\n✓ Test 3: Medical term extraction")
    text = "Patient has Type 2 Diabetes Mellitus and Hypertension"
    terms = recommender._extract_medical_terms(text)
    assert isinstance(terms, list)
    print(f"  - Extracted terms: {terms}")
    
    print("\n✅ Query generation verification passed!")
    return True


def verify_ranking_logic():
    """Verify paper ranking logic."""
    print("\n" + "=" * 80)
    print("Verifying Ranking Logic...")
    print("=" * 80)
    
    recommender = ResearchRecommender()
    
    # Test 1: Mock paper ranking
    print("\n✓ Test 1: Mock paper ranking")
    mock_summaries = [
        {
            'uid': '12345',
            'title': 'Treatment of Hypertension in Adults',
            'pubtype': ['Clinical Trial'],
            'pubdate': '2023'
        },
        {
            'uid': '67890',
            'title': 'Review of Cardiovascular Disease',
            'pubtype': ['Review'],
            'pubdate': '2022'
        }
    ]
    mock_abstracts = {
        '12345': 'This study examines hypertension treatment approaches...',
        '67890': 'A comprehensive review of cardiovascular disease...'
    }
    
    ranked = recommender._rank_papers(
        mock_summaries,
        mock_abstracts,
        "Patient with hypertension",
        ["hypertension"]
    )
    
    assert isinstance(ranked, list)
    assert len(ranked) == 2
    assert all('relevance_score' in paper for paper in ranked)
    assert all(0 <= paper['relevance_score'] <= 1 for paper in ranked)
    print(f"  - Ranked {len(ranked)} papers")
    print(f"  - Scores: {[p['relevance_score'] for p in ranked]}")
    
    # Test 2: Filtering
    print("\n✓ Test 2: Filtering")
    filtered = recommender._apply_filters(ranked, min_year=2022)
    assert isinstance(filtered, list)
    assert len(filtered) <= len(ranked)
    print(f"  - Filtered to {len(filtered)} papers")
    
    print("\n✅ Ranking logic verification passed!")
    return True


def verify_formatting():
    """Verify result formatting."""
    print("\n" + "=" * 80)
    print("Verifying Result Formatting...")
    print("=" * 80)
    
    recommender = ResearchRecommender()
    
    # Test 1: Key findings extraction
    print("\n✓ Test 1: Key findings extraction")
    abstract = """
    Results: The study showed significant improvement in blood pressure control.
    Conclusion: The new treatment approach demonstrated efficacy in managing hypertension.
    """
    findings = recommender._extract_key_findings(abstract)
    assert isinstance(findings, list)
    print(f"  - Extracted {len(findings)} findings")
    if findings:
        print(f"  - Example: {findings[0][:80]}...")
    
    # Test 2: Relevance explanation
    print("\n✓ Test 2: Relevance explanation")
    explanation = recommender._generate_relevance_explanation(
        title="Treatment of Hypertension",
        abstract="Study on blood pressure management",
        case_description="Patient with high blood pressure",
        patient_conditions=["hypertension"],
        relevance_score=0.8
    )
    assert isinstance(explanation, str)
    assert len(explanation) > 0
    print(f"  - Generated explanation: {explanation[:100]}...")
    
    # Test 3: Overall explanation
    print("\n✓ Test 3: Overall explanation")
    overall = recommender._generate_explanation(
        case_description="Patient case",
        patient_conditions=["hypertension"],
        papers_count=5
    )
    assert isinstance(overall, str)
    assert "5" in overall
    print(f"  - Generated overall explanation: {overall[:100]}...")
    
    print("\n✅ Result formatting verification passed!")
    return True


def verify_error_handling():
    """Verify error handling."""
    print("\n" + "=" * 80)
    print("Verifying Error Handling...")
    print("=" * 80)
    
    recommender = ResearchRecommender()
    
    # Test 1: Empty recommendations
    print("\n✓ Test 1: Empty recommendations")
    empty = recommender._create_empty_recommendations(
        case_description="Test case",
        language='en'
    )
    assert empty is not None
    assert empty.case_description == "Test case"
    assert len(empty.papers) >= 1  # Should have placeholder
    assert len(empty.explanation) > 0
    print("  - Empty recommendations created successfully")
    print(f"  - Explanation: {empty.explanation[:80]}...")
    
    # Test 2: Error recommendations
    print("\n✓ Test 2: Error recommendations")
    error = recommender._create_empty_recommendations(
        case_description="Test case",
        language='en',
        error="API connection failed"
    )
    assert error is not None
    assert "error" in error.explanation.lower()
    print("  - Error recommendations created successfully")
    print(f"  - Explanation: {error.explanation[:80]}...")
    
    print("\n✅ Error handling verification passed!")
    return True


def main():
    """Run all verification tests."""
    print("\n" + "=" * 80)
    print("MEDICAL RESEARCH RECOMMENDER VERIFICATION")
    print("=" * 80)
    
    tests = [
        ("PubMed Client", verify_pubmed_client),
        ("Research Recommender", verify_research_recommender),
        ("Query Generation", verify_query_generation),
        ("Ranking Logic", verify_ranking_logic),
        ("Result Formatting", verify_formatting),
        ("Error Handling", verify_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"\n❌ {test_name} verification failed: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for test_name, result, error in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if error:
            print(f"  Error: {error}")
    
    print("\n" + "=" * 80)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 80)
    
    if passed == total:
        print("\n🎉 All verifications passed! Implementation is complete.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} verification(s) failed. Please review.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
