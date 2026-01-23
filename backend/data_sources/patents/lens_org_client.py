"""
Lens.org Patents API Client
Provides global access to patent data via Lens.org Patents API
https://docs.api.lens.org/

NOTE: This replaces USPTO PatentsView which is regionally blocked from Indian servers
Lens.org provides global patent coverage with no regional restrictions
"""

import logging
import requests
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class LensOrgClient:
    """
    Client for Lens.org Patents API

    API Documentation: https://docs.api.lens.org/request-patent.html
    Authentication: Required (Bearer token)
    Rate limit: Based on subscription tier

    Advantages over USPTO:
    - Global patent coverage (not just US)
    - No regional blocking (works from India)
    - Rich metadata and family information
    - Better search capabilities (Elasticsearch DSL)
    """

    BASE_URL = "https://api.lens.org"

    # API endpoints
    SEARCH_ENDPOINT = f"{BASE_URL}/patent/search"

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Lens.org Patents API client

        Args:
            api_token: Lens.org API token (defaults to LENS_API_TOKEN env var)

        Raises:
            ValueError: If no API token provided
        """
        self.api_token = api_token or os.getenv("LENS_API_TOKEN", "")

        if not self.api_token:
            logger.warning("⚠️  No Lens.org API token provided. Set LENS_API_TOKEN environment variable.")
            logger.warning("⚠️  Get free token at: https://www.lens.org/lens/user/subscriptions")

        self.session = requests.Session()

        # Set headers
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'MAESTRO-Patent-Intelligence-Agent/2.0'
        }

        self.session.headers.update(headers)
        self.rate_limit_delay = 1.0  # Conservative 1 request per second
        self.last_request_time = 0
        logger.info("Lens.org Patents API client initialized")

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def search_patents(
        self,
        query: Dict[str, Any],
        include: List[str] = None,
        size: int = 100,
        sort: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Search patents using Lens.org API

        Args:
            query: Query in Elasticsearch DSL format
            include: List of fields to return
            size: Number of results (max 1000)
            sort: Sort criteria

        Returns:
            API response with patent data

        API Documentation: https://docs.api.lens.org/request-patent.html
        """
        if include is None:
            include = [
                "lens_id",
                "biblio",
                "title",
                "abstract",
                "date_published",
                "parties",
                "citations",
                "classifications_cpc",
                "legal_status"
            ]

        if sort is None:
            sort = [{"date_published": "desc"}]

        # Build request payload
        payload = {
            "query": query,
            "include": include,
            "size": min(size, 1000),
            "sort": sort
        }

        self._rate_limit()

        try:
            logger.info(f"Searching Lens.org patents with query: {query}")
            response = self.session.post(
                self.SEARCH_ENDPOINT,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            total_count = data.get('total', 0)
            logger.info(f"Found {total_count} patents via Lens.org")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Lens.org API request failed: {e}")
            logger.error(f"Endpoint: {self.SEARCH_ENDPOINT}")
            logger.error(f"Query: {query}")
            # Return empty result instead of raising
            return {"data": [], "total": 0}

    def search_by_keywords(
        self,
        keywords: str,
        limit: int = 100,
        years_back: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search patents by keywords in title or abstract

        Args:
            keywords: Search keywords (comma-separated or single term)
            limit: Maximum number of results
            years_back: Search patents from last N years

        Returns:
            List of patent records with normalized structure
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years_back)

        # Parse keywords - handle comma-separated terms
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]

        if not keyword_list:
            logger.warning("No keywords provided for patent search")
            return []

        # Build Elasticsearch DSL query
        # Lens.org uses Elasticsearch format, so we use match queries
        if len(keyword_list) == 1:
            # Single keyword - simple match
            keyword_query = {
                "bool": {
                    "should": [
                        {"match": {"title": keyword_list[0]}},
                        {"match": {"abstract.text": keyword_list[0]}}
                    ],
                    "minimum_should_match": 1
                }
            }
        else:
            # Multiple keywords - OR them together
            should_clauses = []
            for kw in keyword_list:
                should_clauses.append({"match": {"title": kw}})
                should_clauses.append({"match": {"abstract.text": kw}})

            keyword_query = {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1
                }
            }

        # Add date filter
        query = {
            "bool": {
                "must": [keyword_query],
                "filter": [
                    {
                        "range": {
                            "date_published": {
                                "gte": start_date.strftime("%Y-%m-%d"),
                                "lte": end_date.strftime("%Y-%m-%d")
                            }
                        }
                    }
                ]
            }
        }

        result = self.search_patents(
            query,
            size=min(limit, 1000),
            sort=[{"date_published": "desc"}]
        )

        # Normalize the response to match USPTO format
        patents = result.get('data', [])
        return self._normalize_patents(patents)

    def search_by_assignee(
        self,
        assignee: str,
        keywords: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search patents by assignee (company/organization)

        Args:
            assignee: Assignee name (e.g., "Novo Nordisk")
            keywords: Optional keywords to filter
            limit: Maximum number of results

        Returns:
            List of patent records (normalized)
        """
        must_clauses = [
            {"match": {"parties.applicants.name": assignee}}
        ]

        if keywords:
            must_clauses.append({
                "bool": {
                    "should": [
                        {"match": {"title": keywords}},
                        {"match": {"abstract.text": keywords}}
                    ],
                    "minimum_should_match": 1
                }
            })

        query = {
            "bool": {
                "must": must_clauses
            }
        }

        result = self.search_patents(
            query,
            size=min(limit, 1000),
            sort=[{"date_published": "desc"}]
        )

        patents = result.get('data', [])
        return self._normalize_patents(patents)

    def search_by_classification(
        self,
        cpc_code: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search patents by CPC (Cooperative Patent Classification) code

        Args:
            cpc_code: CPC code (e.g., "A61K" for pharmaceuticals)
            limit: Maximum number of results

        Returns:
            List of patent records (normalized)
        """
        query = {
            "bool": {
                "must": [
                    {"prefix": {"classifications_cpc.classification.symbol": cpc_code}}
                ]
            }
        }

        result = self.search_patents(
            query,
            size=min(limit, 1000),
            sort=[{"date_published": "desc"}]
        )

        patents = result.get('data', [])
        return self._normalize_patents(patents)

    def get_patent_family(
        self,
        lens_id: str
    ) -> Dict[str, Any]:
        """
        Get patent details by Lens ID

        Args:
            lens_id: Lens ID (e.g., "123-456-789-123-456")

        Returns:
            Patent details (normalized)
        """
        query = {
            "bool": {
                "must": [
                    {"term": {"lens_id": lens_id}}
                ]
            }
        }

        result = self.search_patents(query, size=1)
        patents = result.get('data', [])

        if patents:
            normalized = self._normalize_patents(patents)
            return normalized[0] if normalized else {}
        return {}

    def search_expiring_patents(
        self,
        keywords: str,
        years_from_now: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find patents expiring within specified years
        (Patents typically expire 20 years from filing/priority date)

        Args:
            keywords: Search keywords
            years_from_now: Find patents expiring within N years

        Returns:
            List of expiring patents
        """
        # Patents expire 20 years from filing/priority date
        end_date = datetime.now()
        # Look for patents filed 17-20 years ago (expiring in next 0-3 years)
        start_date = end_date - timedelta(days=365 * 20)
        cutoff_date = end_date - timedelta(days=365 * (20 - years_from_now))

        # Parse keywords
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]

        # Build keyword query
        should_clauses = []
        for kw in keyword_list:
            should_clauses.append({"match": {"title": kw}})
            should_clauses.append({"match": {"abstract.text": kw}})

        query = {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "should": should_clauses,
                            "minimum_should_match": 1
                        }
                    }
                ],
                "filter": [
                    {
                        "range": {
                            "biblio.priority_claims.earliest_priority_date": {
                                "gte": start_date.strftime("%Y-%m-%d"),
                                "lte": cutoff_date.strftime("%Y-%m-%d")
                            }
                        }
                    }
                ]
            }
        }

        result = self.search_patents(
            query,
            size=1000,
            sort=[{"biblio.priority_claims.earliest_priority_date": "asc"}]
        )

        patents = result.get('data', [])
        return self._normalize_patents(patents)

    def get_top_assignees(
        self,
        keywords: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get top assignees (companies) in a technology area

        Args:
            keywords: Technology keywords
            limit: Number of top assignees

        Returns:
            List of assignees with patent counts
        """
        # Parse keywords
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]

        # Build keyword query
        should_clauses = []
        for kw in keyword_list:
            should_clauses.append({"match": {"title": kw}})
            should_clauses.append({"match": {"abstract.text": kw}})

        query = {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "should": should_clauses,
                            "minimum_should_match": 1
                        }
                    }
                ]
            }
        }

        result = self.search_patents(
            query,
            size=1000,
            sort=[{"date_published": "desc"}]
        )

        patents = result.get('data', [])

        # Count patents per assignee
        assignee_counts = {}
        for patent in patents:
            # Extract applicants from biblio.parties
            biblio = patent.get('biblio', {})
            parties = biblio.get('parties', {})
            applicants = parties.get('applicants', [])

            for applicant in applicants:
                org = applicant.get('extracted_name', {}).get('value', 'Unknown')
                if org and org != 'Unknown':
                    assignee_counts[org] = assignee_counts.get(org, 0) + 1

        # Sort by count
        top_assignees = [
            {"organization": org, "patent_count": count}
            for org, count in sorted(
                assignee_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
        ]

        return top_assignees

    def _normalize_patents(self, patents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize patent data from Lens.org format to expected structure

        Args:
            patents: Raw patent data from Lens.org API

        Returns:
            List of normalized patent records matching USPTO format
        """
        normalized_patents = []
        for patent in patents:
            biblio = patent.get('biblio', {})
            parties = biblio.get('parties', {})

            # Extract publication number
            pub_number = biblio.get('publication_reference', {}).get('doc_number', '')

            # Extract title and abstract
            title = patent.get('title', '')
            if isinstance(title, list):
                title = title[0] if title else ''

            abstract_data = patent.get('abstract', [])
            abstract_text = ''
            if abstract_data:
                if isinstance(abstract_data, list):
                    abstract_text = abstract_data[0].get('text', '') if abstract_data else ''
                elif isinstance(abstract_data, dict):
                    abstract_text = abstract_data.get('text', '')

            # Build normalized structure
            normalized = {
                'patent_number': pub_number,
                'patent_title': title,
                'patent_abstract': abstract_text,
                'patent_date': patent.get('date_published', ''),
                'citedby_patent_count': len(patent.get('cited_by', [])),
                'patent_type': biblio.get('publication_reference', {}).get('kind', ''),
                'assignees': [],
                'inventors': [],
                'cpcs': []
            }

            # Normalize assignees (applicants in Lens.org)
            applicants = parties.get('applicants', [])
            for applicant in applicants:
                extracted_name = applicant.get('extracted_name', {})
                normalized['assignees'].append({
                    'assignee_organization': extracted_name.get('value', ''),
                    'assignee_country': applicant.get('residence', '')
                })

            # Normalize inventors
            inventors = parties.get('inventors', [])
            for inventor in inventors:
                extracted_name = inventor.get('extracted_name', {})
                name_value = extracted_name.get('value', '')
                # Split name into first and last (simple heuristic)
                name_parts = name_value.split(' ', 1)
                normalized['inventors'].append({
                    'inventor_first_name': name_parts[0] if name_parts else '',
                    'inventor_last_name': name_parts[1] if len(name_parts) > 1 else ''
                })

            # Normalize CPCs
            cpc_classifications = patent.get('classifications_cpc', [])
            for cpc in cpc_classifications:
                classification = cpc.get('classification', {})
                symbol = classification.get('symbol', '')
                # Extract section (first letter, e.g., "A" from "A61K")
                section = symbol[0] if symbol else ''
                normalized['cpcs'].append({
                    'cpc_section': section
                })

            normalized_patents.append(normalized)

        return normalized_patents
