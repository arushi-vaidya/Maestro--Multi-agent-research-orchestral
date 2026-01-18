"""
Unit Tests for Patent Agent
Tests all methods with mocked external APIs (USPTO, Groq, Gemini)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.patent_agent import PatentAgent


class TestPatentAgentInitialization:
    """Test Patent Agent initialization"""

    def test_agent_initializes_successfully(self):
        """Test that agent initializes with correct properties"""
        agent = PatentAgent(use_web_search=False)  # Disable web search for unit tests

        assert agent.name == "Patent Intelligence Agent"
        assert agent.agent_id == "patent"
        assert hasattr(agent, 'groq_api_key')
        assert hasattr(agent, 'gemini_api_key')

    def test_agent_has_required_methods(self):
        """Test that agent has all required methods"""
        agent = PatentAgent(use_web_search=False)

        assert hasattr(agent, 'extract_keywords')
        assert hasattr(agent, 'search_patents')
        assert hasattr(agent, 'analyze_patent_landscape')
        assert hasattr(agent, 'assess_freedom_to_operate')
        assert hasattr(agent, 'analyze_expiring_patents')
        assert hasattr(agent, 'identify_white_space')
        assert hasattr(agent, 'assess_litigation_risk')
        assert hasattr(agent, 'process')
        assert callable(agent.process)

    def test_agent_has_pharma_cpc_codes(self):
        """Test that agent has pharmaceutical CPC classification codes"""
        agent = PatentAgent(use_web_search=False)

        assert hasattr(agent, 'pharma_cpc_codes')
        assert isinstance(agent.pharma_cpc_codes, dict)
        assert 'A61K' in agent.pharma_cpc_codes  # Pharmaceutical preparations
        assert 'C07D' in agent.pharma_cpc_codes  # Heterocyclic compounds


class TestKeywordExtraction:
    """Test patent keyword extraction"""

    @patch('requests.post')
    def test_extract_keywords_success(self, mock_post):
        """Test successful keyword extraction"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "GLP-1, diabetes treatment"
                }
            }]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        agent = PatentAgent(use_web_search=False)
        keywords = agent.extract_keywords("What is the patent landscape for GLP-1 diabetes drugs?")

        assert isinstance(keywords, str)
        assert len(keywords) > 0
        assert "GLP-1" in keywords or "diabetes" in keywords

    @patch('requests.post')
    def test_extract_keywords_api_failure_fallback(self, mock_post):
        """Test fallback when Groq API fails"""
        mock_post.side_effect = Exception("API Error")

        agent = PatentAgent(use_web_search=False)
        keywords = agent.extract_keywords("GLP-1 patent landscape")

        # Should fall back to sanitized query
        assert isinstance(keywords, str)
        assert len(keywords) > 0

    def test_sanitize_patent_keywords_removes_patent_numbers(self):
        """Test that patent numbers are removed from keywords"""
        agent = PatentAgent(use_web_search=False)

        # Test patent number removal
        assert "US" not in agent._sanitize_patent_keywords("GLP-1 US 11234567")
        assert agent._sanitize_patent_keywords("GLP-1 US11234567") == "GLP-1"

    def test_sanitize_patent_keywords_removes_formatting(self):
        """Test that formatting is removed"""
        agent = PatentAgent(use_web_search=False)

        assert agent._sanitize_patent_keywords("- GLP-1 patents") == "GLP-1 patents"
        assert agent._sanitize_patent_keywords("1. GLP-1 patents") == "GLP-1 patents"
        assert agent._sanitize_patent_keywords("**GLP-1** patents") == "GLP-1 patents"

    def test_sanitize_patent_keywords_limits_length(self):
        """Test keyword length limiting"""
        agent = PatentAgent(use_web_search=False)

        long_keywords = "GLP-1 " * 30
        sanitized = agent._sanitize_patent_keywords(long_keywords)

        assert len(sanitized) <= 100


class TestPatentSearch:
    """Test patent search with mocked USPTO API"""

    def test_search_patents_no_uspto_client(self):
        """Test behavior when USPTO client is not available"""
        with patch('agents.patent_agent.USPTO_AVAILABLE', False):
            agent = PatentAgent(use_web_search=False)
            patents = agent.search_patents("GLP-1", limit=10)

            assert patents == []

    @patch('agents.patent_agent.USPTOClient')
    def test_search_patents_success(self, mock_uspto_class, mock_uspto_patents_response):
        """Test successful patent search"""
        # Mock USPTO client
        mock_client = Mock()
        mock_client.search_by_keywords.return_value = mock_uspto_patents_response
        mock_uspto_class.return_value = mock_client

        with patch('agents.patent_agent.USPTO_AVAILABLE', True):
            agent = PatentAgent(use_web_search=False)
            agent.uspto_client = mock_client

            patents = agent.search_patents("GLP-1", limit=100)

            assert isinstance(patents, list)
            assert len(patents) == 2
            assert patents[0]["patent_number"] == "US11234567B2"
            assert "GLP-1" in patents[0]["patent_title"]

            # Verify USPTO client was called correctly
            mock_client.search_by_keywords.assert_called_once_with(
                keywords="GLP-1",
                limit=100,
                years_back=15
            )

    @patch('agents.patent_agent.USPTOClient')
    def test_search_patents_api_failure(self, mock_uspto_class):
        """Test handling of USPTO API failure"""
        mock_client = Mock()
        mock_client.search_by_keywords.side_effect = Exception("USPTO API Error")
        mock_uspto_class.return_value = mock_client

        with patch('agents.patent_agent.USPTO_AVAILABLE', True):
            agent = PatentAgent(use_web_search=False)
            agent.uspto_client = mock_client

            patents = agent.search_patents("GLP-1")

            assert patents == []


class TestPatentLandscapeAnalysis:
    """Test patent landscape analysis"""

    def test_analyze_patent_landscape_with_data(self, mock_uspto_patents_response):
        """Test landscape analysis with patent data"""
        agent = PatentAgent(use_web_search=False)
        landscape = agent.analyze_patent_landscape(
            mock_uspto_patents_response,
            "GLP-1"
        )

        assert isinstance(landscape, dict)
        assert "total_patents" in landscape
        assert "active_patents" in landscape
        assert "key_players" in landscape
        assert "filing_trends" in landscape
        assert "classification_distribution" in landscape

        assert landscape["total_patents"] == 2
        assert len(landscape["key_players"]) > 0
        assert landscape["key_players"][0]["organization"] in ["Pharma Corp", "BioTech Inc"]

    def test_analyze_patent_landscape_empty_data(self):
        """Test landscape analysis with no patents"""
        agent = PatentAgent(use_web_search=False)
        landscape = agent.analyze_patent_landscape([], "GLP-1")

        assert landscape["total_patents"] == 0
        assert landscape["active_patents"] == 0
        assert landscape["key_players"] == []


class TestFTOAssessment:
    """Test Freedom-to-Operate assessment"""

    def test_assess_fto_with_patents(self, mock_uspto_patents_response):
        """Test FTO assessment with patent data"""
        agent = PatentAgent(use_web_search=False)
        fto = agent.assess_freedom_to_operate(
            mock_uspto_patents_response,
            "GLP-1"
        )

        assert isinstance(fto, dict)
        assert "risk_level" in fto
        assert "analysis" in fto
        assert "active_blocking_patents" in fto
        assert "dominant_players" in fto
        assert "recommendations" in fto

        assert fto["risk_level"] in ["Low", "Medium", "High", "Unknown"]
        assert isinstance(fto["recommendations"], list)

    def test_assess_fto_no_patents(self):
        """Test FTO assessment with no patents"""
        agent = PatentAgent(use_web_search=False)
        fto = agent.assess_freedom_to_operate([], "GLP-1")

        assert fto["risk_level"] == "Unknown"
        assert "No patent data" in fto["analysis"]

    def test_assess_fto_high_risk_scenario(self):
        """Test FTO assessment identifies high risk"""
        agent = PatentAgent(use_web_search=False)

        # Create many recent patents (high risk scenario)
        many_patents = []
        for i in range(60):
            many_patents.append({
                "patent_number": f"US{10000000 + i}",
                "patent_date": "2022-01-01",
                "assignees": [{"assignee_organization": "Pharma Corp"}]
            })

        fto = agent.assess_freedom_to_operate(many_patents, "GLP-1")

        assert fto["risk_level"] == "High"


class TestExpiringPatents:
    """Test expiring patent analysis"""

    @patch('agents.patent_agent.USPTOClient')
    def test_analyze_expiring_patents_success(self, mock_uspto_class):
        """Test expiring patent analysis"""
        mock_client = Mock()
        mock_client.search_expiring_patents.return_value = [
            {
                "patent_number": "US10000000",
                "patent_title": "Expiring GLP-1 Patent",
                "patent_date": "2007-01-01",  # Will expire soon
                "assignees": [{"assignee_organization": "Pharma Corp"}]
            }
        ]

        with patch('agents.patent_agent.USPTO_AVAILABLE', True):
            agent = PatentAgent(use_web_search=False)
            agent.uspto_client = mock_client

            result = agent.analyze_expiring_patents("GLP-1", years_from_now=3)

            assert isinstance(result, dict)
            assert "expiring_patents" in result
            assert "count" in result
            assert "by_assignee" in result
            assert result["count"] == 1

    def test_analyze_expiring_patents_no_uspto(self):
        """Test behavior when USPTO client unavailable"""
        agent = PatentAgent(use_web_search=False)
        agent.uspto_client = None

        result = agent.analyze_expiring_patents("GLP-1")

        assert result["expiring_patents"] == []
        assert result["count"] == 0


class TestWhiteSpaceIdentification:
    """Test white space opportunity identification"""

    def test_identify_white_space_with_patents(self, mock_uspto_patents_response):
        """Test white space identification"""
        agent = PatentAgent(use_web_search=False)
        white_space = agent.identify_white_space(
            mock_uspto_patents_response,
            "GLP-1"
        )

        assert isinstance(white_space, list)
        assert len(white_space) <= 5  # Returns top 5
        # Should return areas with low patent coverage
        for area in white_space:
            assert isinstance(area, str)
            assert len(area) > 0

    def test_identify_white_space_empty_patents(self):
        """Test white space with no patents"""
        agent = PatentAgent(use_web_search=False)
        white_space = agent.identify_white_space([], "GLP-1")

        # With no patents, most areas should be white space
        assert isinstance(white_space, list)


class TestLitigationRisk:
    """Test litigation risk assessment"""

    def test_assess_litigation_risk_high(self):
        """Test high litigation risk detection"""
        agent = PatentAgent(use_web_search=False)

        # High citation patents from many assignees
        high_risk_patents = []
        for i in range(20):
            high_risk_patents.append({
                "patent_number": f"US{10000000 + i}",
                "citedby_patent_count": 25,  # High citations
                "assignees": [{"assignee_organization": f"Company{i}"}]
            })

        risk = agent.assess_litigation_risk(high_risk_patents)
        assert risk == "High"

    def test_assess_litigation_risk_low(self):
        """Test low litigation risk detection"""
        agent = PatentAgent(use_web_search=False)

        low_risk_patents = [
            {
                "patent_number": "US10000000",
                "citedby_patent_count": 2,
                "assignees": [{"assignee_organization": "Company1"}]
            }
        ]

        risk = agent.assess_litigation_risk(low_risk_patents)
        assert risk == "Low"

    def test_assess_litigation_risk_no_patents(self):
        """Test litigation risk with no patents"""
        agent = PatentAgent(use_web_search=False)
        risk = agent.assess_litigation_risk([])
        assert risk == "Unknown"


class TestComprehensiveSummary:
    """Test comprehensive summary generation"""

    @patch('requests.post')
    def test_generate_summary_with_gemini(self, mock_post, mock_uspto_patents_response):
        """Test summary generation with Gemini"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "PATENT INTELLIGENCE REPORT\n\n1. EXECUTIVE SUMMARY\n\nPatent analysis for GLP-1..."
                    }]
                }
            }]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        agent = PatentAgent(use_web_search=False)
        landscape = {"total_patents": 2, "active_patents": 2, "key_players": []}
        fto = {"risk_level": "Medium", "analysis": "Moderate coverage"}
        expiring = {"count": 0}
        white_space = ["Novel formulations"]
        litigation_risk = "Medium"

        summary = agent.generate_comprehensive_summary(
            mock_uspto_patents_response,
            landscape, fto, expiring, white_space, litigation_risk,
            "GLP-1"
        )

        assert isinstance(summary, str)
        assert len(summary) > 100
        assert "PATENT" in summary or "patent" in summary.lower()

    def test_generate_summary_structured_fallback(self):
        """Test structured fallback summary"""
        agent = PatentAgent(use_web_search=False)
        agent.gemini_api_key = ""
        agent.groq_api_key = ""

        landscape = {"total_patents": 2, "active_patents": 2, "key_players": []}
        fto = {"risk_level": "Medium", "analysis": "Moderate", "recommendations": ["Review FTO"]}
        expiring = {"count": 1}
        white_space = ["Novel delivery"]
        litigation_risk = "Medium"

        summary = agent._generate_structured_fallback(
            "GLP-1", landscape, fto, expiring, white_space, litigation_risk
        )

        assert isinstance(summary, str)
        assert "PATENT INTELLIGENCE REPORT" in summary
        assert "EXECUTIVE SUMMARY" in summary
        assert "Medium" in summary


class TestProcessMethod:
    """Test main process() method"""

    @patch('agents.patent_agent.USPTOClient')
    @patch('requests.post')
    def test_process_full_flow(self, mock_post, mock_uspto_class, mock_uspto_patents_response):
        """Test complete process flow"""
        # Mock keyword extraction
        keyword_response = Mock()
        keyword_response.json.return_value = {
            "choices": [{"message": {"content": "GLP-1"}}]
        }
        keyword_response.raise_for_status = Mock()

        # Mock summary generation
        summary_response = Mock()
        summary_response.json.return_value = {
            "candidates": [{
                "content": {"parts": [{"text": "Patent intelligence report..."}]}
            }]
        }
        summary_response.raise_for_status = Mock()

        mock_post.side_effect = [keyword_response, summary_response]

        # Mock USPTO client
        mock_client = Mock()
        mock_client.search_by_keywords.return_value = mock_uspto_patents_response
        mock_client.search_expiring_patents.return_value = []

        with patch('agents.patent_agent.USPTO_AVAILABLE', True):
            agent = PatentAgent(use_web_search=False)
            agent.uspto_client = mock_client

            result = agent.process("What is the GLP-1 patent landscape?")

            # Verify output structure
            assert isinstance(result, dict)
            assert "summary" in result
            assert "comprehensive_summary" in result
            assert "patents" in result
            assert "landscape" in result
            assert "fto_assessment" in result
            assert "confidence_score" in result

            # Verify FTO assessment exists
            assert result["fto_assessment"]["risk_level"] in ["Low", "Medium", "High"]

    @patch('agents.patent_agent.USPTOClient')
    def test_process_no_patents_found(self, mock_uspto_class):
        """Test process when no patents are found"""
        mock_client = Mock()
        mock_client.search_by_keywords.return_value = []

        with patch('agents.patent_agent.USPTO_AVAILABLE', True):
            agent = PatentAgent(use_web_search=False)
            agent.uspto_client = mock_client

            result = agent.process("NonexistentDrug12345")

            assert isinstance(result, dict)
            assert result["patents"] == []
            assert result["fto_assessment"]["risk_level"] == "Unknown"
            assert result["confidence_score"] == 0.0

    @patch('agents.patent_agent.USPTOClient')
    def test_process_handles_exceptions(self, mock_uspto_class):
        """Test that process handles exceptions gracefully"""
        mock_client = Mock()
        mock_client.search_by_keywords.side_effect = Exception("USPTO Error")

        with patch('agents.patent_agent.USPTO_AVAILABLE', True):
            agent = PatentAgent(use_web_search=False)
            agent.uspto_client = mock_client

            result = agent.process("GLP-1")

            # Should return error structure, not crash
            assert isinstance(result, dict)
            assert "summary" in result
            assert "failed" in result["summary"].lower() or "error" in result["summary"].lower()


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_agent_works_without_api_keys(self):
        """Test agent initialization without API keys"""
        with patch.dict('os.environ', {}, clear=True):
            agent = PatentAgent(use_web_search=False)
            assert agent is not None

    def test_agent_without_uspto_client(self):
        """Test agent works without USPTO client"""
        with patch('agents.patent_agent.USPTO_AVAILABLE', False):
            agent = PatentAgent(use_web_search=False)
            assert agent.uspto_client is None

            # Should still be able to call methods
            patents = agent.search_patents("GLP-1")
            assert patents == []
