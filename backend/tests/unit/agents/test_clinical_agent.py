"""
Unit Tests for Clinical Agent
Tests all methods with mocked external APIs (ClinicalTrials.gov, Groq, Gemini)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.clinical_agent import ClinicalAgent


class TestClinicalAgentInitialization:
    """Test Clinical Agent initialization"""

    def test_agent_initializes_successfully(self):
        """Test that agent initializes with correct properties"""
        agent = ClinicalAgent()

        assert agent.name == "Clinical Trials Agent"
        assert agent.agent_id == "clinical"
        assert agent.groq_api_key is not None  # May be empty string, but exists
        assert agent.gemini_api_key is not None

    def test_agent_has_required_methods(self):
        """Test that agent has all required methods"""
        agent = ClinicalAgent()

        assert hasattr(agent, 'extract_keywords')
        assert hasattr(agent, 'search_trials')
        assert hasattr(agent, 'get_trial_details')
        assert hasattr(agent, 'generate_comprehensive_summary')
        assert hasattr(agent, 'process')
        assert callable(agent.process)


class TestKeywordExtraction:
    """Test keyword extraction with mocked Groq API"""

    @patch('requests.post')
    def test_extract_keywords_success(self, mock_post, mock_groq_keyword_response):
        """Test successful keyword extraction from Groq"""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_groq_keyword_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        agent = ClinicalAgent()
        keywords = agent.extract_keywords("What are the latest GLP-1 trials for diabetes?")

        # Verify keywords were extracted and sanitized
        assert isinstance(keywords, str)
        assert len(keywords) > 0
        # Should contain clean keywords, no bullets or numbers
        assert not keywords.startswith('-')
        assert not keywords.startswith('*')

    @patch('requests.post')
    def test_extract_keywords_api_failure_fallback(self, mock_post):
        """Test fallback to original query when Groq API fails"""
        # Simulate API failure
        mock_post.side_effect = Exception("API Error")

        agent = ClinicalAgent()
        original_query = "GLP-1 diabetes trials"
        keywords = agent.extract_keywords(original_query)

        # Should fall back to sanitized original query
        assert isinstance(keywords, str)
        assert len(keywords) > 0

    def test_sanitize_keywords_removes_formatting(self):
        """Test that sanitize_keywords removes formatting"""
        agent = ClinicalAgent()

        # Test bullet point removal
        assert agent._sanitize_keywords("- GLP-1 diabetes") == "GLP-1 diabetes"
        assert agent._sanitize_keywords("* GLP-1 diabetes") == "GLP-1 diabetes"

        # Test numbered list removal
        assert agent._sanitize_keywords("1. GLP-1 diabetes") == "GLP-1 diabetes"

        # Test markdown removal
        assert agent._sanitize_keywords("**GLP-1** diabetes") == "GLP-1 diabetes"

        # Test multiline handling (keeps first line only)
        multi = "GLP-1 diabetes\nType 2 diabetes\nPhase 3"
        assert "\n" not in agent._sanitize_keywords(multi)

    def test_sanitize_keywords_limits_length(self):
        """Test that overly long keywords are truncated"""
        agent = ClinicalAgent()

        long_keywords = "GLP-1 " * 50  # Very long string
        sanitized = agent._sanitize_keywords(long_keywords)

        assert len(sanitized) <= 200


class TestTrialSearch:
    """Test clinical trial search with mocked ClinicalTrials.gov API"""

    @patch('requests.get')
    def test_search_trials_success(self, mock_get, mock_clinical_trials_response):
        """Test successful trial search"""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_clinical_trials_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        agent = ClinicalAgent()
        result = agent.search_trials("GLP-1 diabetes", page_size=100)

        # Verify response structure
        assert isinstance(result, dict)
        assert "studies" in result
        assert "totalCount" in result
        assert len(result["studies"]) == 2
        assert result["totalCount"] == 2

        # Verify API was called with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "clinicaltrials.gov" in call_args[0][0]

    @patch('requests.get')
    def test_search_trials_api_failure(self, mock_get):
        """Test that API failure returns empty structure"""
        # Simulate API failure
        mock_get.side_effect = Exception("Network Error")

        agent = ClinicalAgent()
        result = agent.search_trials("GLP-1 diabetes")

        # Should return empty structure, not crash
        assert isinstance(result, dict)
        assert result["studies"] == []
        assert result["totalCount"] == 0

    @patch('requests.get')
    def test_search_trials_empty_results(self, mock_get):
        """Test handling of empty search results"""
        # Setup mock with empty results
        mock_response = Mock()
        mock_response.json.return_value = {"studies": [], "totalCount": 0}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        agent = ClinicalAgent()
        result = agent.search_trials("NonexistentDrug12345")

        assert result["studies"] == []
        assert result["totalCount"] == 0


class TestSummaryGeneration:
    """Test comprehensive summary generation with mocked LLM APIs"""

    @patch('requests.post')
    def test_generate_summary_with_gemini(self, mock_post,
                                          mock_clinical_trials_response,
                                          mock_gemini_summary_response):
        """Test summary generation using Gemini"""
        # Setup mock Gemini response
        mock_response = Mock()
        mock_response.json.return_value = mock_gemini_summary_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        agent = ClinicalAgent()
        # Set API key so agent tries Gemini
        agent.gemini_api_key = "fake_gemini_key_for_testing"
        summary = agent.generate_comprehensive_summary(
            mock_clinical_trials_response,
            "GLP-1 diabetes"
        )

        # Verify summary was generated
        assert isinstance(summary, str)
        assert len(summary) > 100  # Should be comprehensive
        assert "CLINICAL TRIALS ANALYSIS" in summary or "clinical" in summary.lower()

        # Verify Gemini API was called
        mock_post.assert_called()
        call_args = mock_post.call_args[0][0]
        assert "generativelanguage.googleapis.com" in call_args

    @patch('requests.post')
    def test_generate_summary_fallback_to_groq(self, mock_post,
                                                mock_clinical_trials_response):
        """Test fallback to Groq when Gemini fails"""
        # First call (Gemini) fails, second call (Groq) succeeds
        gemini_fail = Mock()
        gemini_fail.side_effect = Exception("Gemini API Error")

        groq_success = Mock()
        groq_response = Mock()
        groq_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "COMPREHENSIVE CLINICAL TRIALS ANALYSIS\n\nAnalysis content here."
                }
            }]
        }
        groq_response.raise_for_status = Mock()

        # First call fails (Gemini), second succeeds (Groq)
        mock_post.side_effect = [Exception("Gemini Error"), groq_response]

        agent = ClinicalAgent()
        summary = agent.generate_comprehensive_summary(
            mock_clinical_trials_response,
            "GLP-1 diabetes"
        )

        # Should get a summary from Groq fallback or structured fallback
        assert isinstance(summary, str)
        assert len(summary) > 50

    def test_generate_summary_structured_fallback(self, mock_clinical_trials_response):
        """Test structured fallback when all AI APIs fail"""
        agent = ClinicalAgent()
        # Temporarily disable API keys to force fallback
        agent.gemini_api_key = ""
        agent.groq_api_key = ""

        summary = agent._generate_structured_fallback(
            "GLP-1 diabetes",
            mock_clinical_trials_response
        )

        # Verify structured summary was generated
        assert isinstance(summary, str)
        assert len(summary) > 200
        assert "CLINICAL TRIALS ANALYSIS" in summary
        assert "OVERVIEW" in summary
        assert "2" in summary  # Should mention 2 trials

    def test_format_summary_removes_markdown(self):
        """Test that markdown formatting is removed"""
        agent = ClinicalAgent()

        markdown_text = "## Header\n**Bold** text with *italics* and `code`"
        formatted = agent._format_summary(markdown_text)

        assert "##" not in formatted
        assert "**" not in formatted
        assert "*" not in formatted
        assert "`" not in formatted


class TestProcessMethod:
    """Test the main process() method with full mocked flow"""

    @patch('requests.get')
    @patch('requests.post')
    def test_process_full_flow(self, mock_post, mock_get,
                               mock_groq_keyword_response,
                               mock_clinical_trials_response,
                               mock_gemini_summary_response):
        """Test complete process flow with all mocks"""
        # Setup mocks
        # 1. Keyword extraction (Groq)
        groq_response = Mock()
        groq_response.json.return_value = mock_groq_keyword_response
        groq_response.raise_for_status = Mock()

        # 2. Summary generation (Gemini)
        gemini_response = Mock()
        gemini_response.json.return_value = mock_gemini_summary_response
        gemini_response.raise_for_status = Mock()

        mock_post.side_effect = [groq_response, gemini_response]

        # 3. Trial search (ClinicalTrials.gov)
        ct_response = Mock()
        ct_response.json.return_value = mock_clinical_trials_response
        ct_response.raise_for_status = Mock()
        mock_get.return_value = ct_response

        # Execute
        agent = ClinicalAgent()
        result = agent.process("What are the latest GLP-1 trials?")

        # Verify output structure
        assert isinstance(result, dict)
        assert "summary" in result
        assert "comprehensive_summary" in result
        assert "trials" in result
        assert "raw" in result

        # Verify content
        assert len(result["trials"]) == 2
        assert result["trials"][0]["nct_id"] == "NCT12345678"
        assert "GLP-1" in result["summary"] or "trial" in result["summary"].lower()

    @patch('requests.get')
    @patch('requests.post')
    def test_process_handles_api_failures_gracefully(self, mock_post, mock_get):
        """Test that process handles API failures without crashing"""
        # All APIs fail
        mock_post.side_effect = Exception("API Error")
        mock_get.side_effect = Exception("API Error")

        agent = ClinicalAgent()
        result = agent.process("GLP-1 trials")

        # Should still return valid structure
        assert isinstance(result, dict)
        assert "summary" in result
        assert "trials" in result
        # Trials should be empty due to API failure
        assert len(result["trials"]) == 0


class TestGetTrialDetails:
    """Test individual trial details retrieval"""

    @patch('requests.get')
    def test_get_trial_details_success(self, mock_get):
        """Test successful trial details retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT12345678",
                    "briefTitle": "GLP-1 Phase 3 Trial"
                },
                "descriptionModule": {
                    "briefSummary": "This is a comprehensive trial summary."
                }
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        agent = ClinicalAgent()
        details = agent.get_trial_details("NCT12345678")

        assert isinstance(details, dict)
        assert "protocolSection" in details

    @patch('requests.get')
    def test_get_trial_summary(self, mock_get):
        """Test get_trial_summary method"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT12345678",
                    "briefTitle": "GLP-1 Phase 3 Trial"
                },
                "descriptionModule": {
                    "briefSummary": "Trial summary text."
                }
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        agent = ClinicalAgent()
        summary = agent.get_trial_summary("NCT12345678")

        assert summary["nct_id"] == "NCT12345678"
        assert summary["title"] == "GLP-1 Phase 3 Trial"
        assert summary["summary"] == "Trial summary text."


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_agent_works_without_api_keys(self):
        """Test that agent initializes even without API keys"""
        with patch.dict('os.environ', {}, clear=True):
            agent = ClinicalAgent()
            assert agent is not None
            assert agent.groq_api_key == ""
            assert agent.gemini_api_key == ""

    @patch('requests.get')
    def test_search_trials_with_timeout(self, mock_get):
        """Test that timeout is properly handled"""
        mock_get.side_effect = Exception("Timeout")

        agent = ClinicalAgent()
        result = agent.search_trials("GLP-1", page_size=100)

        # Should return empty structure on timeout
        assert result["studies"] == []
        assert result["totalCount"] == 0

    def test_process_with_empty_query(self):
        """Test processing empty or whitespace query"""
        agent = ClinicalAgent()

        # Should not crash with empty query
        # (May return fallback keywords or sanitized empty string)
        keywords = agent._sanitize_keywords("")
        assert isinstance(keywords, str)
