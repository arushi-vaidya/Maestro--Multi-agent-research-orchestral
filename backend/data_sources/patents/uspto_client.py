"""
USPTO PatentsView Search API Client
Provides access to US patent data via the PatentsView Search API
https://search.patentsview.org/docs/

NOTE: Legacy API (api.patentsview.org) was deprecated May 1, 2025
New API: search.patentsview.org with API key authentication
"""

import logging
import requests
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class USPTOClient:
    """
    Client for USPTO PatentsView Search API (2025+)

    API Documentation: https://search.patentsview.org/docs/
    Requires API key (optional for testing, required for production)
    Rate limit: 45 requests per minute

    Legacy API (deprecated May 2025): https://api.patentsview.org
    New API (current): https://search.patentsview.org/api/v1/
    """

    BASE_URL = "https://search.patentsview.org/api/v1"

    # API endpoints
    PATENTS_ENDPOINT = f"{BASE_URL}/patent/"
    INVENTORS_ENDPOINT = f"{BASE_URL}/inventor/"
    ASSIGNEES_ENDPOINT = f"{BASE_URL}/assignee/"
    LOCATIONS_ENDPOINT = f"{BASE_URL}/location/"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize USPTO PatentsView Search API client

        Args:
            api_key: Optional API key (can also be set via USPTO_API_KEY env var)
                    Not required for basic queries, but recommended for production
        """
        self.api_key = api_key or os.getenv('USPTO_API_KEY', '')
        self.session = requests.Session()

        # Set headers
        headers = {
            'User-Agent': 'MAESTRO-Patent-Intelligence-Agent/2.0',
            'Content-Type': 'application/json'
        }

        # Add API key if available (required for production use)
        if self.api_key:
            headers['X-Api-Key'] = self.api_key
            logger.info("USPTO PatentsView Search API client initialized with API key")
        else:
            logger.warning("⚠️  No USPTO API key found - some features may be limited")
            logger.info("Get free API key at: https://search.patentsview.org/")

        self.session.headers.update(headers)
        self.rate_limit_delay = 1.4  # ~43 requests per minute to stay under limit
        self.last_request_time = 0
        logger.info("USPTO PatentsView Search API client initialized (v2 - 2025)")

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def search_patents(
        self,
        query: Dict[str, Any],
        fields: List[str] = None,
        per_page: int = 100,
        page: int = 1,
        sort: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Search patents using PatentsView Search API (2025+)

        Args:
            query: Query in PatentsView format (e.g., {"_text_any": {"patent_abstract": "GLP-1"}})
            fields: List of fields to return
            per_page: Results per page (max 10000)
            page: Page number
            sort: Sort criteria

        Returns:
            API response with patent data

        New API Documentation: https://search.patentsview.org/docs/
        """
        if fields is None:
            fields = [
                "patent_id",
                "patent_title",
                "patent_abstract",
                "patent_date",
                "assignees_at_grant.assignee_organization",
                "assignees_at_grant.assignee_country",
                "inventors_at_grant.inventor_name_first",
                "inventors_at_grant.inventor_name_last",
                "cpcs_at_grant.cpc_section",
                "patent_num_cited_by_us_patents",
                "patent_type"
            ]

        if sort is None:
            sort = [{"patent_date": "desc"}]

        # Build query parameters (new API uses GET with query params)
        import json
        params = {
            'q': json.dumps(query),
            'f': json.dumps(fields),
            'per_page': per_page,
            'page': page,
            's': json.dumps(sort)
        }

        self._rate_limit()

        try:
            logger.info(f"Searching USPTO patents (new API) with query: {query}")
            response = self.session.get(
                self.PATENTS_ENDPOINT,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            patent_count = data.get('total_patent_count', 0)
            logger.info(f"Found {patent_count} patents")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"USPTO API request failed: {e}")
            logger.error(f"Endpoint: {self.PATENTS_ENDPOINT}")
            logger.error(f"Query: {query}")
            raise

    def search_by_keywords(
        self,
        keywords: str,
        limit: int = 100,
        years_back: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search patents by keywords in title or abstract (2025+ API)

        Args:
            keywords: Search keywords
            limit: Maximum number of results
            years_back: Search patents from last N years

        Returns:
            List of patent records with normalized structure
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years_back)

        # Build query using PatentsView Search API query language
        query = {
            "_and": [
                {
                    "_or": [
                        {"_text_any": {"patent_title": keywords}},
                        {"_text_any": {"patent_abstract": keywords}}
                    ]
                },
                {
                    "_gte": {
                        "patent_date": start_date.strftime("%Y-%m-%d")
                    }
                }
            ]
        }

        result = self.search_patents(
            query,
            per_page=min(limit, 1000),
            page=1,
            sort=[{"patent_date": "desc"}]
        )

        # Normalize the response to match expected structure
        patents = result.get('patents', [])

        # Transform new API format to match old agent expectations
        normalized_patents = []
        for patent in patents:
            normalized = {
                'patent_number': patent.get('patent_id', ''),
                'patent_title': patent.get('patent_title', ''),
                'patent_abstract': patent.get('patent_abstract', ''),
                'patent_date': patent.get('patent_date', ''),
                'citedby_patent_count': patent.get('patent_num_cited_by_us_patents', 0),
                'patent_type': patent.get('patent_type', ''),
                'assignees': [],
                'inventors': [],
                'cpcs': []
            }

            # Normalize assignees
            if 'assignees_at_grant' in patent:
                for assignee in patent['assignees_at_grant']:
                    normalized['assignees'].append({
                        'assignee_organization': assignee.get('assignee_organization', ''),
                        'assignee_country': assignee.get('assignee_country', '')
                    })

            # Normalize inventors
            if 'inventors_at_grant' in patent:
                for inventor in patent['inventors_at_grant']:
                    normalized['inventors'].append({
                        'inventor_first_name': inventor.get('inventor_name_first', ''),
                        'inventor_last_name': inventor.get('inventor_name_last', '')
                    })

            # Normalize CPCs
            if 'cpcs_at_grant' in patent:
                for cpc in patent['cpcs_at_grant']:
                    normalized['cpcs'].append({
                        'cpc_section': cpc.get('cpc_section', '')
                    })

            normalized_patents.append(normalized)

        return normalized_patents

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
            List of patent records
        """
        if keywords:
            query = {
                "_and": [
                    {"_text_any": {"assignee_organization": assignee}},
                    {
                        "_or": [
                            {"_text_any": {"patent_title": keywords}},
                            {"_text_any": {"patent_abstract": keywords}}
                        ]
                    }
                ]
            }
        else:
            query = {"_text_any": {"assignee_organization": assignee}}

        options = {
            "per_page": min(limit, 100),
            "page": 1,
            "sort": [{"patent_date": "desc"}]
        }

        result = self.search_patents(query, options=options)
        return result.get('patents', [])

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
            List of patent records
        """
        query = {"_begins": {"cpc_subgroup_id": cpc_code}}

        options = {
            "per_page": min(limit, 100),
            "page": 1,
            "sort": [{"patent_date": "desc"}]
        }

        result = self.search_patents(query, options=options)
        return result.get('patents', [])

    def get_patent_family(
        self,
        patent_number: str
    ) -> Dict[str, Any]:
        """
        Get patent citations and related patents

        Args:
            patent_number: Patent number (e.g., "10123456")

        Returns:
            Patent details with citations
        """
        query = {"_eq": {"patent_number": patent_number}}

        fields = [
            "patent_number",
            "patent_title",
            "patent_abstract",
            "patent_date",
            "assignee_organization",
            "cited_patent_number",
            "citedby_patent_number",
            "cited_patent_count",
            "citedby_patent_count"
        ]

        result = self.search_patents(query, fields=fields)
        patents = result.get('patents', [])

        return patents[0] if patents else {}

    def search_expiring_patents(
        self,
        keywords: str,
        years_from_now: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find patents expiring within specified years
        (US patents typically expire 20 years from filing date)

        Args:
            keywords: Search keywords
            years_from_now: Find patents expiring within N years

        Returns:
            List of expiring patents
        """
        # Patents expire 20 years from filing
        # For granted patents, use grant date as proxy
        end_date = datetime.now()
        # Look for patents granted 17-20 years ago (expiring in next 0-3 years)
        start_date = end_date - timedelta(days=365 * 20)
        cutoff_date = end_date - timedelta(days=365 * (20 - years_from_now))

        query = {
            "_and": [
                {
                    "_or": [
                        {"_text_any": {"patent_title": keywords}},
                        {"_text_any": {"patent_abstract": keywords}}
                    ]
                },
                {
                    "_gte": {"patent_date": start_date.strftime("%Y-%m-%d")}
                },
                {
                    "_lte": {"patent_date": cutoff_date.strftime("%Y-%m-%d")}
                }
            ]
        }

        options = {
            "per_page": 100,
            "page": 1,
            "sort": [{"patent_date": "asc"}]
        }

        result = self.search_patents(query, options=options)
        return result.get('patents', [])

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
        query = {
            "_or": [
                {"_text_any": {"patent_title": keywords}},
                {"_text_any": {"patent_abstract": keywords}}
            ]
        }

        fields = [
            "assignee_organization",
            "patent_number"
        ]

        options = {
            "per_page": 100,
            "page": 1
        }

        result = self.search_patents(query, fields=fields, options=options)
        patents = result.get('patents', [])

        # Count patents per assignee
        assignee_counts = {}
        for patent in patents:
            assignees = patent.get('assignees', [])
            for assignee in assignees:
                org = assignee.get('assignee_organization', 'Unknown')
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
