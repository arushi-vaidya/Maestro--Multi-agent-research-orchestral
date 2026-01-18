"""
Integration Tests for Master Agent
Tests agent orchestration, routing, error isolation, and response fusion
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.master_agent import MasterAgent


class TestMasterAgentInitialization:
    """Test Master Agent initialization"""

    @patch('agents.master_agent.LiteratureAgent')
    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_master_agent_initializes_all_agents(
        self, mock_market_class, mock_patent_class, mock_clinical_class, mock_literature_class
    ):
        """Test that Master Agent initializes all sub-agents"""
        # Setup mocks
        mock_clinical_class.return_value = Mock()
        mock_patent_class.return_value = Mock()
        mock_market_class.return_value = Mock()
        mock_literature_class.return_value = Mock()

        master = MasterAgent()

        assert master.name == "Master Agent"
        assert master.clinical_agent is not None
        assert master.patent_agent is not None
        assert master.market_agent is not None
        assert master.literature_agent is not None

    def test_master_agent_has_required_methods(self):
        """Test that Master Agent has all required methods"""
        with patch('agents.master_agent.ClinicalAgent'), \
             patch('agents.master_agent.PatentAgent'), \
             patch('agents.master_agent.MarketAgentHybrid'), \
             patch('agents.master_agent.LiteratureAgent'):
            master = MasterAgent()

            assert hasattr(master, 'process_query')
            assert hasattr(master, '_classify_query')
            assert hasattr(master, '_run_clinical_agent')
            assert hasattr(master, '_run_market_agent')
            assert hasattr(master, '_run_patent_agent')
            assert hasattr(master, '_run_literature_agent')
            assert hasattr(master, '_fuse_results')
            assert callable(master.process_query)


class TestQueryClassification:
    """Test query classification logic (deterministic, no mocks needed)"""

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_classify_market_only_query(self, mock_m, mock_p, mock_c):
        """Test classification of market-only queries"""
        master = MasterAgent()

        # Market-only queries
        assert master._classify_query("What is the GLP-1 market size?") == ['market']
        assert master._classify_query("GLP-1 revenue forecast for 2024") == ['market']
        assert master._classify_query("Market opportunity for diabetes drugs") == ['market']

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_classify_clinical_only_query(self, mock_m, mock_p, mock_c):
        """Test classification of clinical-only queries"""
        master = MasterAgent()

        # Clinical-only queries
        assert master._classify_query("Show me Phase 3 trials for GLP-1") == ['clinical']
        assert master._classify_query("What clinical trials are recruiting for NCT12345678?") == ['clinical']
        assert master._classify_query("GLP-1 clinical efficacy data") == ['clinical']

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_classify_patent_only_query(self, mock_m, mock_p, mock_c):
        """Test classification of patent-only queries"""
        master = MasterAgent()

        # Patent-only queries
        assert master._classify_query("What is the patent landscape for GLP-1?") == ['patent']
        assert master._classify_query("Patent expiration cliff for diabetes drugs") == ['patent']
        assert master._classify_query("IP strategy for GLP-1 agonists") == ['patent']

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_classify_market_and_clinical_query(self, mock_m, mock_p, mock_c):
        """Test classification requiring both market and clinical"""
        master = MasterAgent()

        result = master._classify_query("GLP-1 market opportunity and clinical trial landscape")

        assert 'market' in result
        assert 'clinical' in result

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_classify_fto_query_uses_all_agents(self, mock_m, mock_p, mock_c):
        """Test that FTO queries trigger all agents"""
        master = MasterAgent()

        # FTO queries should use all three agents
        result = master._classify_query("Freedom to operate analysis for GLP-1")

        assert 'patent' in result
        assert 'market' in result
        assert 'clinical' in result

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_classify_multi_dimensional_query(self, mock_m, mock_p, mock_c):
        """Test multi-dimensional queries use all agents"""
        master = MasterAgent()

        # Comprehensive analysis queries
        result = master._classify_query("Comprehensive due diligence for GLP-1 therapeutic")

        assert len(result) == 3
        assert 'patent' in result
        assert 'market' in result
        assert 'clinical' in result

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_classify_ambiguous_query_defaults_to_both(self, mock_m, mock_p, mock_c):
        """Test that ambiguous queries default to market + clinical"""
        master = MasterAgent()

        # Ambiguous query
        result = master._classify_query("Tell me about GLP-1")

        # Default is both market and clinical
        assert 'market' in result
        assert 'clinical' in result

    @patch('agents.master_agent.LiteratureAgent')
    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_classify_literature_only_query(self, mock_m, mock_p, mock_c, mock_l):
        """Test classification of literature-only queries"""
        master = MasterAgent()

        # Literature-only queries
        assert master._classify_query("Show me recent literature on GLP-1") == ['literature']
        assert master._classify_query("What are the latest publications about GLP-1?") == ['literature']
        assert master._classify_query("GLP-1 research papers and studies") == ['literature']
        assert master._classify_query("Literature review on diabetes treatments") == ['literature']

    @patch('agents.master_agent.LiteratureAgent')
    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_classify_literature_and_clinical_query(self, mock_m, mock_p, mock_c, mock_l):
        """Test classification requiring both literature and clinical"""
        master = MasterAgent()

        result = master._classify_query("GLP-1 publications and clinical trials")

        assert 'literature' in result
        assert 'clinical' in result

    @patch('agents.master_agent.LiteratureAgent')
    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_classify_literature_and_market_query(self, mock_m, mock_p, mock_c, mock_l):
        """Test classification requiring both literature and market"""
        master = MasterAgent()

        result = master._classify_query("GLP-1 research papers and market analysis")

        assert 'literature' in result
        assert 'market' in result


class TestAgentRouting:
    """Test correct routing to agents based on classification"""

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_routes_to_market_agent_only(
        self, mock_market_class, mock_patent_class, mock_clinical_class,
        mock_market_agent_output
    ):
        """Test routing to market agent only"""
        # Setup mocks
        mock_market = Mock()
        mock_market.process.return_value = mock_market_agent_output
        mock_market_class.return_value = mock_market

        mock_clinical = Mock()
        mock_clinical_class.return_value = mock_clinical

        mock_patent = Mock()
        mock_patent_class.return_value = mock_patent

        master = MasterAgent()
        master.market_agent = mock_market
        master.clinical_agent = mock_clinical
        master.patent_agent = mock_patent

        result = master.process_query("What is the GLP-1 market size?")

        # Verify only market agent was called
        mock_market.process.assert_called_once()
        mock_clinical.process.assert_not_called()
        mock_patent.process.assert_not_called()

        # Verify response structure
        assert isinstance(result, dict)

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_routes_to_clinical_agent_only(
        self, mock_market_class, mock_patent_class, mock_clinical_class,
        mock_clinical_agent_output
    ):
        """Test routing to clinical agent only"""
        mock_clinical = Mock()
        mock_clinical.process.return_value = mock_clinical_agent_output["raw"]
        mock_clinical_class.return_value = mock_clinical

        mock_market = Mock()
        mock_market_class.return_value = mock_market

        mock_patent = Mock()
        mock_patent_class.return_value = mock_patent

        master = MasterAgent()
        master.clinical_agent = mock_clinical
        master.market_agent = mock_market
        master.patent_agent = mock_patent

        result = master.process_query("Show me Phase 3 GLP-1 trials")

        # Verify only clinical agent was called
        mock_clinical.process.assert_called_once()
        mock_market.process.assert_not_called()
        mock_patent.process.assert_not_called()

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_routes_to_both_market_and_clinical(
        self, mock_market_class, mock_patent_class, mock_clinical_class,
        mock_market_agent_output, mock_clinical_agent_output
    ):
        """Test routing to both market and clinical agents"""
        mock_market = Mock()
        mock_market.process.return_value = mock_market_agent_output
        mock_market_class.return_value = mock_market

        mock_clinical = Mock()
        mock_clinical.process.return_value = mock_clinical_agent_output["raw"]
        mock_clinical_class.return_value = mock_clinical

        mock_patent = Mock()
        mock_patent_class.return_value = mock_patent

        master = MasterAgent()
        master.market_agent = mock_market
        master.clinical_agent = mock_clinical
        master.patent_agent = mock_patent

        result = master.process_query("GLP-1 market and clinical landscape")

        # Both should be called
        mock_market.process.assert_called_once()
        mock_clinical.process.assert_called_once()
        mock_patent.process.assert_not_called()


class TestErrorIsolation:
    """Test that one agent failure doesn't crash the system"""

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_market_agent_failure_doesnt_crash_system(
        self, mock_market_class, mock_patent_class, mock_clinical_class,
        mock_clinical_agent_output
    ):
        """Test that market agent failure doesn't crash entire query"""
        # Market agent fails
        mock_market = Mock()
        mock_market.process.side_effect = Exception("Market Agent Error")
        mock_market_class.return_value = mock_market

        # Clinical agent succeeds
        mock_clinical = Mock()
        mock_clinical.process.return_value = mock_clinical_agent_output["raw"]
        mock_clinical_class.return_value = mock_clinical

        mock_patent = Mock()
        mock_patent_class.return_value = mock_patent

        master = MasterAgent()
        master.market_agent = mock_market
        master.clinical_agent = mock_clinical

        # Query that needs both agents
        result = master.process_query("GLP-1 analysis")

        # Should still return a result (from clinical agent)
        assert isinstance(result, dict)

        # Check execution status shows market failed
        if 'agent_execution_status' in result:
            market_status = [s for s in result['agent_execution_status'] if s['agent_id'] == 'market']
            if market_status:
                assert market_status[0]['status'] == 'failed'

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_clinical_agent_failure_doesnt_crash_system(
        self, mock_market_class, mock_patent_class, mock_clinical_class,
        mock_market_agent_output
    ):
        """Test that clinical agent failure doesn't crash entire query"""
        # Clinical agent fails
        mock_clinical = Mock()
        mock_clinical.process.side_effect = Exception("Clinical Agent Error")
        mock_clinical_class.return_value = mock_clinical

        # Market agent succeeds
        mock_market = Mock()
        mock_market.process.return_value = mock_market_agent_output
        mock_market_class.return_value = mock_market

        mock_patent = Mock()
        mock_patent_class.return_value = mock_patent

        master = MasterAgent()
        master.market_agent = mock_market
        master.clinical_agent = mock_clinical

        result = master.process_query("GLP-1 comprehensive analysis")

        # Should still return result from market agent
        assert isinstance(result, dict)

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_all_agents_fail_returns_error_structure(
        self, mock_market_class, mock_patent_class, mock_clinical_class
    ):
        """Test that all agents failing still returns valid structure"""
        # All agents fail
        mock_market = Mock()
        mock_market.process.side_effect = Exception("Market Error")
        mock_market_class.return_value = mock_market

        mock_clinical = Mock()
        mock_clinical.process.side_effect = Exception("Clinical Error")
        mock_clinical_class.return_value = mock_clinical

        mock_patent = Mock()
        mock_patent.process.side_effect = Exception("Patent Error")
        mock_patent_class.return_value = mock_patent

        master = MasterAgent()
        master.market_agent = mock_market
        master.clinical_agent = mock_clinical
        master.patent_agent = mock_patent

        result = master.process_query("GLP-1 FTO analysis")

        # Should still return a dict, not crash
        assert isinstance(result, dict)


class TestResponseFusion:
    """Test result fusion from multiple agents"""

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_fuses_results_from_multiple_agents(
        self, mock_market_class, mock_patent_class, mock_clinical_class,
        mock_market_agent_output, mock_clinical_agent_output, mock_patent_agent_output
    ):
        """Test that results from multiple agents are properly fused"""
        mock_market = Mock()
        mock_market.process.return_value = mock_market_agent_output
        mock_market_class.return_value = mock_market

        mock_clinical = Mock()
        mock_clinical.process.return_value = mock_clinical_agent_output["raw"]
        mock_clinical_class.return_value = mock_clinical

        mock_patent = Mock()
        mock_patent.process.return_value = mock_patent_agent_output
        mock_patent_class.return_value = mock_patent

        master = MasterAgent()
        master.market_agent = mock_market
        master.clinical_agent = mock_clinical
        master.patent_agent = mock_patent

        # FTO query triggers all agents
        result = master.process_query("Freedom to operate analysis for GLP-1")

        # Verify fused response structure
        assert isinstance(result, dict)
        assert "summary" in result
        assert "references" in result
        assert "agent_execution_status" in result

        # Verify all agents' data is present
        execution_status = result.get("agent_execution_status", [])
        agent_ids = [s["agent_id"] for s in execution_status]
        assert "market" in agent_ids
        assert "clinical" in agent_ids
        assert "patent" in agent_ids

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_references_have_correct_agent_ids(
        self, mock_market_class, mock_patent_class, mock_clinical_class,
        mock_market_agent_output, mock_clinical_agent_output
    ):
        """Test that references are tagged with correct agentId"""
        mock_market = Mock()
        mock_market.process.return_value = mock_market_agent_output
        mock_market_class.return_value = mock_market

        mock_clinical = Mock()
        mock_clinical.process.return_value = mock_clinical_agent_output["raw"]
        mock_clinical_class.return_value = mock_clinical

        mock_patent = Mock()
        mock_patent_class.return_value = mock_patent

        master = MasterAgent()
        master.market_agent = mock_market
        master.clinical_agent = mock_clinical

        result = master.process_query("GLP-1 market and trials")

        # Check references have agentId
        if "references" in result:
            for ref in result["references"]:
                assert "agentId" in ref
                assert ref["agentId"] in ["market", "clinical", "patent"]

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_no_duplicate_agent_execution(
        self, mock_market_class, mock_patent_class, mock_clinical_class,
        mock_market_agent_output
    ):
        """Test that agents are not executed multiple times"""
        mock_market = Mock()
        mock_market.process.return_value = mock_market_agent_output
        mock_market_class.return_value = mock_market

        mock_clinical = Mock()
        mock_clinical_class.return_value = mock_clinical

        mock_patent = Mock()
        mock_patent_class.return_value = mock_patent

        master = MasterAgent()
        master.market_agent = mock_market

        # Market-only query
        result = master.process_query("GLP-1 market size")

        # Market agent should be called exactly once
        assert mock_market.process.call_count == 1


class TestResponseSchema:
    """Test response schema correctness"""

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_response_has_required_fields(
        self, mock_market_class, mock_patent_class, mock_clinical_class,
        mock_market_agent_output
    ):
        """Test that response has all required fields"""
        mock_market = Mock()
        mock_market.process.return_value = mock_market_agent_output
        mock_market_class.return_value = mock_market

        mock_clinical = Mock()
        mock_clinical_class.return_value = mock_clinical

        mock_patent = Mock()
        mock_patent_class.return_value = mock_patent

        master = MasterAgent()
        master.market_agent = mock_market

        result = master.process_query("GLP-1 market")

        # Required top-level fields
        assert "summary" in result
        assert "references" in result or "insights" in result
        assert "agent_execution_status" in result

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_execution_status_structure(
        self, mock_market_class, mock_patent_class, mock_clinical_class,
        mock_clinical_agent_output
    ):
        """Test execution status has correct structure"""
        mock_clinical = Mock()
        mock_clinical.process.return_value = mock_clinical_agent_output["raw"]
        mock_clinical_class.return_value = mock_clinical

        mock_market = Mock()
        mock_market_class.return_value = mock_market

        mock_patent = Mock()
        mock_patent_class.return_value = mock_patent

        master = MasterAgent()
        master.clinical_agent = mock_clinical

        result = master.process_query("GLP-1 Phase 3 trials")

        # Check execution status
        if "agent_execution_status" in result:
            for status in result["agent_execution_status"]:
                assert "agent_id" in status
                assert "status" in status
                assert status["status"] in ["running", "completed", "failed"]
                assert "started_at" in status
                assert "result_count" in status

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_market_intelligence_structure(
        self, mock_market_class, mock_patent_class, mock_clinical_class,
        mock_market_agent_output
    ):
        """Test market intelligence data structure"""
        mock_market = Mock()
        mock_market.process.return_value = mock_market_agent_output
        mock_market_class.return_value = mock_market

        mock_clinical = Mock()
        mock_clinical_class.return_value = mock_clinical

        mock_patent = Mock()
        mock_patent_class.return_value = mock_patent

        master = MasterAgent()
        master.market_agent = mock_market

        result = master.process_query("GLP-1 market")

        # If market data is included
        if "market_intelligence" in result:
            mi = result["market_intelligence"]
            assert "sections" in mi
            assert isinstance(mi["sections"], dict)


class TestEdgeCases:
    """Test edge cases and unusual inputs"""

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_handles_empty_query(self, mock_m, mock_p, mock_c):
        """Test handling of empty query"""
        master = MasterAgent()

        # Should not crash
        result = master.process_query("")

        assert isinstance(result, dict)

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_handles_very_long_query(self, mock_m, mock_p, mock_c):
        """Test handling of very long query"""
        master = MasterAgent()

        long_query = "GLP-1 market analysis " * 100

        result = master.process_query(long_query)

        assert isinstance(result, dict)

    @patch('agents.master_agent.ClinicalAgent')
    @patch('agents.master_agent.PatentAgent')
    @patch('agents.master_agent.MarketAgentHybrid')
    def test_handles_special_characters_in_query(self, mock_m, mock_p, mock_c):
        """Test handling of special characters"""
        master = MasterAgent()

        special_query = "GLP-1 <>&\"' market analysis"

        result = master.process_query(special_query)

        assert isinstance(result, dict)
