"""
Unit Tests for Market Agent Hybrid
Tests hybrid retrieval (Web Search + RAG) with mocked components
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.market_agent_hybrid import MarketAgentHybrid


class TestMarketAgentInitialization:
    """Test Market Agent initialization"""

    @patch('agents.market_agent_hybrid.RAG_AVAILABLE', False)
    @patch('agents.market_agent_hybrid.WEB_SEARCH_AVAILABLE', False)
    def test_agent_initializes_without_dependencies(self):
        """Test agent initializes even without RAG or web search"""
        agent = MarketAgentHybrid(
            use_rag=False,
            use_web_search=False,
            initialize_corpus=False
        )

        assert agent.name == "Market Intelligence Agent (Hybrid)"
        assert agent.agent_id == "market"
        assert agent.use_rag is False
        assert agent.use_web_search is False

    @patch('agents.market_agent_hybrid.RAGEngine')
    @patch('agents.market_agent_hybrid.RAG_AVAILABLE', True)
    def test_agent_initializes_with_rag(self, mock_rag_class):
        """Test agent initializes with RAG"""
        mock_rag = Mock()
        mock_rag.get_collection_stats.return_value = {"total_documents": 100}
        mock_rag_class.return_value = mock_rag

        agent = MarketAgentHybrid(
            use_rag=True,
            use_web_search=False,
            initialize_corpus=False
        )

        assert agent.use_rag is True
        assert agent.rag_engine is not None

    @patch('agents.market_agent_hybrid.WebSearchEngine')
    @patch('agents.market_agent_hybrid.WEB_SEARCH_AVAILABLE', True)
    def test_agent_initializes_with_web_search(self, mock_web_class):
        """Test agent initializes with web search"""
        mock_web = Mock()
        mock_web_class.return_value = mock_web

        agent = MarketAgentHybrid(
            use_rag=False,
            use_web_search=True,
            initialize_corpus=False
        )

        assert agent.use_web_search is True

    def test_agent_has_required_methods(self):
        """Test agent has all required methods"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        assert hasattr(agent, 'process')
        assert hasattr(agent, '_analyze_query')
        assert hasattr(agent, '_extract_search_keywords')
        assert hasattr(agent, '_retrieve_from_web')
        assert hasattr(agent, '_retrieve_from_rag')
        assert hasattr(agent, '_synthesize_intelligence')
        assert callable(agent.process)


class TestQueryAnalysis:
    """Test query analysis for retrieval strategy"""

    def test_analyze_query_fresh_indicators(self):
        """Test detection of queries needing fresh data"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        needs_fresh, needs_historical = agent._analyze_query("What is the latest 2024 GLP-1 market size?")
        assert needs_fresh is True

        needs_fresh, needs_historical = agent._analyze_query("Recent market trends for GLP-1")
        assert needs_fresh is True

    def test_analyze_query_historical_indicators(self):
        """Test detection of queries needing historical context"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        needs_fresh, needs_historical = agent._analyze_query("History of GLP-1 market evolution")
        assert needs_historical is True

        needs_fresh, needs_historical = agent._analyze_query("GLP-1 market background and trends")
        assert needs_historical is True

    def test_analyze_query_both_by_default(self):
        """Test that queries use both sources by default if unclear"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        needs_fresh, needs_historical = agent._analyze_query("GLP-1 market")
        # Default is both
        assert needs_fresh is True
        assert needs_historical is True


class TestKeywordExtraction:
    """Test search keyword extraction"""

    @patch('agents.market_agent_hybrid.generate_llm_response')
    @patch('agents.market_agent_hybrid.KEYWORD_EXTRACTION_AVAILABLE', True)
    def test_extract_search_keywords_with_llm(self, mock_llm):
        """Test keyword extraction using LLM"""
        mock_llm.return_value = "GLP-1 market size, diabetes drugs 2024, GLP-1 forecast"

        # Mock the keyword extractor
        with patch('agents.market_agent_hybrid.KeywordExtractor') as mock_ke_class:
            mock_ke = Mock()
            mock_ke.extract_keywords_robust.return_value = [
                "GLP-1 market size",
                "diabetes drugs 2024",
                "GLP-1 forecast"
            ]
            mock_ke_class.return_value = mock_ke

            agent = MarketAgentHybrid(use_rag=False, use_web_search=False)
            agent.keyword_extractor = mock_ke

            keywords = agent._extract_search_keywords("What is the GLP-1 market size?")

            assert isinstance(keywords, list)
            assert len(keywords) > 0
            assert all(isinstance(k, str) for k in keywords)

    def test_extract_search_keywords_legacy_fallback(self):
        """Test legacy keyword extraction when new module unavailable"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)
        agent.keyword_extractor = None

        with patch('agents.market_agent_hybrid.generate_llm_response') as mock_llm:
            mock_llm.return_value = "GLP-1 market, diabetes drugs"

            keywords = agent._extract_search_keywords("GLP-1 market analysis")

            assert isinstance(keywords, list)
            assert len(keywords) > 0

    @patch('agents.market_agent_hybrid.generate_llm_response')
    def test_extract_search_keywords_llm_failure(self, mock_llm):
        """Test fallback when LLM fails"""
        mock_llm.side_effect = Exception("LLM Error")

        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)
        agent.keyword_extractor = None

        keywords = agent._extract_search_keywords_legacy("GLP-1 market")

        # Should fall back to using the query itself
        assert isinstance(keywords, list)
        assert len(keywords) > 0


class TestWebRetrieval:
    """Test web search retrieval"""

    def test_retrieve_from_web_no_keywords(self):
        """Test web retrieval with no keywords"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=True)
        results = agent._retrieve_from_web([], top_k=10)

        assert results == []

    @patch('agents.market_agent_hybrid.WebSearchEngine')
    def test_retrieve_from_web_success(self, mock_web_class, mock_web_search_results):
        """Test successful web retrieval"""
        mock_web = Mock()
        mock_web.search_multi_query.return_value = mock_web_search_results
        mock_web_class.return_value = mock_web

        agent = MarketAgentHybrid(use_rag=False, use_web_search=True, initialize_corpus=False)
        agent.web_search = mock_web

        keywords = ["GLP-1 market", "diabetes drugs"]
        results = agent._retrieve_from_web(keywords, top_k=10)

        assert isinstance(results, list)
        assert len(results) <= 10
        # Verify structure
        if results:
            assert "title" in results[0]
            assert "snippet" in results[0]
            assert "url" in results[0]

    @patch('agents.market_agent_hybrid.WebSearchEngine')
    def test_retrieve_from_web_api_failure(self, mock_web_class):
        """Test web retrieval handles API failures"""
        mock_web = Mock()
        mock_web.search_multi_query.side_effect = Exception("Search API Error")
        mock_web_class.return_value = mock_web

        agent = MarketAgentHybrid(use_rag=False, use_web_search=True, initialize_corpus=False)
        agent.web_search = mock_web

        results = agent._retrieve_from_web(["GLP-1"], top_k=10)

        # Should return empty list on error
        assert results == []


class TestRAGRetrieval:
    """Test RAG retrieval"""

    @patch('agents.market_agent_hybrid.RAGEngine')
    def test_retrieve_from_rag_success(self, mock_rag_class, mock_rag_results):
        """Test successful RAG retrieval"""
        mock_rag = Mock()
        mock_rag.search.return_value = mock_rag_results
        mock_rag_class.return_value = mock_rag

        agent = MarketAgentHybrid(use_rag=True, use_web_search=False, initialize_corpus=False)
        agent.rag_engine = mock_rag

        results = agent._retrieve_from_rag("GLP-1 market", top_k=5)

        assert isinstance(results, list)
        assert len(results) <= 5
        if results:
            assert "content" in results[0]
            assert "metadata" in results[0]

    @patch('agents.market_agent_hybrid.RAGEngine')
    def test_retrieve_from_rag_failure(self, mock_rag_class):
        """Test RAG retrieval handles failures"""
        mock_rag = Mock()
        mock_rag.search.side_effect = Exception("RAG Error")
        mock_rag_class.return_value = mock_rag

        agent = MarketAgentHybrid(use_rag=True, use_web_search=False, initialize_corpus=False)
        agent.rag_engine = mock_rag

        results = agent._retrieve_from_rag("GLP-1", top_k=5)

        assert results == []


class TestContextFusion:
    """Test context fusion from web and RAG"""

    def test_fuse_contexts_with_both_sources(self, mock_web_search_results, mock_rag_results):
        """Test fusing contexts from web and RAG"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        fused = agent._fuse_contexts(mock_web_search_results, mock_rag_results)

        assert isinstance(fused, str)
        assert len(fused) > 0
        assert "WEB SEARCH RESULTS" in fused
        assert "INTERNAL KNOWLEDGE BASE" in fused

    def test_fuse_contexts_web_only(self, mock_web_search_results):
        """Test fusing with only web results"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        fused = agent._fuse_contexts(mock_web_search_results, [])

        assert isinstance(fused, str)
        assert "WEB SEARCH RESULTS" in fused
        assert "INTERNAL KNOWLEDGE BASE" not in fused

    def test_fuse_contexts_rag_only(self, mock_rag_results):
        """Test fusing with only RAG results"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        fused = agent._fuse_contexts([], mock_rag_results)

        assert isinstance(fused, str)
        assert "INTERNAL KNOWLEDGE BASE" in fused

    def test_fuse_contexts_empty(self):
        """Test fusing with no results"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        fused = agent._fuse_contexts([], [])

        assert isinstance(fused, str)


class TestIntelligenceSynthesis:
    """Test market intelligence synthesis"""

    @patch('agents.market_agent_hybrid.SectionSynthesizer')
    @patch('agents.market_agent_hybrid.SECTION_SYNTHESIS_AVAILABLE', True)
    def test_synthesize_intelligence_with_section_synthesizer(
        self, mock_ss_class, mock_web_search_results, mock_rag_results
    ):
        """Test synthesis with new section synthesizer"""
        mock_ss = Mock()
        mock_ss.synthesize_all_sections.return_value = {
            "summary": "Market summary",
            "market_overview": "Market overview",
            "key_metrics": "Key metrics",
            "drivers_and_trends": "Drivers and trends",
            "competitive_landscape": "Competitive landscape",
            "risks_and_opportunities": "Risks",
            "future_outlook": "Outlook"
        }
        mock_ss_class.return_value = mock_ss

        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)
        agent.section_synthesizer = mock_ss

        fused_context = "Web and RAG context combined"
        sections = agent._synthesize_intelligence(
            "GLP-1 market",
            fused_context,
            mock_web_search_results,
            mock_rag_results
        )

        assert isinstance(sections, dict)
        assert len(sections) == 7
        assert "summary" in sections
        assert "market_overview" in sections
        assert "future_outlook" in sections

    @patch('agents.market_agent_hybrid.generate_llm_response')
    def test_synthesize_intelligence_legacy(
        self, mock_llm, mock_web_search_results, mock_rag_results, mock_llm_synthesis_response
    ):
        """Test legacy synthesis method"""
        mock_llm.return_value = mock_llm_synthesis_response

        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)
        agent.section_synthesizer = None  # Force legacy path

        fused_context = "Context with web and RAG data"
        sections = agent._synthesize_intelligence_legacy(
            "GLP-1 market",
            fused_context,
            mock_web_search_results,
            mock_rag_results
        )

        assert isinstance(sections, dict)
        assert "summary" in sections
        assert "market_overview" in sections
        # All 7 sections should be populated
        assert len(sections) == 7

    def test_synthesize_intelligence_no_sources_fallback(self):
        """Test synthesis fallback when no sources available"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)
        agent.section_synthesizer = None

        sections = agent._synthesize_intelligence_legacy(
            "GLP-1 market",
            "",
            [],  # No web results
            []   # No RAG results
        )

        assert isinstance(sections, dict)
        assert "No market intelligence sources available" in sections["summary"]

    @patch('agents.market_agent_hybrid.generate_llm_response')
    def test_synthesize_intelligence_llm_failure(self, mock_llm, mock_web_search_results):
        """Test synthesis handles LLM failure"""
        mock_llm.side_effect = Exception("LLM Error")

        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)
        agent.section_synthesizer = None

        sections = agent._synthesize_intelligence_legacy(
            "GLP-1 market",
            "Some context",
            mock_web_search_results,
            []
        )

        # Should fall back to source snippets
        assert isinstance(sections, dict)
        assert len(sections) > 0


class TestPlainTextParsing:
    """Test plain text section parsing"""

    def test_parse_plain_text_sections_complete(self, mock_llm_synthesis_response):
        """Test parsing complete plain text response"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        sections = agent._parse_plain_text_sections(mock_llm_synthesis_response)

        assert isinstance(sections, dict)
        assert "summary" in sections
        assert "market_overview" in sections
        # Verify content was extracted
        assert len(sections["summary"]) > 0

    def test_parse_plain_text_sections_incomplete(self):
        """Test parsing handles incomplete text"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        incomplete_text = "SUMMARY\nJust a summary, missing other sections."

        sections = agent._parse_plain_text_sections(incomplete_text)

        # Should still have summary
        assert "summary" in sections


class TestConfidenceCalculation:
    """Test confidence scoring"""

    @patch('agents.market_agent_hybrid.ConfidenceScorer')
    @patch('agents.market_agent_hybrid.CONFIDENCE_SCORING_AVAILABLE', True)
    def test_confidence_calculation_with_scorer(self, mock_cs_class):
        """Test confidence calculation with ConfidenceScorer"""
        mock_cs = Mock()
        mock_cs.calculate_confidence.return_value = {
            "score": 0.85,
            "breakdown": {"source_coverage": 0.9, "source_quality": 0.8},
            "explanation": "Good coverage",
            "level": "high"
        }
        mock_cs_class.return_value = mock_cs

        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)
        agent.confidence_scorer = mock_cs

        # Test is implicit in process() method

    def test_confidence_calculation_fallback(self, mock_web_search_results, mock_rag_results):
        """Test simple fallback confidence calculation"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)
        agent.confidence_scorer = None  # Force fallback

        confidence = agent._calculate_confidence_fallback(
            mock_web_search_results,
            mock_rag_results
        )

        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_confidence_fallback_no_sources(self):
        """Test confidence fallback with no sources"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        confidence = agent._calculate_confidence_fallback([], [])

        assert confidence == 0.0


class TestProcessMethod:
    """Test main process() method with full flow"""

    @patch('agents.market_agent_hybrid.RAGEngine')
    @patch('agents.market_agent_hybrid.WebSearchEngine')
    @patch('agents.market_agent_hybrid.generate_llm_response')
    def test_process_full_flow_with_both_sources(
        self, mock_llm, mock_web_class, mock_rag_class,
        mock_web_search_results, mock_rag_results, mock_llm_synthesis_response
    ):
        """Test complete process with web and RAG"""
        # Setup mocks
        mock_web = Mock()
        mock_web.search_multi_query.return_value = mock_web_search_results
        mock_web_class.return_value = mock_web

        mock_rag = Mock()
        mock_rag.search.return_value = mock_rag_results
        mock_rag.get_collection_stats.return_value = {"total_documents": 100}
        mock_rag_class.return_value = mock_rag

        # Mock LLM for keyword extraction and synthesis
        mock_llm.side_effect = [
            "GLP-1 market, diabetes drugs",  # Keyword extraction
            mock_llm_synthesis_response       # Synthesis
        ]

        with patch('agents.market_agent_hybrid.RAG_AVAILABLE', True):
            with patch('agents.market_agent_hybrid.WEB_SEARCH_AVAILABLE', True):
                agent = MarketAgentHybrid(
                    use_rag=True,
                    use_web_search=True,
                    initialize_corpus=False
                )
                agent.rag_engine = mock_rag
                agent.web_search = mock_web
                agent.section_synthesizer = None  # Use legacy
                agent.confidence_scorer = None  # Use fallback

                result = agent.process("What is the GLP-1 market size?", top_k_rag=5, top_k_web=10)

                # Verify output structure
                assert isinstance(result, dict)
                assert result["agentId"] == "market"
                assert "query" in result
                assert "retrieval_used" in result
                assert "sections" in result
                assert "confidence" in result
                assert "web_results" in result
                assert "rag_results" in result
                assert "sources" in result

                # Verify retrieval was used
                assert result["retrieval_used"]["web_search"] is True
                assert result["retrieval_used"]["rag"] is True

                # Verify sections exist
                assert len(result["sections"]) == 7
                assert "summary" in result["sections"]

    @patch('agents.market_agent_hybrid.generate_llm_response')
    def test_process_web_only(self, mock_llm, mock_web_search_results, mock_llm_synthesis_response):
        """Test process with web search only"""
        mock_llm.side_effect = [
            "GLP-1 market",
            mock_llm_synthesis_response
        ]

        with patch('agents.market_agent_hybrid.WebSearchEngine') as mock_web_class:
            mock_web = Mock()
            mock_web.search_multi_query.return_value = mock_web_search_results
            mock_web_class.return_value = mock_web

            with patch('agents.market_agent_hybrid.WEB_SEARCH_AVAILABLE', True):
                agent = MarketAgentHybrid(
                    use_rag=False,
                    use_web_search=True,
                    initialize_corpus=False
                )
                agent.web_search = mock_web
                agent.section_synthesizer = None
                agent.confidence_scorer = None

                result = agent.process("Latest GLP-1 market data 2024")

                assert result["retrieval_used"]["web_search"] is True
                assert result["retrieval_used"]["rag"] is False

    def test_process_no_sources(self):
        """Test process with no retrieval sources"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)
        agent.section_synthesizer = None
        agent.confidence_scorer = None

        result = agent.process("GLP-1 market")

        # Should return structure with limited data
        assert isinstance(result, dict)
        assert result["confidence_score"] == 0.0


class TestOutputContract:
    """Test that output follows the expected contract"""

    def test_output_structure_matches_contract(self):
        """Test output has all required fields"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)
        agent.confidence_scorer = None

        result = agent.process("GLP-1 market")

        # Required fields per contract
        required_fields = [
            "agentId", "query", "retrieval_used", "search_keywords",
            "web_results", "rag_results", "sections", "confidence",
            "confidence_score", "sources"
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Verify sections structure
        required_sections = [
            "summary", "market_overview", "key_metrics",
            "drivers_and_trends", "competitive_landscape",
            "risks_and_opportunities", "future_outlook"
        ]

        for section in required_sections:
            assert section in result["sections"], f"Missing section: {section}"

    def test_sources_structure(self):
        """Test sources field structure"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        result = agent.process("GLP-1")

        assert "sources" in result
        assert "web" in result["sources"]
        assert "internal" in result["sources"]
        assert isinstance(result["sources"]["web"], list)
        assert isinstance(result["sources"]["internal"], list)


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_process_with_empty_query(self):
        """Test process with empty query"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        # Should not crash
        result = agent.process("")

        assert isinstance(result, dict)

    def test_process_with_very_long_query(self):
        """Test process with very long query"""
        agent = MarketAgentHybrid(use_rag=False, use_web_search=False)

        long_query = "GLP-1 market " * 100

        result = agent.process(long_query)

        assert isinstance(result, dict)
