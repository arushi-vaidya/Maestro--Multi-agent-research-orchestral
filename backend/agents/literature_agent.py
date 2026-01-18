"""
Literature Review Agent
Analyzes biomedical literature using PubMed

This agent provides:
- PubMed literature search
- Publication metadata extraction
- Citation analysis
- Research trend identification
- Abstract summarization

Design Philosophy:
- Read-only operations (no writes to AKGP yet)
- Deterministic ranking (no ML)
- Defensive API failure handling
- Clear provenance for all results
"""

import os
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class LiteratureAgent:
    """
    Literature Review Agent

    Searches and analyzes biomedical literature from PubMed.
    Provides structured summaries with full provenance tracking.

    Features:
    - PubMed API integration
    - Publication metadata extraction
    - Abstract summarization
    - Deterministic relevance ranking
    - Defensive error handling
    """

    def __init__(self):
        """Initialize Literature Agent"""
        self.name = "Literature Agent"
        self.agent_id = "literature"

        # PubMed E-utilities API (no key required for basic usage, but recommended)
        self.pubmed_api_key = os.getenv("PUBMED_API_KEY", "")
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

        # LLM API keys for optional summarization
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY", "")

        logger.info(f"{self.name} initialized (PubMed API)")

    def extract_keywords(self, query: str) -> str:
        """
        Extract clean keywords from user query for PubMed search

        Args:
            query: User query

        Returns:
            Clean keywords for PubMed
        """
        import re

        logger.info(f"Extracting literature search keywords from: '{query}'")

        # Try LLM extraction first (if available)
        if self.groq_api_key:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a PubMed search query optimizer. Extract ONLY 2-5 key biomedical terms for literature search. NO explanations, NO lists. Return ONLY space-separated keywords. Examples: 'GLP-1 diabetes treatment' or 'cancer immunotherapy checkpoint inhibitors'."
                        },
                        {
                            "role": "user",
                            "content": query
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 50
                }

                response = requests.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                keywords = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()

                if keywords:
                    # Sanitize the output
                    keywords = self._sanitize_keywords(keywords)
                    logger.info(f"Extracted keywords: '{keywords}'")
                    return keywords

            except Exception as e:
                logger.warning(f"Groq keyword extraction failed: {e}")

        # Fallback: Deterministic keyword extraction
        keywords = self._deterministic_keyword_extraction(query)
        logger.info(f"Using fallback keywords: '{keywords}'")
        return keywords

    def _deterministic_keyword_extraction(self, query: str) -> str:
        """
        Deterministic fallback for keyword extraction
        Removes stopwords and extracts meaningful terms
        """
        import re

        # Common stopwords to remove
        stopwords = {'what', 'are', 'the', 'is', 'for', 'in', 'on', 'of', 'with', 'to', 'a', 'an', 'and', 'or', 'but', 'show', 'me', 'tell', 'about', 'latest', 'recent'}

        # Tokenize and clean
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        # Join and sanitize
        result = " ".join(keywords[:10])  # Limit to 10 terms
        return self._sanitize_keywords(result)

    def _sanitize_keywords(self, keywords: str) -> str:
        """
        Sanitize keywords for PubMed search

        Removes:
        - Numbered lists
        - Bullet points
        - Markdown formatting
        - Excess whitespace
        - Multiple lines

        Returns:
            Clean keyword string
        """
        import re

        # Keep only first line
        keywords = keywords.split('\n')[0].strip()

        # Remove numbered lists
        keywords = re.sub(r'^\d+\.\s*', '', keywords)

        # Remove bullet points
        keywords = re.sub(r'^[\-\*\•]\s*', '', keywords)

        # Remove markdown
        keywords = re.sub(r'\*\*', '', keywords)
        keywords = re.sub(r'\*', '', keywords)
        keywords = re.sub(r'`', '', keywords)

        # Remove parentheticals
        keywords = re.sub(r'\([^)]*\)', '', keywords)

        # Collapse whitespace
        keywords = re.sub(r'\s+', ' ', keywords)

        return keywords.strip()

    def search_pubmed(self, keywords: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search PubMed for publications

        Args:
            keywords: Search keywords
            max_results: Maximum number of results

        Returns:
            List of publication records with metadata
        """
        logger.info(f"Searching PubMed for: '{keywords}' (max {max_results} results)")

        try:
            # Step 1: Search for PMIDs
            search_url = f"{self.base_url}/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": keywords,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance"
            }

            if self.pubmed_api_key:
                search_params["api_key"] = self.pubmed_api_key

            response = requests.get(search_url, params=search_params, timeout=15)
            response.raise_for_status()
            search_result = response.json()

            pmids = search_result.get("esearchresult", {}).get("idlist", [])

            if not pmids:
                logger.warning(f"No PubMed results found for: '{keywords}'")
                return []

            logger.info(f"Found {len(pmids)} PMIDs")

            # Step 2: Fetch publication details
            fetch_url = f"{self.base_url}/efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "rettype": "abstract"
            }

            if self.pubmed_api_key:
                fetch_params["api_key"] = self.pubmed_api_key

            response = requests.get(fetch_url, params=fetch_params, timeout=20)
            response.raise_for_status()

            # Parse XML response
            publications = self._parse_pubmed_xml(response.text)

            logger.info(f"Successfully retrieved {len(publications)} publications")
            return publications

        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []

    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """
        Parse PubMed XML response

        Args:
            xml_text: XML response from PubMed

        Returns:
            List of parsed publication records
        """
        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(xml_text)
            publications = []

            for article in root.findall(".//PubmedArticle"):
                try:
                    # Extract metadata
                    pmid = article.find(".//PMID")
                    pmid_text = pmid.text if pmid is not None else "N/A"

                    title = article.find(".//ArticleTitle")
                    title_text = title.text if title is not None else "No title"

                    abstract = article.find(".//AbstractText")
                    abstract_text = abstract.text if abstract is not None else "No abstract available"

                    # Authors
                    author_list = article.findall(".//Author")
                    authors = []
                    for author in author_list[:5]:  # Top 5 authors
                        last = author.find("LastName")
                        first = author.find("ForeName")
                        if last is not None:
                            author_name = last.text
                            if first is not None:
                                author_name += f" {first.text[0]}"  # First initial
                            authors.append(author_name)

                    # Publication date
                    pub_date = article.find(".//PubDate")
                    year = pub_date.find("Year") if pub_date is not None else None
                    year_text = year.text if year is not None else "Unknown"

                    # Journal
                    journal = article.find(".//Journal/Title")
                    journal_text = journal.text if journal is not None else "Unknown journal"

                    publication = {
                        "pmid": pmid_text,
                        "title": title_text,
                        "abstract": abstract_text,
                        "authors": authors,
                        "year": year_text,
                        "journal": journal_text,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid_text}/",
                        "source": "PubMed"
                    }

                    publications.append(publication)

                except Exception as e:
                    logger.warning(f"Failed to parse article: {e}")
                    continue

            return publications

        except Exception as e:
            logger.error(f"XML parsing failed: {e}")
            return []

    def generate_summary(self, publications: List[Dict[str, Any]], keywords: str) -> str:
        """
        Generate literature review summary from publications

        Args:
            publications: List of publication records
            keywords: Search keywords

        Returns:
            Summary text
        """
        if not publications:
            return f"No literature found for: {keywords}"

        logger.info(f"Generating summary for {len(publications)} publications")

        # Try LLM-powered summary first
        if self.gemini_api_key or self.groq_api_key:
            llm_summary = self._generate_llm_summary(publications, keywords)
            if llm_summary:
                return llm_summary

        # Fallback: Structured summary
        return self._generate_structured_summary(publications, keywords)

    def _generate_llm_summary(self, publications: List[Dict[str, Any]], keywords: str) -> str:
        """Generate summary using LLM"""
        # Prepare publication data
        pub_summaries = []
        for i, pub in enumerate(publications[:10], 1):  # Top 10
            authors = ", ".join(pub.get("authors", [])[:3])
            pub_summaries.append(
                f"{i}. {pub['title']} ({pub['year']})\n"
                f"   Authors: {authors}\n"
                f"   Journal: {pub['journal']}\n"
                f"   Abstract: {pub['abstract'][:200]}..."
            )

        pubs_text = "\n\n".join(pub_summaries)

        # Try Gemini first
        if self.gemini_api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.gemini_api_key}"
                headers = {"Content-Type": "application/json"}

                prompt = f"""Analyze this biomedical literature for: {keywords}

Publications:
{pubs_text}

Provide a structured literature review with:

1. OVERVIEW
Brief summary of the research landscape.

2. KEY FINDINGS
Main discoveries and conclusions from the literature.

3. RESEARCH TRENDS
Patterns, gaps, and emerging directions.

4. CLINICAL RELEVANCE
Implications for clinical practice or drug development.

Use plain text, UPPERCASE for section headers."""

                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 2000
                    }
                }

                response = requests.post(url, json=payload, headers=headers, timeout=45)
                response.raise_for_status()
                result = response.json()

                if 'candidates' in result and len(result['candidates']) > 0:
                    summary = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    logger.info(f"Generated Gemini summary ({len(summary)} chars)")
                    return summary

            except Exception as e:
                logger.warning(f"Gemini summary generation failed: {e}")

        # Try Groq fallback
        if self.groq_api_key:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }

                prompt = f"""Analyze biomedical literature for: {keywords}

{pubs_text}

Provide structured review with:
1. OVERVIEW
2. KEY FINDINGS
3. RESEARCH TRENDS
4. CLINICAL RELEVANCE

Plain text, UPPERCASE headers."""

                payload = {
                    "model": "llama-3.1-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You are a biomedical literature analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }

                response = requests.post(url, json=payload, headers=headers, timeout=45)
                response.raise_for_status()
                summary = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()

                if summary:
                    logger.info(f"Generated Groq summary ({len(summary)} chars)")
                    return summary

            except Exception as e:
                logger.warning(f"Groq summary generation failed: {e}")

        return ""

    def _generate_structured_fallback(self, keywords: str, publications: List[Dict[str, Any]]) -> str:
        """Generate structured fallback summary (alias for test compatibility)"""
        return self._generate_structured_summary(publications, keywords)

    def _generate_structured_summary(self, publications: List[Dict[str, Any]], keywords: str) -> str:
        """Generate structured fallback summary"""
        logger.info("Generating structured fallback summary")

        sections = []
        sections.append("LITERATURE REVIEW")
        sections.append("")
        sections.append(f"Search Query: {keywords}")
        sections.append(f"Publications Found: {len(publications)}")
        sections.append("")

        sections.append("1. OVERVIEW")
        sections.append("")
        sections.append(f"This literature review analyzed {len(publications)} publications from PubMed related to {keywords}.")

        # Year distribution
        years = {}
        for pub in publications:
            year = pub.get("year", "Unknown")
            years[year] = years.get(year, 0) + 1

        if years:
            sections.append(f"Publication years range: {min(years.keys())} - {max(years.keys())}")
        sections.append("")

        sections.append("2. KEY PUBLICATIONS")
        sections.append("")
        for i, pub in enumerate(publications[:5], 1):
            authors = ", ".join(pub.get("authors", [])[:2])
            sections.append(f"{i}. {pub['title']}")
            sections.append(f"   {authors} ({pub['year']})")
            sections.append(f"   {pub['journal']}")
            sections.append("")

        sections.append("3. RESEARCH TRENDS")
        sections.append("")
        sections.append(f"The literature contains {len(publications)} relevant publications covering various aspects of {keywords}.")
        sections.append("")

        return "\n".join(sections)

    def process(self, user_query: str) -> Dict[str, Any]:
        """
        Main processing method for Literature Agent

        Args:
            user_query: User's literature query

        Returns:
            Literature review results with provenance
        """
        logger.info("="*50)
        logger.info(f"Starting Literature Agent processing for: '{user_query}'")
        logger.info("="*50)

        try:
            # Step 1: Extract keywords
            logger.info("Step 1/3: Extracting keywords")
            keywords = self.extract_keywords(user_query)

            # Step 2: Search PubMed
            logger.info("Step 2/3: Searching PubMed")
            publications = self.search_pubmed(keywords, max_results=20)

            if not publications:
                logger.warning(f"No PubMed results found for: '{keywords}'")
                return {
                    "query": user_query,
                    "summary": f"No publications found for: {keywords}",
                    "comprehensive_summary": "Unable to generate literature review due to lack of publications.",
                    "publications": [],
                    "total_publications": 0,
                    "keywords": keywords,
                    "confidence_score": 0.0,
                    "references": [],
                    "agent_id": self.agent_id,
                    "agent_name": self.name,
                    "source": "PubMed",
                    "timestamp": datetime.utcnow().isoformat()
                }

            # Step 3: Generate summary
            logger.info("Step 3/3: Generating literature review")
            comprehensive_summary = self.generate_summary(publications, keywords)

            # Prepare basic summary
            basic_summary = f"Found {len(publications)} publications for {keywords}."

            # Calculate confidence based on result count
            confidence_score = min(len(publications) / 20, 1.0)  # Max at 20 results

            # Create references from publications
            references = []
            for i, pub in enumerate(publications[:20], 1):
                pmid = pub.get('pmid', 'N/A')
                references.append({
                    "id": f"PMID:{pmid}",
                    "title": pub.get('title', 'No title'),
                    "url": pub.get('url', f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"),
                    "date": pub.get('year', 'N/A'),
                    "source": "PubMed",
                    "agentId": "literature",
                    "confidence": confidence_score
                })

            logger.info("="*50)
            logger.info("Literature Agent processing completed successfully")
            logger.info("="*50)

            return {
                "query": user_query,
                "summary": basic_summary,
                "comprehensive_summary": comprehensive_summary,
                "publications": publications,
                "total_publications": len(publications),
                "keywords": keywords,
                "confidence_score": confidence_score,
                "references": references,
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "source": "PubMed",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Literature Agent processing failed: {e}", exc_info=True)
            return {
                "summary": f"Literature search failed: {str(e)}",
                "comprehensive_summary": f"Unable to generate literature review due to error: {str(e)}",
                "publications": [],
                "total_publications": 0,
                "keywords": "",
                "confidence_score": 0.0,
                "agent_id": self.agent_id,
                "agent_name": self.name
            }
