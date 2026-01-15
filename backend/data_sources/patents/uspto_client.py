"""
USPTO PatentsView API Client
Provides access to US patent data via the PatentsView API
https://patentsview.org/apis/purpose
"""

import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class USPTOClient:
    """
    Client for USPTO PatentsView API

    API Documentation: https://patentsview.org/apis/api-query-language
    No authentication required for basic queries
    Rate limit: 45 requests per minute
    """

    BASE_URL = "https://api.patentsview.org"

    # API endpoints
    PATENTS_ENDPOINT = f"{BASE_URL}/patents/query"
    INVENTORS_ENDPOINT = f"{BASE_URL}/inventors/query"
    ASSIGNEES_ENDPOINT = f"{BASE_URL}/assignees/query"
    LOCATIONS_ENDPOINT = f"{BASE_URL}/locations/query"

    def __init__(self):
        """Initialize USPTO PatentsView client"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MAESTRO-Patent-Intelligence-Agent/1.0'
        })
        self.rate_limit_delay = 1.4  # ~43 requests per minute to stay under limit
        self.last_request_time = 0
        logger.info("USPTO PatentsView client initialized")

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
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Search patents using PatentsView query language

        Args:
            query: Query in PatentsView format (e.g., {"_text_any": {"patent_abstract": "GLP-1"}})
            fields: List of fields to return
            options: Query options (per_page, page, sort)

        Returns:
            API response with patent data
        """
        if fields is None:
            fields = [
                "patent_number",
                "patent_title",
                "patent_abstract",
                "patent_date",
                "assignee_organization",
                "assignee_country",
                "inventor_first_name",
                "inventor_last_name",
                "ipc_section",
                "cpc_section",
                "cited_patent_count",
                "citedby_patent_count",
                "patent_kind",
                "patent_type"
            ]

        if options is None:
            options = {
                "per_page": 100,
                "page": 1,
                "sort": [{"citedby_patent_count": "desc"}]
            }

        payload = {
            "q": query,
            "f": fields,
            "o": options
        }

        self._rate_limit()

        try:
            logger.info(f"Searching USPTO patents with query: {query}")
            response = self.session.post(
                self.PATENTS_ENDPOINT,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            patent_count = data.get('count', 0)
            logger.info(f"Found {patent_count} patents")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"USPTO API request failed: {e}")
            raise

    def search_by_keywords(
        self,
        keywords: str,
        limit: int = 100,
        years_back: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search patents by keywords in title or abstract

        Args:
            keywords: Search keywords
            limit: Maximum number of results
            years_back: Search patents from last N years

        Returns:
            List of patent records
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years_back)

        # Build query using PatentsView query language
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

        options = {
            "per_page": min(limit, 100),
            "page": 1,
            "sort": [{"patent_date": "desc"}]
        }

        result = self.search_patents(query, options=options)
        return result.get('patents', [])

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
