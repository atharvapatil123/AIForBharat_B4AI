# Medical Research Recommender

## Overview

The Medical Research Recommender service integrates with PubMed to search for relevant medical research papers based on patient cases and conditions. It ranks papers by relevance, filters for peer-reviewed and recent publications, and formats results for clinical use.

## Features

- **PubMed Integration**: Searches the PubMed database using NCBI E-utilities API
- **Intelligent Query Generation**: Automatically generates search queries from case descriptions and patient conditions
- **Relevance Ranking**: Ranks papers based on title/abstract matching, publication type, and recency
- **Smart Filtering**: Filters for peer-reviewed papers and recent publications (default: last 5 years)
- **Clinical Formatting**: Extracts abstracts, key findings, and generates relevance explanations
- **Rate Limiting**: Respects NCBI API rate limits (3 req/sec without key, 10 req/sec with key)
- **Error Handling**: Gracefully handles API failures and returns informative error messages

## Requirements Validation

This service validates the following requirements:

- **Requirement 9.1**: Search medical research databases for relevant papers
- **Requirement 9.2**: Rank research papers by relevance to the specific case
- **Requirement 9.3**: Provide paper abstracts and key findings
- **Requirement 9.4**: Filter for peer-reviewed and recent publications
- **Requirement 9.5**: Explain why each paper is relevant to the case

## Architecture

### Components

1. **PubMedClient**: Low-level client for PubMed API interactions
   - Handles API requests with rate limiting
   - Searches for papers
   - Fetches article summaries and abstracts
   - Parses XML responses

2. **ResearchRecommender**: High-level service for research recommendations
   - Generates search queries from case descriptions
   - Ranks papers by relevance
   - Applies filters (peer-reviewed, recent)
   - Formats results for clinical use
   - Generates explanations

### Data Flow

```
Case Description + Conditions
        ↓
Generate Search Query
        ↓
PubMed API Search
        ↓
Fetch Summaries & Abstracts
        ↓
Rank by Relevance
        ↓
Apply Filters
        ↓
Format Results
        ↓
ResearchRecommendations
```

## Usage

### Basic Usage

```python
from healthcare_insurance_platform.services.research_recommender import ResearchRecommender

# Initialize the recommender
recommender = ResearchRecommender(
    pubmed_api_key="your_ncbi_api_key",  # Optional but recommended
    pubmed_email="your_email@example.com"  # Recommended by NCBI
)

# Get research recommendations
recommendations = recommender.recommend_research(
    case_description="Patient with uncontrolled hypertension, BP 160/95",
    patient_conditions=["hypertension", "cardiovascular disease"],
    max_papers=10,
    min_year=2020,
    language='en'
)

# Access results
for paper in recommendations.papers:
    print(f"Title: {paper.title}")
    print(f"Relevance: {paper.relevance_score}")
    print(f"Explanation: {paper.relevance_explanation}")
    print(f"Abstract: {paper.abstract}")
```

### Advanced Usage

```python
# Get top papers by relevance
top_papers = recommendations.get_top_papers(n=5)

# Access specific paper details
for paper in top_papers:
    print(f"PubMed ID: {paper.paper_id}")
    print(f"Authors: {', '.join(paper.authors)}")
    print(f"Journal: {paper.journal}")
    print(f"Publication Date: {paper.publication_date}")
    if paper.doi:
        print(f"DOI: {paper.doi}")
    
    # Key findings
    for finding in paper.key_findings:
        print(f"  - {finding}")
```

### Error Handling

```python
try:
    recommendations = recommender.recommend_research(
        case_description=case_description,
        patient_conditions=conditions
    )
except requests.RequestException as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## API Reference

### ResearchRecommender

#### `__init__(pubmed_api_key=None, pubmed_email=None, **kwargs)`

Initialize the research recommender.

**Parameters:**
- `pubmed_api_key` (str, optional): NCBI API key for higher rate limits
- `pubmed_email` (str, optional): Email for NCBI to contact if issues arise
- `**kwargs`: Additional arguments for BaseService

#### `recommend_research(case_description, patient_conditions=None, max_papers=10, min_year=None, language='en')`

Recommend relevant research papers for a medical case.

**Parameters:**
- `case_description` (str): Description of the medical case
- `patient_conditions` (List[str], optional): List of patient diagnoses/conditions
- `max_papers` (int): Maximum number of papers to return (default: 10)
- `min_year` (int, optional): Minimum publication year (default: current year - 5)
- `language` (str): Language code for output (default: 'en')

**Returns:**
- `ResearchRecommendations`: Object containing ranked papers with explanations

**Validates:**
- Requirements 9.1, 9.2, 9.3, 9.4, 9.5

### PubMedClient

#### `__init__(api_key=None, email=None)`

Initialize PubMed client.

**Parameters:**
- `api_key` (str, optional): NCBI API key
- `email` (str, optional): Contact email

#### `search(query, max_results=20, min_date=None, max_date=None)`

Search PubMed for articles.

**Parameters:**
- `query` (str): Search query string
- `max_results` (int): Maximum number of results (default: 20)
- `min_date` (str, optional): Minimum publication date (YYYY/MM/DD)
- `max_date` (str, optional): Maximum publication date (YYYY/MM/DD)

**Returns:**
- `List[str]`: List of PubMed IDs (PMIDs)

#### `fetch_summaries(pmids)`

Fetch article summaries for given PubMed IDs.

**Parameters:**
- `pmids` (List[str]): List of PubMed IDs

**Returns:**
- `List[Dict[str, Any]]`: List of article summary dictionaries

#### `fetch_abstracts(pmids)`

Fetch full abstracts for given PubMed IDs.

**Parameters:**
- `pmids` (List[str]): List of PubMed IDs

**Returns:**
- `Dict[str, str]`: Dictionary mapping PMID to abstract text

## Data Models

### ResearchRecommendations

```python
{
    "recommendation_id": str,
    "case_description": str,
    "papers": List[ResearchPaper],
    "explanation": str,
    "citations": List[str],
    "language": str,
    "generated_at": datetime
}
```

### ResearchPaper

```python
{
    "paper_id": str,           # PubMed ID
    "title": str,
    "authors": List[str],
    "abstract": str,
    "key_findings": List[str],
    "relevance_score": float,  # 0.0 to 1.0
    "relevance_explanation": str,
    "publication_date": str,
    "journal": str,
    "doi": Optional[str]
}
```

## Relevance Scoring

Papers are ranked using a weighted scoring system:

1. **Title Matching (40%)**: Matches case terms in paper title
2. **Abstract Matching (30%)**: Matches case terms in abstract
3. **Publication Type (20%)**: Bonus for clinical trials, reviews, meta-analyses
4. **Recency (10%)**: Bonus for papers published in last 2-5 years

Score calculation:
```
score = (title_matches * 0.4) + 
        (abstract_matches * 0.3) + 
        (pub_type_bonus * 0.2) + 
        (recency_bonus * 0.1)
```

## Filtering Criteria

### Peer-Review Filter
- Excludes: Letters, Editorials, Comments, News
- Includes: All other PubMed-indexed articles (generally peer-reviewed)

### Recency Filter
- Default: Last 5 years
- Configurable via `min_year` parameter

### Publication Type Priority
1. Clinical Trials (highest priority)
2. Meta-Analyses
3. Systematic Reviews
4. Reviews
5. Other research articles

## Rate Limiting

The service respects NCBI E-utilities rate limits:

- **Without API key**: 3 requests per second
- **With API key**: 10 requests per second

Rate limiting is automatically handled by the PubMedClient.

## Best Practices

1. **Use API Key**: Register for a free NCBI API key for higher rate limits
2. **Provide Email**: NCBI requests an email for contact purposes
3. **Specific Queries**: More specific case descriptions yield better results
4. **Condition Lists**: Provide patient conditions for improved relevance
5. **Adjust Year Range**: Use `min_year` to focus on recent research
6. **Error Handling**: Always wrap API calls in try-except blocks

## Configuration

### Environment Variables

```bash
# Optional: Set NCBI API credentials
export NCBI_API_KEY="your_api_key_here"
export NCBI_EMAIL="your_email@example.com"
```

### Code Configuration

```python
import os

recommender = ResearchRecommender(
    pubmed_api_key=os.getenv('NCBI_API_KEY'),
    pubmed_email=os.getenv('NCBI_EMAIL')
)
```

## Limitations

1. **PubMed Coverage**: Only searches PubMed database (biomedical literature)
2. **English Bias**: Most papers are in English
3. **Abstract Only**: Full text not available through API
4. **Rate Limits**: Subject to NCBI rate limiting
5. **Query Complexity**: Very complex queries may return fewer results

## Future Enhancements

1. Integration with additional databases (Cochrane, Google Scholar)
2. Full-text analysis when available
3. Citation network analysis
4. Machine learning-based relevance scoring
5. Automatic query expansion and refinement
6. Support for non-English medical literature

## Troubleshooting

### No Results Found

**Problem**: Search returns no papers

**Solutions:**
- Broaden case description
- Remove very specific terms
- Increase `max_results` parameter
- Adjust `min_year` to include older papers

### Low Relevance Scores

**Problem**: Papers have low relevance scores

**Solutions:**
- Provide more specific patient conditions
- Include key medical terms in case description
- Check for spelling errors in medical terms

### API Errors

**Problem**: Requests fail with API errors

**Solutions:**
- Check internet connection
- Verify API key is valid
- Ensure rate limits are not exceeded
- Check NCBI E-utilities status

### Slow Performance

**Problem**: Recommendations take too long

**Solutions:**
- Reduce `max_papers` parameter
- Use API key for faster rate limits
- Cache results for repeated queries
- Implement async requests (future enhancement)

## Examples

See `examples/research_recommender_example.py` for complete usage examples.

## References

- [NCBI E-utilities Documentation](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [PubMed Search Tips](https://pubmed.ncbi.nlm.nih.gov/help/)
- [NCBI API Key Registration](https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/)
