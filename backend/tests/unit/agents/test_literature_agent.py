"""
Unit Tests for Literature Agent
Tests all methods with mocked external APIs (PubMed, Groq, Gemini)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.literature_agent import LiteratureAgent
import xml.etree.ElementTree as ET


class TestLiteratureAgentInitialization:
    """Test Literature Agent initialization"""

    def test_agent_initializes_successfully(self):
        """Test that agent initializes with correct properties"""
        agent = LiteratureAgent()

        assert agent.name == "Literature Agent"
        assert agent.agent_id == "literature"
        assert agent.groq_api_key is not None  # May be empty string, but exists
        assert agent.gemini_api_key is not None
        assert agent.pubmed_base_url == "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def test_agent_has_required_methods(self):
        """Test that agent has all required methods"""
        agent = LiteratureAgent()

        assert hasattr(agent, 'extract_keywords')
        assert hasattr(agent, 'search_pubmed')
        assert hasattr(agent, 'generate_summary')
        assert hasattr(agent, 'process')
        assert callable(agent.process)


class TestKeywordExtraction:
    """Test keyword extraction with mocked Groq API"""

    @patch('requests.post')
    def test_extract_keywords_success(self, mock_post, mock_groq_literature_keywords):
        """Test successful keyword extraction from Groq"""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_groq_literature_keywords
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        agent = LiteratureAgent()
        keywords = agent.extract_keywords("What are the latest publications on GLP-1 for diabetes?")

        # Verify keywords were extracted
        assert isinstance(keywords, str)
        assert len(keywords) > 0
        assert "GLP-1" in keywords or "diabetes" in keywords

    @patch('requests.post')
    def test_extract_keywords_api_failure_fallback(self, mock_post):
        """Test fallback to deterministic extraction when Groq API fails"""
        # Simulate API failure
        mock_post.side_effect = Exception("API Error")

        agent = LiteratureAgent()
        original_query = "GLP-1 diabetes cardiovascular outcomes"
        keywords = agent.extract_keywords(original_query)

        # Should fall back to deterministic extraction
        assert isinstance(keywords, str)
        assert len(keywords) > 0

    def test_deterministic_fallback_extracts_keywords(self):
        """Test that deterministic fallback extracts meaningful keywords"""
        agent = LiteratureAgent()

        # Test basic keyword extraction
        query1 = "GLP-1 receptor agonists for type 2 diabetes treatment"
        keywords1 = agent._deterministic_keyword_extraction(query1)
        assert "GLP-1" in keywords1
        assert "diabetes" in keywords1

        # Test stopword removal
        query2 = "What are the best treatments for diabetes?"
        keywords2 = agent._deterministic_keyword_extraction(query2)
        assert "what" not in keywords2.lower()
        assert "are" not in keywords2.lower()
        assert "treatments" in keywords2 or "diabetes" in keywords2


class TestPubMedSearch:
    """Test PubMed search with mocked PubMed API"""

    @patch('requests.get')
    def test_search_pubmed_success(self, mock_get, mock_pubmed_search_response, mock_pubmed_fetch_xml):
        """Test successful PubMed search"""
        # Setup mock responses for esearch and efetch
        search_response = Mock()
        search_response.json.return_value = mock_pubmed_search_response
        search_response.raise_for_status = Mock()

        fetch_response = Mock()
        fetch_response.text = mock_pubmed_fetch_xml
        fetch_response.raise_for_status = Mock()

        # First call is esearch, second is efetch
        mock_get.side_effect = [search_response, fetch_response]

        agent = LiteratureAgent()
        publications = agent.search_pubmed("GLP-1 diabetes", max_results=10)

        # Verify publications were retrieved
        assert isinstance(publications, list)
        assert len(publications) == 2
        assert publications[0]['pmid'] == "38123456"
        assert "GLP-1" in publications[0]['title']
        assert publications[1]['pmid'] == "38234567"

    @patch('requests.get')
    def test_search_pubmed_no_results(self, mock_get):
        """Test PubMed search with no results"""
        # Setup mock response with no results
        search_response = Mock()
        search_response.json.return_value = {
            "esearchresult": {
                "count": "0",
                "retmax": "0",
                "idlist": []
            }
        }
        search_response.raise_for_status = Mock()
        mock_get.return_value = search_response

        agent = LiteratureAgent()
        publications = agent.search_pubmed("nonexistent query")

        # Should return empty list
        assert isinstance(publications, list)
        assert len(publications) == 0

    @patch('requests.get')
    def test_search_pubmed_api_failure(self, mock_get):
        """Test PubMed search handles API failures gracefully"""
        # Simulate API failure
        mock_get.side_effect = Exception("PubMed API Error")

        agent = LiteratureAgent()
        publications = agent.search_pubmed("GLP-1 diabetes")

        # Should return empty list on failure
        assert isinstance(publications, list)
        assert len(publications) == 0

    def test_parse_pubmed_xml_valid(self, mock_pubmed_fetch_xml):
        """Test XML parsing with valid PubMed response"""
        agent = LiteratureAgent()
        publications = agent._parse_pubmed_xml(mock_pubmed_fetch_xml)

        # Verify parsing results
        assert len(publications) == 2

        # Check first publication
        assert publications[0]['pmid'] == "38123456"
        assert "GLP-1 Receptor Agonists" in publications[0]['title']
        assert "Smith" in publications[0]['authors']
        assert publications[0]['journal'] == "Diabetes Care"
        assert publications[0]['year'] == "2024"
        assert len(publications[0]['abstract']) > 50

        # Check second publication
        assert publications[1]['pmid'] == "38234567"
        assert "Cardiovascular Outcomes" in publications[1]['title']
        assert "Johnson" in publications[1]['authors']
        assert publications[1]['year'] == "2023"

    def test_parse_pubmed_xml_malformed(self):
        """Test XML parsing with malformed XML"""
        agent = LiteratureAgent()

        # Test with invalid XML
        malformed_xml = "<Invalid>XML</NotClosed>"
        publications = agent._parse_pubmed_xml(malformed_xml)

        # Should return empty list on parse failure
        assert isinstance(publications, list)
        assert len(publications) == 0

    def test_parse_pubmed_xml_empty(self):
        """Test XML parsing with empty results"""
        agent = LiteratureAgent()

        empty_xml = '<?xml version="1.0" ?><PubmedArticleSet></PubmedArticleSet>'
        publications = agent._parse_pubmed_xml(empty_xml)

        assert isinstance(publications, list)
        assert len(publications) == 0


class TestSummaryGeneration:
    """Test summary generation with mocked LLM APIs"""

    @patch('requests.post')
    def test_generate_summary_with_gemini(self, mock_post, mock_gemini_literature_summary):
        """Test summary generation using Gemini"""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_gemini_literature_summary
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        agent = LiteratureAgent()
        publications = [
            {
                "pmid": "38123456",
                "title": "GLP-1 Study",
                "authors": "Smith J",
                "journal": "Diabetes Care",
                "year": "2024",
                "abstract": "GLP-1 abstract..."
            }
        ]

        summary = agent.generate_summary(publications, "GLP-1 diabetes")

        # Verify summary was generated
        assert isinstance(summary, str)
        assert len(summary) > 100
        assert "LITERATURE REVIEW" in summary.upper() or "OVERVIEW" in summary.upper()

    @patch('requests.post')
    def test_generate_summary_with_groq_fallback(self, mock_post):
        """Test summary generation falls back to Groq when Gemini fails"""
        # Setup mock responses: Gemini fails, Groq succeeds
        groq_response = Mock()
        groq_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "BIOMEDICAL LITERATURE REVIEW\n\n1. OVERVIEW\n\nThis review analyzes GLP-1 literature."
                }
            }]
        }
        groq_response.raise_for_status = Mock()

        # First call fails (Gemini), second succeeds (Groq)
        mock_post.side_effect = [Exception("Gemini Error"), groq_response]

        agent = LiteratureAgent()
        publications = [{"pmid": "123", "title": "Test", "authors": "Author", "journal": "Journal", "year": "2024", "abstract": "Abstract"}]
        summary = agent.generate_summary(publications, "GLP-1")

        # Should get a summary from Groq or structured fallback
        assert isinstance(summary, str)
        assert len(summary) > 50

    def test_generate_summary_structured_fallback(self):
        """Test structured fallback when all AI APIs fail"""
        agent = LiteratureAgent()
        # Disable API keys to force fallback
        agent.gemini_api_key = ""
        agent.groq_api_key = ""

        publications = [
            {
                "pmid": "38123456",
                "title": "GLP-1 Receptor Agonists Study",
                "authors": "Smith J, Jones M",
                "journal": "Diabetes Care",
                "year": "2024",
                "abstract": "This study evaluates GLP-1 agonists for diabetes treatment.",
                "publication_types": ["Journal Article", "Review"]
            },
            {
                "pmid": "38234567",
                "title": "Cardiovascular Outcomes",
                "authors": "Johnson E",
                "journal": "JAMA",
                "year": "2023",
                "abstract": "Meta-analysis of cardiovascular outcomes.",
                "publication_types": ["Meta-Analysis"]
            }
        ]

        summary = agent._generate_structured_fallback("GLP-1 diabetes", publications)

        # Verify structured summary was generated
        assert isinstance(summary, str)
        assert len(summary) > 200
        assert "BIOMEDICAL LITERATURE REVIEW" in summary
        assert "OVERVIEW" in summary
        assert "2" in summary  # Should mention 2 publications
        assert "PMID:38123456" in summary
        assert "Smith" in summary


class TestProcessMethod:
    """Test the main process() method with full integration"""

    @patch('requests.post')
    @patch('requests.get')
    def test_process_full_workflow(
        self,
        mock_get,
        mock_post,
        mock_groq_literature_keywords,
        mock_pubmed_search_response,
        mock_pubmed_fetch_xml,
        mock_gemini_literature_summary
    ):
        """Test complete workflow from query to result"""
        # Setup all mocks
        # Mock Groq for keyword extraction
        groq_response = Mock()
        groq_response.json.return_value = mock_groq_literature_keywords
        groq_response.raise_for_status = Mock()

        # Mock Gemini for summary
        gemini_response = Mock()
        gemini_response.json.return_value = mock_gemini_literature_summary
        gemini_response.raise_for_status = Mock()

        mock_post.side_effect = [groq_response, gemini_response]

        # Mock PubMed search and fetch
        search_response = Mock()
        search_response.json.return_value = mock_pubmed_search_response
        search_response.raise_for_status = Mock()

        fetch_response = Mock()
        fetch_response.text = mock_pubmed_fetch_xml
        fetch_response.raise_for_status = Mock()

        mock_get.side_effect = [search_response, fetch_response]

        # Execute full workflow
        agent = LiteratureAgent()
        result = agent.process("What are the latest GLP-1 studies for diabetes?")

        # Verify result structure
        assert isinstance(result, dict)
        assert result['agent_id'] == 'literature'
        assert 'query' in result
        assert 'keywords' in result
        assert 'publications' in result
        assert 'summary' in result
        assert 'comprehensive_summary' in result
        assert 'total_publications' in result
        assert 'references' in result

        # Verify publications
        assert isinstance(result['publications'], list)
        assert len(result['publications']) == 2
        assert result['total_publications'] == 2

        # Verify references have correct structure
        assert isinstance(result['references'], list)
        for ref in result['references']:
            assert 'id' in ref
            assert ref['id'].startswith('PMID:')
            assert 'title' in ref
            assert 'url' in ref
            assert 'agentId' in ref
            assert ref['agentId'] == 'literature'
            assert 'confidence' in ref

    @patch('requests.get')
    def test_process_handles_no_results(self, mock_get):
        """Test process() handles no search results gracefully"""
        # Mock empty search results
        search_response = Mock()
        search_response.json.return_value = {
            "esearchresult": {"count": "0", "idlist": []}
        }
        search_response.raise_for_status = Mock()
        mock_get.return_value = search_response

        agent = LiteratureAgent()
        result = agent.process("nonexistent query xyz123")

        # Should still return valid structure
        assert isinstance(result, dict)
        assert result['total_publications'] == 0
        assert len(result['publications']) == 0
        assert len(result['references']) == 0
        assert "no publications found" in result['summary'].lower()

    @patch('requests.get')
    def test_process_handles_api_failures(self, mock_get):
        """Test process() handles API failures gracefully"""
        # Simulate API failure
        mock_get.side_effect = Exception("Network Error")

        agent = LiteratureAgent()
        result = agent.process("GLP-1 diabetes")

        # Should return result with error indication
        assert isinstance(result, dict)
        assert result['total_publications'] == 0
        assert len(result['publications']) == 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_query_handling(self):
        """Test handling of empty queries"""
        agent = LiteratureAgent()

        # Empty string
        keywords = agent.extract_keywords("")
        assert isinstance(keywords, str)

        # Whitespace only
        keywords = agent.extract_keywords("   ")
        assert isinstance(keywords, str)

    def test_very_long_query(self):
        """Test handling of very long queries"""
        agent = LiteratureAgent()

        long_query = "GLP-1 " * 200  # Very long query
        keywords = agent.extract_keywords(long_query)

        # Should still extract keywords without crashing
        assert isinstance(keywords, str)
        assert len(keywords) > 0

    def test_special_characters_in_query(self):
        """Test handling of special characters"""
        agent = LiteratureAgent()

        query = "GLP-1 (receptor agonists) & diabetes [Type 2]"
        keywords = agent.extract_keywords(query)

        # Should handle special characters gracefully
        assert isinstance(keywords, str)
        assert "GLP-1" in keywords or "diabetes" in keywords

    def test_non_english_characters(self):
        """Test handling of non-English characters"""
        agent = LiteratureAgent()

        query = "GLP-1 diabetes 糖尿病"
        keywords = agent.extract_keywords(query)

        # Should not crash with non-English characters
        assert isinstance(keywords, str)

    def test_empty_publications_list_summary(self):
        """Test summary generation with empty publications list"""
        agent = LiteratureAgent()

        summary = agent.generate_summary([], "GLP-1")

        # Should return a valid message
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "no publications" in summary.lower()
