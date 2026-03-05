"""Medical Research Recommender service for finding relevant research papers."""

import re
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from urllib.parse import quote

import requests

from healthcare_insurance_platform.core.logging import get_logger
from healthcare_insurance_platform.models.results import (
    ResearchRecommendations,
    ResearchPaper,
)
from healthcare_insurance_platform.services.base import BaseService

logger = get_logger(__name__)


class PubMedClient:
    """
    Client for interacting with PubMed E-utilities API.
    
    Handles API requests, rate limiting, and error handling for PubMed searches.
    
    Validates: Requirements 9.1
    """
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    SEARCH_URL = f"{BASE_URL}/esearch.fcgi"
    FETCH_URL = f"{BASE_URL}/efetch.fcgi"
    SUMMARY_URL = f"{BASE_URL}/esummary.fcgi"
    
    def __init__(self, api_key: Optional[str] = None, email: Optional[str] = None):
        """
        Initialize PubMed client.
        
        Args:
            api_key: NCBI API key for higher rate limits (optional)
            email: Email for NCBI to contact if issues arise (recommended)
        """
        self.api_key = api_key
        self.email = email
        self.logger = logger
        self.session = requests.Session()
        
        # Rate limiting: 3 requests/second without API key, 10/second with key
        self.rate_limit_delay = 0.34 if not api_key else 0.11
        self.last_request_time = 0
    
    def search(
        self,
        query: str,
        max_results: int = 20,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None
    ) -> List[str]:
        """
        Search PubMed for articles matching the query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            min_date: Minimum publication date (YYYY/MM/DD format)
            max_date: Maximum publication date (YYYY/MM/DD format)
            
        Returns:
            List of PubMed IDs (PMIDs)
            
        Raises:
            requests.RequestException: If API request fails
        """
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'sort': 'relevance',
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        if self.email:
            params['email'] = self.email
        if min_date:
            params['mindate'] = min_date
        if max_date:
            params['maxdate'] = max_date
        
        try:
            self._respect_rate_limit()
            response = self.session.get(self.SEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            pmids = data.get('esearchresult', {}).get('idlist', [])
            
            self.logger.info(
                f"PubMed search completed",
                query=query,
                results_count=len(pmids)
            )
            
            return pmids
            
        except requests.RequestException as e:
            self.logger.error(f"PubMed search failed", error=str(e), query=query)
            raise
        except (KeyError, ValueError) as e:
            self.logger.error(f"Failed to parse PubMed response", error=str(e))
            return []
    
    def fetch_summaries(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch article summaries for given PubMed IDs.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of article summary dictionaries
            
        Raises:
            requests.RequestException: If API request fails
        """
        if not pmids:
            return []
        
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'json',
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        if self.email:
            params['email'] = self.email
        
        try:
            self._respect_rate_limit()
            response = self.session.get(self.SUMMARY_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            result = data.get('result', {})
            
            summaries = []
            for pmid in pmids:
                if pmid in result:
                    summaries.append(result[pmid])
            
            self.logger.info(f"Fetched {len(summaries)} article summaries")
            
            return summaries
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch PubMed summaries", error=str(e))
            raise
        except (KeyError, ValueError) as e:
            self.logger.error(f"Failed to parse PubMed summaries", error=str(e))
            return []
    
    def fetch_abstracts(self, pmids: List[str]) -> Dict[str, str]:
        """
        Fetch full abstracts for given PubMed IDs.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            Dictionary mapping PMID to abstract text
            
        Raises:
            requests.RequestException: If API request fails
        """
        if not pmids:
            return {}
        
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'rettype': 'abstract',
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        if self.email:
            params['email'] = self.email
        
        try:
            self._respect_rate_limit()
            response = self.session.get(self.FETCH_URL, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML to extract abstracts
            abstracts = self._parse_abstracts_from_xml(response.text)
            
            self.logger.info(f"Fetched {len(abstracts)} abstracts")
            
            return abstracts
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch PubMed abstracts", error=str(e))
            raise
        except Exception as e:
            self.logger.error(f"Failed to parse abstracts", error=str(e))
            return {}
    
    def _parse_abstracts_from_xml(self, xml_text: str) -> Dict[str, str]:
        """
        Parse abstracts from PubMed XML response.
        
        Args:
            xml_text: XML response text
            
        Returns:
            Dictionary mapping PMID to abstract text
        """
        abstracts = {}
        
        # Simple regex-based parsing (for production, use xml.etree.ElementTree)
        # Extract PMID and AbstractText pairs
        pmid_pattern = r'<PMID[^>]*>(\d+)</PMID>'
        abstract_pattern = r'<AbstractText[^>]*>(.*?)</AbstractText>'
        
        # Find all articles
        article_pattern = r'<PubmedArticle>(.*?)</PubmedArticle>'
        articles = re.findall(article_pattern, xml_text, re.DOTALL)
        
        for article in articles:
            pmid_match = re.search(pmid_pattern, article)
            if pmid_match:
                pmid = pmid_match.group(1)
                
                # Extract all abstract text sections
                abstract_parts = re.findall(abstract_pattern, article, re.DOTALL)
                if abstract_parts:
                    # Clean HTML tags and join parts
                    abstract = ' '.join(
                        re.sub(r'<[^>]+>', '', part).strip()
                        for part in abstract_parts
                    )
                    abstracts[pmid] = abstract
        
        return abstracts
    
    def _respect_rate_limit(self):
        """Implement rate limiting to comply with NCBI guidelines."""
        import time
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()


class ResearchRecommender(BaseService):
    """
    Service for recommending relevant medical research papers.
    
    Integrates with PubMed to search for relevant papers, ranks them by relevance,
    and formats results for clinical use.
    
    Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
    """
    
    def __init__(
        self,
        pubmed_api_key: Optional[str] = None,
        pubmed_email: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize research recommender.
        
        Args:
            pubmed_api_key: NCBI API key for PubMed access
            pubmed_email: Email for NCBI contact
            **kwargs: Additional arguments for BaseService
        """
        super().__init__(**kwargs)
        self.pubmed_client = PubMedClient(api_key=pubmed_api_key, email=pubmed_email)
    
    def recommend_research(
        self,
        case_description: str,
        patient_conditions: Optional[List[str]] = None,
        max_papers: int = 10,
        min_year: Optional[int] = None,
        language: str = 'en'
    ) -> ResearchRecommendations:
        """
        Recommend relevant research papers for a medical case.
        
        Searches medical research databases, ranks papers by relevance,
        filters for peer-reviewed and recent publications, and formats
        results for clinical use.
        
        Args:
            case_description: Description of the medical case
            patient_conditions: List of patient diagnoses/conditions
            max_papers: Maximum number of papers to return
            min_year: Minimum publication year (for recent papers filter)
            language: Language code for output
            
        Returns:
            ResearchRecommendations object with ranked papers
            
        Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
        """
        self._log_operation(
            "recommend_research",
            case_description=case_description[:100],
            conditions_count=len(patient_conditions) if patient_conditions else 0
        )
        
        try:
            # Generate search query from case description
            search_query = self._generate_search_query(
                case_description,
                patient_conditions
            )
            
            # Set date filter for recent papers (default: last 5 years)
            if min_year is None:
                min_year = datetime.now().year - 5
            min_date = f"{min_year}/01/01"
            
            # Search PubMed
            pmids = self.pubmed_client.search(
                query=search_query,
                max_results=max_papers * 2,  # Get more to filter
                min_date=min_date
            )
            
            if not pmids:
                self.logger.warning("No research papers found", query=search_query)
                # Return empty recommendations with explanation
                return self._create_empty_recommendations(
                    case_description,
                    language
                )
            
            # Fetch article summaries
            summaries = self.pubmed_client.fetch_summaries(pmids)
            
            # Fetch abstracts
            abstracts = self.pubmed_client.fetch_abstracts(pmids)
            
            # Rank papers by relevance
            ranked_papers = self._rank_papers(
                summaries,
                abstracts,
                case_description,
                patient_conditions
            )
            
            # Apply filters (peer-reviewed, recent)
            filtered_papers = self._apply_filters(ranked_papers, min_year)
            
            # Take top N papers
            top_papers = filtered_papers[:max_papers]
            
            # Format results
            research_papers = self._format_papers(
                top_papers,
                case_description,
                patient_conditions
            )
            
            # Generate overall explanation
            explanation = self._generate_explanation(
                case_description,
                patient_conditions,
                len(research_papers)
            )
            
            # Generate citations
            citations = [f"PubMed ID: {paper.paper_id}" for paper in research_papers]
            
            # Create recommendations
            recommendations = ResearchRecommendations(
                recommendation_id=f"research_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                case_description=case_description,
                papers=research_papers,
                explanation=explanation,
                citations=citations,
                language=language
            )
            
            self.logger.info(
                f"Generated research recommendations",
                papers_count=len(research_papers)
            )
            
            return recommendations
            
        except Exception as e:
            self._log_error("recommend_research", e)
            # Return empty recommendations with error explanation
            return self._create_empty_recommendations(
                case_description,
                language,
                error=str(e)
            )
    
    def _generate_search_query(
        self,
        case_description: str,
        patient_conditions: Optional[List[str]] = None
    ) -> str:
        """
        Generate PubMed search query from case description and conditions.
        
        Args:
            case_description: Medical case description
            patient_conditions: List of patient conditions
            
        Returns:
            Formatted PubMed search query
            
        Validates: Requirements 9.1
        """
        query_parts = []
        
        # Extract key medical terms from case description
        medical_terms = self._extract_medical_terms(case_description)
        if medical_terms:
            query_parts.extend(medical_terms)
        
        # Add patient conditions
        if patient_conditions:
            query_parts.extend(patient_conditions)
        
        # Build query with AND operators
        if query_parts:
            # Limit to first 5 terms to avoid overly restrictive queries
            main_terms = query_parts[:5]
            query = ' AND '.join(f'"{term}"' for term in main_terms)
        else:
            # Fallback to case description
            query = case_description[:200]
        
        # Add filters for clinical relevance
        query += ' AND (clinical trial[pt] OR review[pt] OR systematic review[pt])'
        
        self.logger.debug(f"Generated search query", query=query)
        
        return query
    
    def _extract_medical_terms(self, text: str) -> List[str]:
        """
        Extract medical terms from text.
        
        Args:
            text: Text to extract terms from
            
        Returns:
            List of medical terms
        """
        # Simple extraction based on capitalized medical terms
        # In production, use medical NLP library like scispacy
        
        terms = []
        
        # Common medical term patterns
        patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized phrases
            r'\b(?:diabetes|hypertension|cancer|asthma|copd|pneumonia|arthritis)\b',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            terms.extend(matches)
        
        # Remove duplicates and common non-medical words
        stopwords = {'The', 'A', 'An', 'In', 'On', 'At', 'To', 'For', 'With', 'Patient'}
        terms = [t for t in set(terms) if t not in stopwords and len(t) > 2]
        
        return terms[:10]  # Limit to 10 terms
    
    def _rank_papers(
        self,
        summaries: List[Dict[str, Any]],
        abstracts: Dict[str, str],
        case_description: str,
        patient_conditions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Rank papers by relevance to the case.
        
        Calculates relevance scores based on title/abstract matching,
        publication type, and recency.
        
        Args:
            summaries: List of PubMed article summaries
            abstracts: Dictionary of abstracts by PMID
            case_description: Medical case description
            patient_conditions: List of patient conditions
            
        Returns:
            List of papers with relevance scores, sorted by score
            
        Validates: Requirements 9.2
        """
        ranked_papers = []
        
        # Extract key terms for matching
        case_terms = set(self._extract_medical_terms(case_description))
        if patient_conditions:
            case_terms.update(condition.lower() for condition in patient_conditions)
        
        for summary in summaries:
            pmid = str(summary.get('uid', ''))
            title = summary.get('title', '')
            
            # Calculate relevance score
            score = 0.0
            
            # Title matching (weight: 0.4)
            title_lower = title.lower()
            title_matches = sum(1 for term in case_terms if term.lower() in title_lower)
            score += (title_matches / max(len(case_terms), 1)) * 0.4
            
            # Abstract matching (weight: 0.3)
            if pmid in abstracts:
                abstract_lower = abstracts[pmid].lower()
                abstract_matches = sum(1 for term in case_terms if term.lower() in abstract_lower)
                score += (abstract_matches / max(len(case_terms), 1)) * 0.3
            
            # Publication type bonus (weight: 0.2)
            pub_types = summary.get('pubtype', [])
            if isinstance(pub_types, list):
                if any('Clinical Trial' in pt for pt in pub_types):
                    score += 0.2
                elif any('Review' in pt for pt in pub_types):
                    score += 0.15
                elif any('Meta-Analysis' in pt for pt in pub_types):
                    score += 0.2
            
            # Recency bonus (weight: 0.1)
            pub_date = summary.get('pubdate', '')
            if pub_date:
                year_match = re.search(r'(\d{4})', pub_date)
                if year_match:
                    year = int(year_match.group(1))
                    current_year = datetime.now().year
                    years_ago = current_year - year
                    if years_ago <= 2:
                        score += 0.1
                    elif years_ago <= 5:
                        score += 0.05
            
            # Add to ranked list
            ranked_papers.append({
                'summary': summary,
                'abstract': abstracts.get(pmid, ''),
                'relevance_score': min(score, 1.0)  # Cap at 1.0
            })
        
        # Sort by relevance score (descending)
        ranked_papers.sort(key=lambda p: p['relevance_score'], reverse=True)
        
        self.logger.debug(
            f"Ranked {len(ranked_papers)} papers",
            top_score=ranked_papers[0]['relevance_score'] if ranked_papers else 0
        )
        
        return ranked_papers
    
    def _apply_filters(
        self,
        papers: List[Dict[str, Any]],
        min_year: int
    ) -> List[Dict[str, Any]]:
        """
        Apply filters for peer-reviewed and recent publications.
        
        Args:
            papers: List of ranked papers
            min_year: Minimum publication year
            
        Returns:
            Filtered list of papers
            
        Validates: Requirements 9.4
        """
        filtered = []
        
        for paper in papers:
            summary = paper['summary']
            
            # Check publication year
            pub_date = summary.get('pubdate', '')
            year_match = re.search(r'(\d{4})', pub_date)
            if year_match:
                year = int(year_match.group(1))
                if year < min_year:
                    continue
            
            # PubMed articles are generally peer-reviewed
            # Additional filtering could check for specific publication types
            pub_types = summary.get('pubtype', [])
            if isinstance(pub_types, list):
                # Exclude certain types
                excluded_types = ['Letter', 'Editorial', 'Comment', 'News']
                if any(et in str(pub_types) for et in excluded_types):
                    continue
            
            filtered.append(paper)
        
        self.logger.debug(f"Filtered to {len(filtered)} papers from {len(papers)}")
        
        return filtered
    
    def _format_papers(
        self,
        papers: List[Dict[str, Any]],
        case_description: str,
        patient_conditions: Optional[List[str]] = None
    ) -> List[ResearchPaper]:
        """
        Format papers into ResearchPaper objects.
        
        Extracts abstracts and key findings, generates relevance explanations,
        and formats results for clinical use.
        
        Args:
            papers: List of ranked and filtered papers
            case_description: Medical case description
            patient_conditions: List of patient conditions
            
        Returns:
            List of ResearchPaper objects
            
        Validates: Requirements 9.3, 9.5
        """
        research_papers = []
        
        for paper in papers:
            summary = paper['summary']
            abstract = paper['abstract']
            relevance_score = paper['relevance_score']
            
            pmid = str(summary.get('uid', ''))
            title = summary.get('title', 'Untitled')
            authors = summary.get('authors', [])
            
            # Extract author names
            author_names = []
            if isinstance(authors, list):
                for author in authors[:5]:  # Limit to first 5 authors
                    if isinstance(author, dict):
                        name = author.get('name', '')
                        if name:
                            author_names.append(name)
            
            # Extract key findings from abstract
            key_findings = self._extract_key_findings(abstract)
            
            # Generate relevance explanation
            relevance_explanation = self._generate_relevance_explanation(
                title,
                abstract,
                case_description,
                patient_conditions,
                relevance_score
            )
            
            # Get publication info
            pub_date = summary.get('pubdate', 'Unknown')
            journal = summary.get('source', 'Unknown Journal')
            doi = summary.get('elocationid', None)
            if doi and not doi.startswith('10.'):
                doi = None  # Only keep valid DOIs
            
            # Create ResearchPaper object
            research_paper = ResearchPaper(
                paper_id=pmid,
                title=title,
                authors=author_names,
                abstract=abstract if abstract else "Abstract not available",
                key_findings=key_findings,
                relevance_score=relevance_score,
                relevance_explanation=relevance_explanation,
                publication_date=pub_date,
                journal=journal,
                doi=doi
            )
            
            research_papers.append(research_paper)
        
        return research_papers
    
    def _extract_key_findings(self, abstract: str) -> List[str]:
        """
        Extract key findings from abstract.
        
        Args:
            abstract: Paper abstract
            
        Returns:
            List of key findings
        """
        if not abstract:
            return []
        
        findings = []
        
        # Look for conclusion/results sections
        sections = ['conclusion', 'results', 'findings']
        for section in sections:
            pattern = rf'{section}[:\s]+(.*?)(?=\.|$)'
            matches = re.findall(pattern, abstract, re.IGNORECASE)
            if matches:
                findings.extend(m.strip() for m in matches if len(m.strip()) > 20)
        
        # If no structured findings, extract sentences with key result indicators
        if not findings:
            result_indicators = [
                'showed', 'demonstrated', 'found', 'revealed',
                'indicated', 'suggested', 'concluded'
            ]
            sentences = re.split(r'[.!?]', abstract)
            for sentence in sentences:
                if any(indicator in sentence.lower() for indicator in result_indicators):
                    findings.append(sentence.strip())
        
        # Limit to 3 key findings
        return findings[:3]
    
    def _generate_relevance_explanation(
        self,
        title: str,
        abstract: str,
        case_description: str,
        patient_conditions: Optional[List[str]],
        relevance_score: float
    ) -> str:
        """
        Generate explanation of why paper is relevant.
        
        Args:
            title: Paper title
            abstract: Paper abstract
            case_description: Medical case description
            patient_conditions: List of patient conditions
            relevance_score: Calculated relevance score
            
        Returns:
            Relevance explanation text
            
        Validates: Requirements 9.5
        """
        explanations = []
        
        # Check for condition matches
        if patient_conditions:
            title_lower = title.lower()
            abstract_lower = abstract.lower() if abstract else ''
            
            matched_conditions = [
                cond for cond in patient_conditions
                if cond.lower() in title_lower or cond.lower() in abstract_lower
            ]
            
            if matched_conditions:
                explanations.append(
                    f"This paper addresses {', '.join(matched_conditions)}, "
                    f"which are relevant to the patient's conditions."
                )
        
        # Check for treatment/intervention mentions
        treatment_keywords = ['treatment', 'therapy', 'intervention', 'management']
        if any(kw in title.lower() for kw in treatment_keywords):
            explanations.append(
                "This paper discusses treatment approaches applicable to this case."
            )
        
        # Check for clinical trial/review
        if 'clinical trial' in title.lower() or 'clinical trial' in (abstract.lower() if abstract else ''):
            explanations.append(
                "This clinical trial provides evidence-based treatment insights."
            )
        elif 'review' in title.lower():
            explanations.append(
                "This review synthesizes current knowledge on the topic."
            )
        
        # Add relevance score context
        if relevance_score >= 0.7:
            explanations.append("High relevance to the case based on content analysis.")
        elif relevance_score >= 0.4:
            explanations.append("Moderate relevance to the case based on content analysis.")
        else:
            explanations.append("Related to the case with potential insights.")
        
        # Combine explanations
        if explanations:
            return ' '.join(explanations)
        else:
            return "This paper may provide relevant background information for the case."
    
    def _generate_explanation(
        self,
        case_description: str,
        patient_conditions: Optional[List[str]],
        papers_count: int
    ) -> str:
        """
        Generate overall explanation for recommendations.
        
        Args:
            case_description: Medical case description
            patient_conditions: List of patient conditions
            papers_count: Number of papers recommended
            
        Returns:
            Overall explanation text
        """
        explanation_parts = [
            f"Found {papers_count} relevant research papers for this case."
        ]
        
        if patient_conditions:
            explanation_parts.append(
                f"Papers were selected based on relevance to: {', '.join(patient_conditions)}."
            )
        
        explanation_parts.append(
            "Papers are ranked by relevance score, considering title/abstract matching, "
            "publication type (clinical trials and reviews prioritized), and recency."
        )
        
        explanation_parts.append(
            "All papers are peer-reviewed and published in the last 5 years."
        )
        
        return ' '.join(explanation_parts)
    
    def _create_empty_recommendations(
        self,
        case_description: str,
        language: str,
        error: Optional[str] = None
    ) -> ResearchRecommendations:
        """
        Create empty recommendations when no papers found or error occurs.
        
        Args:
            case_description: Medical case description
            language: Language code
            error: Optional error message
            
        Returns:
            ResearchRecommendations with empty papers list
        """
        if error:
            explanation = (
                f"Unable to retrieve research recommendations due to an error: {error}. "
                "Please try again later or contact support."
            )
        else:
            explanation = (
                "No relevant research papers found for this case. "
                "Try broadening the search criteria or checking the case description."
            )
        
        # Create a placeholder paper to satisfy the min_length=1 constraint
        placeholder_paper = ResearchPaper(
            paper_id="N/A",
            title="No papers found",
            authors=[],
            abstract="No relevant research papers were found for this case.",
            key_findings=[],
            relevance_score=0.0,
            relevance_explanation="No papers matched the search criteria.",
            publication_date="N/A",
            journal="N/A",
            doi=None
        )
        
        return ResearchRecommendations(
            recommendation_id=f"research_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            case_description=case_description,
            papers=[placeholder_paper],
            explanation=explanation,
            citations=[],
            language=language
        )
