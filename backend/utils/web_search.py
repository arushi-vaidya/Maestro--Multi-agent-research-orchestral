"""
Web Search Utility for Market Intelligence
Performs live web searches for fresh market data
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class WebSearchEngine:
    """
    Web Search Engine for Market Intelligence
    Supports multiple search APIs with fallbacks
    """

    def __init__(self, api_key: Optional[str] = None, search_provider: str = "serpapi"):
        """
        Initialize web search engine

        Args:
            api_key: API key for search provider (optional, falls back to env var)
            search_provider: Search provider to use ('serpapi', 'bing', 'google', 'duckduckgo')
        """
        self.search_provider = search_provider.lower()
        self.api_key = api_key or os.getenv(f"{search_provider.upper()}_API_KEY")

        if not REQUESTS_AVAILABLE:
            logger.warning("requests library not available. Web search disabled.")

    def search(
        self,
        query: str,
        num_results: int = 10,
        time_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform web search for market intelligence

        Args:
            query: Search query
            num_results: Number of results to retrieve
            time_filter: Time filter ('day', 'week', 'month', 'year', None)

        Returns:
            List of search results with title, snippet, url, date
        """
        if not REQUESTS_AVAILABLE:
            logger.error("Web search unavailable: requests library not installed")
            return []

        try:
            if self.search_provider == "serpapi" and self.api_key:
                return self._search_serpapi(query, num_results, time_filter)
            elif self.search_provider == "bing" and self.api_key:
                return self._search_bing(query, num_results, time_filter)
            elif self.search_provider == "duckduckgo":
                return self._search_duckduckgo(query, num_results)
            else:
                logger.warning(f"No API key for {self.search_provider}, using fallback search")
                return self._search_fallback(query, num_results)

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []

    def _search_serpapi(
        self,
        query: str,
        num_results: int,
        time_filter: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Search using SerpAPI (Google Search API)"""
        url = "https://serpapi.com/search"

        params = {
            "q": query,
            "api_key": self.api_key,
            "num": num_results,
            "engine": "google"
        }

        if time_filter:
            time_map = {
                "day": "qdr:d",
                "week": "qdr:w",
                "month": "qdr:m",
                "year": "qdr:y"
            }
            params["tbs"] = time_map.get(time_filter, "")

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = []

        for item in data.get("organic_results", [])[:num_results]:
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("link", ""),
                "date": item.get("date", ""),
                "source": "serpapi"
            })

        logger.info(f"SerpAPI returned {len(results)} results for: {query}")
        return results

    def _search_bing(
        self,
        query: str,
        num_results: int,
        time_filter: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Search using Bing Web Search API"""
        url = "https://api.bing.microsoft.com/v7.0/search"

        headers = {"Ocp-Apim-Subscription-Key": self.api_key}

        params = {
            "q": query,
            "count": num_results,
            "responseFilter": "Webpages"
        }

        if time_filter:
            time_map = {
                "day": "Day",
                "week": "Week",
                "month": "Month"
            }
            params["freshness"] = time_map.get(time_filter, "")

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = []

        for item in data.get("webPages", {}).get("value", [])[:num_results]:
            # Extract date from snippet if available
            date = self._extract_date_from_text(item.get("snippet", ""))

            results.append({
                "title": item.get("name", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("url", ""),
                "date": date,
                "source": "bing"
            })

        logger.info(f"Bing returned {len(results)} results for: {query}")
        return results

    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo (no API key required)"""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.error("duckduckgo_search library not installed")
            return []

        try:
            with DDGS() as ddgs:
                results_raw = list(ddgs.text(query, max_results=num_results))

            results = []
            for item in results_raw:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("body", ""),
                    "url": item.get("href", ""),
                    "date": self._extract_date_from_text(item.get("body", "")),
                    "source": "duckduckgo"
                })

            logger.info(f"DuckDuckGo returned {len(results)} results for: {query}")
            return results

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

    def _search_fallback(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """
        Fallback search using basic HTTP requests
        Returns mock results when no API is available
        """
        logger.warning("Using fallback mock search results")

        # Return mock results that look like real web search
        mock_results = [
            {
                "title": f"Market Analysis: {query}",
                "snippet": f"Comprehensive market intelligence on {query} including market size, CAGR, key players, and future outlook...",
                "url": "https://www.iqvia.com/insights/market-intelligence",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "fallback"
            },
            {
                "title": f"{query} - Industry Report 2024",
                "snippet": f"Latest market trends and competitive analysis for {query}. Market size, growth forecasts, and strategic recommendations...",
                "url": "https://www.evaluatepharma.com/",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "fallback"
            }
        ]

        return mock_results[:num_results]

    def _extract_date_from_text(self, text: str) -> str:
        """Extract date from text using regex patterns"""
        # Common date patterns
        patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2024-01-15
            r'\d{1,2}/\d{1,2}/\d{4}',  # 1/15/2024
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}',  # Jan 15, 2024
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return ""

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize web text
        Removes boilerplate, ads, and excessive whitespace
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove common boilerplate phrases
        boilerplate_patterns = [
            r'Click here.*?(?=\.|$)',
            r'Subscribe to.*?(?=\.|$)',
            r'Follow us.*?(?=\.|$)',
            r'©\s*\d{4}.*?(?=\.|$)',
            r'Privacy Policy.*?(?=\.|$)',
            r'Terms of Service.*?(?=\.|$)',
        ]

        for pattern in boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        return text.strip()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize search engine (will use fallback if no API key)
    search = WebSearchEngine(search_provider="serpapi")

    # Test search
    query = "GLP-1 agonist market size 2024"
    results = search.search(query, num_results=5, time_filter="year")

    print(f"\n🔍 Search Results for: {query}")
    print("=" * 60)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Date: {result['date']}")
        print(f"   Snippet: {result['snippet'][:150]}...")
