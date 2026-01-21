"""
Master Agent - Simplified for Feature 1
Orchestrates query processing and agent coordination

Feature 1: Clinical Agent, Patent Agent, and Market Agent
Future: Multi-agent coordination with LangGraph
"""
from typing import Dict, Any, List
from datetime import datetime
import logging
import os  # CRITICAL FIX: Added missing import
import requests
import time
from agents.clinical_agent import ClinicalAgent
from agents.patent_agent import PatentAgent
from agents.market_agent_hybrid import MarketAgentHybrid
from agents.literature_agent import LiteratureAgent

# STEP 4: Evidence Normalization Layer + AKGP Integration
from normalization import (
    parse_clinical_evidence,
    parse_patent_evidence,
    parse_market_evidence,
    parse_literature_evidence,
    ParsingRejection
)
from akgp.graph_manager import GraphManager
from akgp.ingestion import IngestionEngine

# Import LLM config for summary generation
from config.llm.llm_config_sync import generate_llm_response

# STEP 7: LangGraph Orchestration (toggle-able)
USE_LANGGRAPH = os.getenv('USE_LANGGRAPH', 'false').lower() == 'true'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MasterAgent:
    """
    Master Agent - Orchestrates specialized agents

    Features:
    - Clinical Agent: Clinical trials analysis
    - Patent Agent: Patent landscape, FTO, IP strategy
    - Market Agent: Market intelligence, forecasts, competitive landscape
    Future: LangGraph-based multi-agent orchestration
    """

    def __init__(self):
        self.name = "Master Agent"
        self.clinical_agent = ClinicalAgent()
        self.patent_agent = PatentAgent()
        self.market_agent = MarketAgentHybrid(
            use_rag=True,
            use_web_search=True,
            initialize_corpus=False  # Avoid corpus initialization at startup
        )
        self.literature_agent = LiteratureAgent()

        # STEP 4: Initialize AKGP for evidence ingestion
        self.graph_manager = GraphManager()
        self.ingestion_engine = IngestionEngine(self.graph_manager)

        logger.info("Master Agent initialized with Clinical, Patent, Market, and Literature agents")
        logger.info("STEP 4: AKGP IngestionEngine initialized for evidence normalization")

    def _ingest_to_akgp(
        self,
        agent_output: Dict[str, Any],
        agent_id: str,
        parser_func: callable
    ) -> Dict[str, Any]:
        """
        STEP 4: Ingest agent output through normalization layer into AKGP

        This is the SINGLE INGESTION GATE for all agents.

        Flow: Agent Output → Normalization Parser → AKGP.ingest_evidence()

        Args:
            agent_output: Raw agent output
            agent_id: Agent identifier (clinical/patent/market/literature)
            parser_func: Normalization parser function (parse_clinical_evidence, etc.)

        Returns:
            Ingestion summary with statistics

        Error Handling:
            - ParsingRejection: Expected - log but don't crash (malformed data)
            - Other exceptions: Log error but don't crash (agent failures shouldn't cascade)
        """
        ingestion_summary = {
            "agent_id": agent_id,
            "total_evidence": 0,
            "ingested_evidence": 0,
            "rejected_evidence": 0,
            "errors": []
        }

        try:
            logger.info(f"🔗 STEP 4: Normalizing {agent_id} output for AKGP ingestion...")

            # Parse agent output into normalized evidence
            normalized_evidence_list = parser_func(agent_output)

            ingestion_summary["total_evidence"] = len(normalized_evidence_list)

            logger.info(
                f"✅ Normalization complete: {len(normalized_evidence_list)} evidence items from {agent_id}"
            )

            # Ingest each normalized evidence into AKGP
            for evidence in normalized_evidence_list:
                try:
                    ingest_result = self.ingestion_engine.ingest_evidence(evidence)

                    if ingest_result.get("success"):
                        ingestion_summary["ingested_evidence"] += 1
                        logger.debug(
                            f"   ✓ Ingested: {evidence.evidence_node.name} "
                            f"({evidence.polarity}: {evidence.drug_id[:20]}... → {evidence.disease_id[:20]}...)"
                        )
                    else:
                        ingestion_summary["rejected_evidence"] += 1
                        logger.warning(f"   ✗ Ingestion failed: {ingest_result.get('warning', 'Unknown error')}")

                except Exception as e:
                    ingestion_summary["rejected_evidence"] += 1
                    ingestion_summary["errors"].append(str(e))
                    logger.error(f"   ✗ AKGP ingestion error: {e}", exc_info=False)

            logger.info(
                f"✅ AKGP ingestion complete for {agent_id}: "
                f"{ingestion_summary['ingested_evidence']}/{ingestion_summary['total_evidence']} ingested, "
                f"{ingestion_summary['rejected_evidence']} rejected"
            )

        except ParsingRejection as e:
            # Expected - agent output doesn't meet normalization requirements
            logger.warning(f"⚠️ Parsing rejection for {agent_id}: {e}")
            ingestion_summary["errors"].append(f"ParsingRejection: {e}")

        except Exception as e:
            # Unexpected error - log but don't crash
            logger.error(f"❌ Unexpected error during {agent_id} normalization: {e}", exc_info=True)
            ingestion_summary["errors"].append(f"Unexpected error: {e}")

        return ingestion_summary

    def _classify_query(self, query: str) -> List[str]:
        """
        Classify query to determine which agents to activate.

        Returns: List of agent IDs: ['market'], ['clinical'], ['patent'], or combination

        Classification Logic (Deterministic Priority Order):
        1. Multi-dimensional FTO queries → ALL AGENTS
        2. Explicit multi-agent queries (e.g., "market and clinical") → SPECIFIED AGENTS
        3. Single-agent indicators → SINGLE AGENT
        4. Default → MARKET + CLINICAL (conservative)

        Rules:
        - Single-intent query → exactly one agent
        - Multi-intent query → deterministic priority ordering
        - No implicit fan-out
        - No silent aggregation
        """
        query_lower = query.lower()

        # 1. MULTI-DIMENSIONAL (FTO/Due Diligence) - requires ALL agents
        # Note: "patent landscape" alone is NOT multi-dimensional (goes to patent only)
        multi_dimensional_keywords = [
            'freedom to operate', 'fto', 'ip landscape',
            'competitive intelligence', 'due diligence', 'investment analysis',
            'strategic assessment', 'comprehensive analysis'
        ]

        is_multi_dimensional = any(kw in query_lower for kw in multi_dimensional_keywords)
        if is_multi_dimensional:
            logger.info("🎯 Query classified as: MULTI-DIMENSIONAL (FTO/Comprehensive) → ALL AGENTS")
            return ['patent', 'market', 'clinical']

        # 2. EXPLICIT MULTI-AGENT CONNECTIVES
        # Detect explicit "X and Y" patterns for multi-agent queries
        has_explicit_and = ' and ' in query_lower

        # Patent-specific keywords (prioritized to avoid over-triggering)
        patent_keywords = [
            'patent landscape', 'patent expir', 'patent cliff',
            'patent strategy', 'ip strategy', 'patent portfolio',
            'patent litigation', 'patent protection', 'exclusivity',
            'white space', 'licensing'
        ]

        # More specific patent keywords that should NOT trigger other agents
        patent_only_keywords = [
            'patent landscape', 'patent expiration', 'patent cliff',
            'patent portfolio', 'patent strategy'
        ]

        # General patent terms (may co-occur with market/clinical)
        general_patent_keywords = ['patent', 'ip ', 'intellectual property']

        # Market-specific keywords
        market_keywords = [
            'market size', 'market share', 'revenue', 'forecast',
            'cagr', 'growth rate', 'sales', 'pricing', 'valuation',
            'pipeline value', 'market opportunity', 'market analysis',
            'revenue forecast', 'market trends', 'market dynamics'
        ]

        # General market terms (may co-occur)
        general_market_keywords = ['market', 'competitive', 'opportunity']

        # Clinical-specific keywords
        clinical_keywords = [
            'clinical trial', 'phase 1', 'phase 2', 'phase 3', 'phase i', 'phase ii', 'phase iii',
            'efficacy', 'safety', 'nct', 'endpoint', 'adverse event',
            'protocol', 'enrollment', 'recruiting'
        ]

        # General clinical terms
        general_clinical_keywords = ['trial', 'patient', 'study', 'clinical']

        # Literature-specific keywords
        literature_keywords = [
            'literature', 'literature review', 'publications', 'pubmed',
            'research papers', 'scientific literature', 'biomedical literature',
            'research articles', 'peer-reviewed', 'pmid', 'published studies',
            'systematic review', 'meta-analysis'
        ]

        # Check for specific patterns first (higher priority)
        has_literature = any(kw in query_lower for kw in literature_keywords)
        has_patent_only = any(kw in query_lower for kw in patent_only_keywords)
        has_patent_general = any(kw in query_lower for kw in general_patent_keywords)
        has_patent = has_patent_only or has_patent_general or any(kw in query_lower for kw in patent_keywords)

        has_market_specific = any(kw in query_lower for kw in market_keywords)
        has_market_general = any(kw in query_lower for kw in general_market_keywords)
        has_market = has_market_specific or has_market_general

        has_clinical_specific = any(kw in query_lower for kw in clinical_keywords)
        has_clinical_general = any(kw in query_lower for kw in general_clinical_keywords)
        has_clinical = has_clinical_specific or has_clinical_general

        # DECISION TREE (Deterministic)

        # 3a. Literature-only queries
        if has_literature and not has_patent and not has_market_specific and not has_clinical_specific:
            logger.info("🎯 Query classified as: LITERATURE ONLY")
            return ['literature']

        # 3b. Patent-only queries (specific patent landscape keywords)
        if has_patent_only and not has_market_specific and not has_clinical_specific and not has_literature:
            logger.info("🎯 Query classified as: PATENT ONLY (patent landscape/specific)")
            return ['patent']

        # 3b. Explicit multi-agent with "and" connective
        if has_explicit_and:
            if has_literature and has_clinical and not has_market and not has_patent:
                logger.info("🎯 Query classified as: LITERATURE + CLINICAL (explicit 'and')")
                return ['literature', 'clinical']
            elif has_literature and has_market and not has_clinical and not has_patent:
                logger.info("🎯 Query classified as: LITERATURE + MARKET (explicit 'and')")
                return ['literature', 'market']
            elif has_market and has_clinical and not has_patent and not has_literature:
                logger.info("🎯 Query classified as: MARKET + CLINICAL (explicit 'and')")
                return ['market', 'clinical']
            elif has_patent and has_market and has_clinical:
                logger.info("🎯 Query classified as: ALL AGENTS (explicit multi-agent)")
                return ['patent', 'market', 'clinical']

        # 3c. Patent + other agents
        if has_patent and (has_market or has_clinical):
            logger.info("🎯 Query classified as: PATENT + MARKET + CLINICAL (patent with others)")
            return ['patent', 'market', 'clinical']

        # 3d. Patent only (general patent terms without market/clinical)
        if has_patent:
            logger.info("🎯 Query classified as: PATENT ONLY")
            return ['patent']

        # 3e. Market + Clinical
        if has_market and has_clinical:
            logger.info("🎯 Query classified as: MARKET + CLINICAL")
            return ['market', 'clinical']

        # 3f. Market only
        if has_market and not has_clinical:
            logger.info("🎯 Query classified as: MARKET ONLY")
            return ['market']

        # 3g. Clinical only
        if has_clinical and not has_market:
            logger.info("🎯 Query classified as: CLINICAL ONLY")
            return ['clinical']

        # 4. Default: Market + Clinical (conservative)
        logger.info("🎯 Query classified as: MARKET + CLINICAL (default)")
        return ['market', 'clinical']

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process query with intelligent multi-agent routing.

        Flow: Classification → Agent Execution → Result Fusion

        STEP 7: Toggle-able LangGraph orchestration
        - If USE_LANGGRAPH=true: Use LangGraph parallel execution
        - If USE_LANGGRAPH=false: Use legacy sequential execution
        """
        from datetime import datetime

        logger.info("="*60)
        logger.info(f"Master Agent processing query: {query[:100]}...")
        logger.info("="*60)
        print(f"\nMaster Agent processing query: {query[:100]}...")

        # STEP 7: LangGraph orchestration (if enabled)
        if USE_LANGGRAPH:
            logger.info("Using LangGraph orchestration (STEP 7)")
            print("Using LangGraph orchestration (STEP 7)")
            from graph_orchestration.workflow import execute_query
            return execute_query(query)

        # LEGACY: Sequential orchestration
        logger.info("Using legacy sequential orchestration")
        print("🎯 Using legacy sequential orchestration")

        # Step 1: Classify query to determine which agents to run
        active_agents = self._classify_query(query)
        logger.info(f"📋 Classification result: {active_agents}")
        print(f"📋 Classification result: {active_agents}")

        # Step 2 & 3: Execute agents
        results = {}
        execution_status = []  # Track execution status for frontend

        if 'patent' in active_agents:
            logger.info("⚖️ Delegating to Patent Agent...")
            print(f"   ⚖️ Calling Patent Agent...")
            start_time = datetime.now()
            
            # Add RUNNING status BEFORE execution
            execution_status.append({
                'agent_id': 'patent',
                'status': 'running',
                'started_at': start_time.isoformat(),
                'completed_at': None,
                'result_count': 0
            })
            
            try:
                patent_result = self._run_patent_agent(query)
                results['patent'] = patent_result
                patent_count = len(patent_result.get('references', []))
                logger.info(f"✅ Patent Agent returned: {patent_count} patents")
                print(f"   ✅ Patent Agent: {patent_count} patents")

                # STEP 4: Normalize + ingest into AKGP
                ingestion_summary = self._ingest_to_akgp(
                    agent_output=patent_result,
                    agent_id='patent',
                    parser_func=parse_patent_evidence
                )
                results['patent_akgp_ingestion'] = ingestion_summary

                # Update to COMPLETED status
                execution_status[-1].update({
                    'status': 'completed',
                    'completed_at': datetime.now().isoformat(),
                    'result_count': patent_count,
                    'akgp_ingestion': ingestion_summary
                })
            except Exception as e:
                logger.error(f"❌ Patent Agent FAILED: {e}", exc_info=True)
                print(f"   ❌ Patent Agent FAILED: {e}")
                execution_status[-1].update({
                    'status': 'failed',
                    'completed_at': datetime.now().isoformat(),
                    'result_count': 0
                })

        if 'clinical' in active_agents:
            logger.info("🏥 Delegating to Clinical Agent...")
            print(f"   🏥 Calling Clinical Agent...")
            start_time = datetime.now()
            
            # Add RUNNING status BEFORE execution
            execution_status.append({
                'agent_id': 'clinical',
                'status': 'running',
                'started_at': start_time.isoformat(),
                'completed_at': None,
                'result_count': 0
            })
            
            try:
                clinical_result = self._run_clinical_agent(query)
                results['clinical'] = clinical_result
                trial_count = clinical_result.get('total_trials', 0)
                ref_count = len(clinical_result.get('references', []))
                logger.info(f"✅ Clinical Agent returned: {trial_count} trials, {ref_count} references")
                print(f"   ✅ Clinical Agent: {trial_count} trials, {ref_count} references")

                # STEP 4: Normalize + ingest into AKGP
                ingestion_summary = self._ingest_to_akgp(
                    agent_output=clinical_result,
                    agent_id='clinical',
                    parser_func=parse_clinical_evidence
                )
                results['clinical_akgp_ingestion'] = ingestion_summary

                # Update to COMPLETED status
                execution_status[-1].update({
                    'status': 'completed',
                    'completed_at': datetime.now().isoformat(),
                    'result_count': trial_count,
                    'akgp_ingestion': ingestion_summary
                })
            except Exception as e:
                logger.error(f"❌ Clinical Agent FAILED: {e}", exc_info=True)
                print(f"   ❌ Clinical Agent FAILED: {e}")
                execution_status[-1].update({
                    'status': 'failed',
                    'completed_at': datetime.now().isoformat(),
                    'result_count': 0
                })

        if 'market' in active_agents:
            logger.info("📊 Delegating to Market Agent...")
            print(f"   📊 Calling Market Agent...")
            start_time = datetime.now()
            
            # Add RUNNING status BEFORE execution
            execution_status.append({
                'agent_id': 'market',
                'status': 'running',
                'started_at': start_time.isoformat(),
                'completed_at': None,
                'result_count': 0
            })
            
            try:
                market_result = self._run_market_agent(query)
                results['market'] = market_result
                web_count = len(market_result.get('web_results', []))
                rag_count = len(market_result.get('rag_results', []))
                source_count = web_count + rag_count
                logger.info(f"✅ Market Agent returned: {web_count} web sources, {rag_count} RAG docs")
                print(f"   ✅ Market Agent: {web_count} web sources, {rag_count} RAG docs")

                # STEP 4: Normalize + ingest into AKGP
                ingestion_summary = self._ingest_to_akgp(
                    agent_output=market_result,
                    agent_id='market',
                    parser_func=parse_market_evidence
                )
                results['market_akgp_ingestion'] = ingestion_summary

                # Update to COMPLETED status
                execution_status[-1].update({
                    'status': 'completed',
                    'completed_at': datetime.now().isoformat(),
                    'result_count': source_count,
                    'akgp_ingestion': ingestion_summary
                })
            except Exception as e:
                logger.error(f"❌ Market Agent FAILED: {e}", exc_info=True)
                print(f"   ❌ Market Agent FAILED: {e}")
                execution_status[-1].update({
                    'status': 'failed',
                    'completed_at': datetime.now().isoformat(),
                    'result_count': 0
                })

        if 'literature' in active_agents:
            logger.info("📚 Delegating to Literature Agent...")
            print(f"   📚 Calling Literature Agent...")
            start_time = datetime.now()

            # Add RUNNING status BEFORE execution
            execution_status.append({
                'agent_id': 'literature',
                'status': 'running',
                'started_at': start_time.isoformat(),
                'completed_at': None,
                'result_count': 0
            })

            try:
                literature_result = self._run_literature_agent(query)
                results['literature'] = literature_result
                pub_count = len(literature_result.get('publications', []))
                logger.info(f"✅ Literature Agent returned: {pub_count} publications")
                print(f"   ✅ Literature Agent: {pub_count} publications")

                # STEP 4: Normalize + ingest into AKGP
                ingestion_summary = self._ingest_to_akgp(
                    agent_output=literature_result,
                    agent_id='literature',
                    parser_func=parse_literature_evidence
                )
                results['literature_akgp_ingestion'] = ingestion_summary

                # Update to COMPLETED status
                execution_status[-1].update({
                    'status': 'completed',
                    'completed_at': datetime.now().isoformat(),
                    'result_count': pub_count,
                    'akgp_ingestion': ingestion_summary
                })
            except Exception as e:
                logger.error(f"❌ Literature Agent FAILED: {e}", exc_info=True)
                print(f"   ❌ Literature Agent FAILED: {e}")
                execution_status[-1].update({
                    'status': 'failed',
                    'completed_at': datetime.now().isoformat(),
                    'result_count': 0
                })

        # Step 3: Fuse results into unified response
        logger.info(f"🔀 Fusing results from {len(results)} agent(s)...")
        print(f"🔀 Fusing results from {len(results)} agent(s)...")
        fused_response = self._fuse_results(query, results, execution_status)

        # Log final response stats
        total_refs = len(fused_response.get('references', []))
        total_insights = len(fused_response.get('insights', []))
        logger.info(f"✅ Master Agent completed: {total_refs} total references, {total_insights} insights")
        print(f"✅ Master Agent completed: {total_refs} total references, {total_insights} insights")
        logger.info("="*60)

        return fused_response

    def _run_clinical_agent(self, query: str) -> Dict[str, Any]:
        """Run Clinical Agent and return structured results"""
        logger.info(f"🔬 Clinical Agent: Starting process for query: '{query}'")

        # Get clinical trials data
        clinical_result = self.clinical_agent.process(query)

        # DIAGNOSTIC: Log raw clinical agent response
        logger.info(f"🔬 Clinical Agent raw response keys: {clinical_result.keys()}")
        logger.info(f"🔬 Clinical Agent trials count from API: {len(clinical_result.get('trials', []))}")

        # Fetch detailed summaries for each trial
        trial_count = len(clinical_result.get('trials', []))

        if trial_count == 0:
            logger.warning(f"⚠️ Clinical Agent returned 0 trials! Raw response: {clinical_result}")
            print(f"   ⚠️ WARNING: Clinical Agent returned 0 trials!")
            return {
                'summary': clinical_result.get('comprehensive_summary', 'No trials found'),
                'comprehensive_summary': clinical_result.get('comprehensive_summary', 'No trials found'),
                'trials': [],
                'references': [],
                'total_trials': 0
            }

        # Limit detailed fetching to top 25 trials to prevent timeout
        MAX_DETAILED_TRIALS = 25
        trials_to_fetch = min(trial_count, MAX_DETAILED_TRIALS)
        
        logger.info(f"📄 Fetching detailed summaries for {trials_to_fetch}/{trial_count} trials (limited to {MAX_DETAILED_TRIALS} for performance)...")
        print(f"   📄 Fetching detailed summaries for {trials_to_fetch}/{trial_count} trials...")

        references = []
        for i, trial in enumerate(clinical_result.get('trials', [])[:MAX_DETAILED_TRIALS], 1):
            try:
                if i <= 5:  # Log first 5 for debugging
                    logger.info(f"   Fetching trial {i}/{trial_count}: {trial['nct_id']}")
                trial_details = self.clinical_agent.get_trial_details(trial['nct_id'])
                trial_summary = self.clinical_agent.get_trial_summary(trial['nct_id'])
                
                # Extract full trial data from API response
                protocol = trial_details.get('protocolSection', {})
                status_module = protocol.get('statusModule', {})
                design_module = protocol.get('designModule', {})
                
                # Get trial status and date
                trial_status = status_module.get('overallStatus', 'Unknown')
                start_date_str = status_module.get('startDateStruct', {}).get('date', '2024')
                
                # Get phases
                phases = design_module.get('phases', [])
                phase_str = ', '.join(phases) if phases else 'Unknown'
                
                # Get enrollment
                enrollment_info = design_module.get('enrollmentInfo', {})
                enrollment_count = enrollment_info.get('count', 0)
                
                # Map ClinicalTrials.gov status to ROS-compatible status
                ros_status = trial_status
                if 'RECRUITING' in trial_status or 'ACTIVE' in trial_status:
                    ros_status = 'recruiting'
                elif 'COMPLETED' in trial_status:
                    ros_status = 'completed'
                elif 'TERMINATED' in trial_status or 'WITHDRAWN' in trial_status:
                    ros_status = 'terminated'
                else:
                    ros_status = 'other'
                
                references.append({
                    "type": "clinical_trial",  # CRITICAL FIX: underscore not hyphen
                    "title": trial_summary['title'],
                    "source": f"ClinicalTrials.gov {trial['nct_id']}",
                    "date": start_date_str,  # CRITICAL FIX: actual trial start date
                    "url": f"https://clinicaltrials.gov/study/{trial['nct_id']}",
                    "relevance": 90,
                    "agentId": "clinical",
                    "nct_id": trial['nct_id'],
                    "summary": trial_summary['summary'],
                    "status": ros_status,  # CRITICAL FIX: add status for recency calculation
                    "phase": phase_str,  # CRITICAL FIX: add phase for novelty calculation
                    "enrollment": enrollment_count  # Additional info for future scoring
                })
            except Exception as e:
                logger.warning(f"Failed to fetch summary for {trial['nct_id']}: {e}")
                references.append({
                    "type": "clinical_trial",  # CRITICAL FIX: underscore not hyphen
                    "title": trial['title'],
                    "source": f"ClinicalTrials.gov {trial['nct_id']}",
                    "date": "2024",
                    "url": f"https://clinicaltrials.gov/study/{trial['nct_id']}",
                    "relevance": 85,
                    "agentId": "clinical",
                    "nct_id": trial['nct_id'],
                    "summary": "Summary unavailable",
                    "status": "unknown",  # CRITICAL FIX: add status
                    "phase": "Unknown",  # CRITICAL FIX: add phase
                    "enrollment": 0
                })

        logger.info(f"✅ Clinical Agent wrapper completed: {len(references)} trial references created")

        return {
            'summary': clinical_result.get('comprehensive_summary', clinical_result.get('summary', '')),
            'comprehensive_summary': clinical_result.get('comprehensive_summary', ''),
            'trials': clinical_result.get('trials', []),
            'raw': clinical_result.get('raw', clinical_result.get('trials', [])),  # Add raw field for normalization
            'references': references,
            'total_trials': trial_count
        }

    def _run_market_agent(self, query: str) -> Dict[str, Any]:
        """
        Run Market Agent and return structured results

        Retrieval Configuration:
        - top_k_rag=15: Retrieve 15 internal knowledge base documents
        - top_k_web=80: Retrieve 80 web sources (targets 25-30 after deduplication)
        """
        market_result = self.market_agent.process(query, top_k_rag=15, top_k_web=80)

        web_count = len(market_result.get('web_results', []))
        rag_count = len(market_result.get('rag_results', []))
        logger.info(f"✅ Market Agent completed: {web_count} web sources, {rag_count} RAG docs, confidence {market_result['confidence']['score']:.2%}")

        return market_result

    def _run_patent_agent(self, query: str) -> Dict[str, Any]:
        """Run Patent Agent and return structured results"""
        logger.info(f"⚖️ Patent Agent: Starting process for query: '{query}'")
        
        # Get patent intelligence data
        patent_result = self.patent_agent.process(query)

        # Extract key patent data
        patents = patent_result.get('patents', [])
        landscape = patent_result.get('landscape', {})
        fto_assessment = patent_result.get('fto_assessment', {})
        expiring_analysis = patent_result.get('expiring_analysis', {})

        # Create references from patents
        logger.info(f"⚖️ Processing {len(patents)} patent records...")
        references = []
        for i, patent in enumerate(patents[:20], 1):  # Top 20 patents
            assignees = [
                a.get('assignee_organization', 'Unknown')
                for a in patent.get('assignees', [])
            ]
            patent_number = patent.get('patent_number', 'N/A')
            references.append({
                "type": "patent",
                "title": patent.get('patent_title', 'No title available'),
                "source": f"USPTO Patent {patent_number}",
                "date": patent.get('patent_date', 'N/A')[:4] if patent.get('patent_date') else 'N/A',
                "url": f"https://patents.google.com/patent/US{patent_number}",
                "relevance": 90 - i,  # Decreasing relevance
                "agentId": "patent",
                "patent_number": patent_number,
                "assignee": ', '.join(assignees[:2]) if assignees else 'Unknown',
                "citations": patent.get('citedby_patent_count', 0),
                "summary": patent.get('patent_abstract', 'No abstract available')[:300] + '...'
                    if patent.get('patent_abstract') else 'No abstract available',
                "status": "issued",  # Patents are issued
                "phase": "Patent"  # Use 'Patent' as phase for patent references
            })

        logger.info(f"✅ Patent Agent wrapper completed: {len(references)} patent references created")

        return {
            'summary': patent_result.get('comprehensive_summary', patent_result.get('summary', '')),
            'comprehensive_summary': patent_result.get('comprehensive_summary', ''),
            'patents': patents,
            'references': references,
            'total_patents': len(patents),
            'landscape': landscape,
            'fto_assessment': fto_assessment,
            'expiring_analysis': expiring_analysis
        }

    def _run_literature_agent(self, query: str) -> Dict[str, Any]:
        """Run Literature Agent and return structured results"""
        logger.info(f"📚 Literature Agent: Starting process for query: '{query}'")

        # Get literature review data
        literature_result = self.literature_agent.process(query)

        # Extract publications
        publications = literature_result.get('publications', [])

        # Create references from publications
        logger.info(f"📚 Processing {len(publications)} publication records...")
        references = []
        for i, pub in enumerate(publications[:20], 1):  # Top 20 publications
            authors = ", ".join(pub.get('authors', [])[:3])
            pmid = pub.get('pmid', 'N/A')
            references.append({
                "type": "literature",
                "title": pub.get('title', 'No title available'),
                "source": f"PubMed {pmid}",
                "date": pub.get('year', 'N/A'),
                "url": pub.get('url', f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"),
                "relevance": 90 - i,  # Decreasing relevance
                "agentId": "literature",
                "pmid": pmid,
                "authors": authors,
                "journal": pub.get('journal', 'Unknown journal'),
                "summary": pub.get('abstract', 'No abstract available')[:300] + '...'
                    if pub.get('abstract') else 'No abstract available',
                "status": "published",  # Literature is published
                "phase": "Review"  # Use 'Review' as phase for literature references
            })

        logger.info(f"✅ Literature Agent completed: {len(references)} publication references created")

        return {
            'summary': literature_result.get('comprehensive_summary', literature_result.get('summary', '')),
            'comprehensive_summary': literature_result.get('comprehensive_summary', ''),
            'publications': publications,
            'references': references,
            'total_publications': len(publications),
            'keywords': literature_result.get('keywords', '')
        }

    def _fuse_results(self, query: str, results: Dict[str, Any], execution_status: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fuse results from multiple agents into unified response.

        Strategy:
        - Preserve backward compatibility (existing fields unchanged)
        - Add new fields (market_intelligence, confidence_score)
        - Namespace market data separately (no flattening)
        - Merge references with agentId for filtering
        - Generate intelligent overview summary (LLM synthesis with graceful fallback)
        """
        clinical_data = results.get('clinical', {})
        market_data = results.get('market', {})
        patent_data = results.get('patent', {})
        literature_data = results.get('literature', {})
        execution_status = execution_status or []

        # 1. BUILD OVERVIEW SUMMARY (Intelligent Synthesis with robust fallback)
        try:
            summary = self._synthesize_overview_summary(query, clinical_data, market_data, patent_data, literature_data)
            # If we got the error message, fall back to constructed summary
            if "synthesis failed" in summary.lower():
                logger.warning("LLM synthesis returned error message, using constructed summary instead")
                summary = self._construct_summary_fallback(query, clinical_data, market_data, patent_data, literature_data)
        except Exception as e:
            logger.error(f"Overview summary synthesis exception: {e}, using fallback")
            summary = self._construct_summary_fallback(query, clinical_data, market_data, patent_data, literature_data)

        # 2. BUILD INSIGHTS ARRAY
        insights = []

        if clinical_data:
            insights.append({
                "agent": "Clinical Trials Agent",
                "finding": clinical_data.get('comprehensive_summary', clinical_data.get('summary', '')),
                "confidence": 95,
                "total_trials": clinical_data.get('total_trials', 0)
            })

        if market_data:
            insights.append({
                "agent": "Market Intelligence Agent",
                "finding": market_data['sections']['summary'],
                "confidence": int(market_data['confidence']['score'] * 100),
                "confidence_level": market_data['confidence']['level'],
                "sources_used": {
                    "web": len(market_data.get('web_results', [])),
                    "internal": len(market_data.get('rag_results', []))
                }
            })

        if patent_data:
            insights.append({
                "agent": "Patent Intelligence Agent",
                "finding": patent_data.get('comprehensive_summary', patent_data.get('summary', '')),
                "confidence": 90,
                "total_patents": patent_data.get('total_patents', 0)
            })

        if literature_data:
            insights.append({
                "agent": "Literature Agent",
                "finding": literature_data.get('comprehensive_summary', literature_data.get('summary', '')),
                "confidence": 85,
                "total_publications": literature_data.get('total_publications', 0)
            })

        # 3. BUILD RECOMMENDATION
        # Simplified recommendation logic for brevity
        recommendation = "Review the comprehensive Executive Summary and detailed agent reports below."

        # 4. MERGE REFERENCES WITH STRICT SCHEMA ENFORCEMENT
        references = []

        # Add clinical references
        if clinical_data:
            clinical_refs = clinical_data.get('references', [])
            for ref in clinical_refs:
                if 'agentId' not in ref: ref['agentId'] = 'clinical'
                references.append(ref)

        # Add patent references
        if patent_data:
            patent_refs = patent_data.get('references', [])
            for ref in patent_refs:
                if 'agentId' not in ref: ref['agentId'] = 'patent'
                references.append(ref)

        # Add literature references
        if literature_data:
            lit_refs = literature_data.get('references', [])
            for ref in lit_refs:
                if 'agentId' not in ref: ref['agentId'] = 'literature'
                references.append(ref)

        # Add market references
        if market_data:
            market_refs = []
            for web_result in market_data.get('web_results', []):
                url = web_result.get('url', '')
                domain_tier = web_result.get('domain_tier', 2)
                relevance_map = {1: 95, 2: 85, 3: 70}
                relevance = relevance_map.get(domain_tier, 85)
                market_refs.append({
                    "type": "market-report",
                    "title": web_result.get('title', 'Market Intelligence Source'),
                    "source": url.split('/')[2] if url else 'Web',
                    "date": web_result.get('date', '2024'),
                    "url": url,
                    "relevance": relevance,
                    "agentId": "market",
                    "summary": web_result.get('snippet', ''),
                    "domain_tier": domain_tier,
                    "status": "published",  # Market reports are published
                    "phase": "Market"  # Use 'Market' as phase for market references
                })
            for rag_result in market_data.get('rag_results', []):
                market_refs.append({
                    "type": "market-report",
                    "title": rag_result.get('metadata', {}).get('title', 'Internal Market Intelligence'),
                    "source": "Internal Knowledge Base",
                    "date": rag_result.get('metadata', {}).get('date', '2024'),
                    "url": "",
                    "relevance": 90,
                    "agentId": "market",
                    "summary": rag_result.get('content', '')[:500],
                    "status": "published",  # Market reports are published
                    "phase": "Market"  # Use 'Market' as phase
                })
            references.extend(market_refs)

        # 5. CALCULATE AGGREGATE CONFIDENCE
        scores = []
        if clinical_data: scores.append(95)
        if patent_data: scores.append(90)
        if literature_data: scores.append(85)
        if market_data: scores.append(market_data['confidence']['score'] * 100)
        
        aggregate_confidence = sum(scores) / len(scores) if scores else 0

        # 6. BUILD UNIFIED RESPONSE
        response = {
            "summary": summary,
            "insights": insights,
            "recommendation": recommendation,
            "timelineSaved": "6-8 hours",
            "references": references,
            "confidence_score": aggregate_confidence,
            "active_agents": list(results.keys()),
            "agent_execution_status": execution_status,
            "market_intelligence": market_data if market_data else None,
            "patent_intelligence": patent_data if patent_data else None,
            "total_trials": clinical_data.get('total_trials', 0) if clinical_data else 0
        }

        logger.info(f"🔀 Fusion complete: {len(references)} references, {len(insights)} insights")

        return response

    def _generate_agent_output_summaries(
        self,
        clinical_data: Dict[str, Any],
        market_data: Dict[str, Any],
        patent_data: Dict[str, Any],
        literature_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate concise LLM summaries for each agent's findings.
        Takes raw agent output (references, data) and produces a 2-3 sentence summary.
        """
        summaries = {}
        logger.info(f"📝 Generating LLM summaries... Clinical: {bool(clinical_data)}, Market: {bool(market_data)}, Patent: {bool(patent_data)}, Literature: {bool(literature_data)}")
        
        # Clinical Agent Summary
        if clinical_data and clinical_data.get('references'):
            logger.info(f"   Generating clinical summary from {len(clinical_data.get('references', []))} references...")
            clinical_refs = clinical_data.get('references', [])[:10]
            refs_text = "\n".join([f"- {r.get('title', 'Trial')}: {r.get('summary', '')[:100]}" for r in clinical_refs])
            prompt = f"""Summarize the following clinical trial findings in 2-3 sentences. Focus on key outcomes and patient populations.

Trials analyzed ({len(clinical_refs)}):
{refs_text}

Provide a concise summary:"""
            try:
                summary = generate_llm_response(prompt, temperature=0.3, max_tokens=150)
                summaries['clinical'] = summary.strip()
                logger.info(f"   ✅ Clinical summary generated: {len(summary)} chars")
            except Exception as e:
                logger.warning(f"   ❌ Failed to generate clinical summary: {e}")
                summaries['clinical'] = f"Analyzed {clinical_data.get('total_trials', 0)} clinical trials with mixed results."
        else:
            logger.info("   ⏭️ Clinical summary skipped (no data)")
        
        # Market Agent Summary
        if market_data and market_data.get('web_results'):
            logger.info(f"   Generating market summary from {len(market_data.get('web_results', []))} sources...")
            market_refs = market_data.get('web_results', [])[:10]
            refs_text = "\n".join([f"- {r.get('title', 'Source')}: {r.get('snippet', '')[:100]}" for r in market_refs])
            prompt = f"""Summarize the following market intelligence findings in 2-3 sentences. Focus on market size, trends, and competitive landscape.

Sources analyzed ({len(market_refs)}):
{refs_text}

Provide a concise summary:"""
            try:
                summary = generate_llm_response(prompt, temperature=0.3, max_tokens=150)
                summaries['market'] = summary.strip()
            except Exception as e:
                logger.warning(f"Failed to generate market summary: {e}")
                summaries['market'] = f"Analyzed {len(market_refs)} market sources across web and internal databases."
        
        # Patent Agent Summary
        if patent_data and patent_data.get('references'):
            logger.info(f"   Generating patent summary from {len(patent_data.get('references', []))} patents...")
            patent_refs = patent_data.get('references', [])[:10]
            refs_text = "\n".join([f"- {r.get('title', 'Patent')}: {r.get('summary', '')[:100]}" for r in patent_refs])
            prompt = f"""Summarize the following patent landscape findings in 2-3 sentences. Focus on key innovations and filing trends.

Patents analyzed ({len(patent_refs)}):
{refs_text}

Provide a concise summary:"""
            try:
                summary = generate_llm_response(prompt, temperature=0.3, max_tokens=150)
                summaries['patent'] = summary.strip()
            except Exception as e:
                logger.warning(f"Failed to generate patent summary: {e}")
                summaries['patent'] = f"Analyzed {patent_data.get('total_patents', 0)} patents covering various therapeutic approaches."
        
        # Literature Agent Summary
        if literature_data and literature_data.get('references'):
            lit_refs = literature_data.get('references', [])[:10]
            refs_text = "\n".join([f"- {r.get('title', 'Publication')}: {r.get('summary', '')[:100]}" for r in lit_refs])
            prompt = f"""Summarize the following scientific literature findings in 2-3 sentences. Focus on mechanisms of action and key findings.

Publications analyzed ({len(lit_refs)}):
{refs_text}

Provide a concise summary:"""
            try:
                summary = generate_llm_response(prompt, temperature=0.3, max_tokens=150)
                summaries['literature'] = summary.strip()
            except Exception as e:
                logger.warning(f"Failed to generate literature summary: {e}")
                summaries['literature'] = f"Analyzed {literature_data.get('total_publications', 0)} publications exploring therapeutic mechanisms."
        
        return summaries

    def _synthesize_overview_summary(
        self, 
        query: str, 
        clinical_data: Dict[str, Any], 
        market_data: Dict[str, Any],
        patent_data: Dict[str, Any],
        literature_data: Dict[str, Any]
    ) -> str:
        """
        Generate detailed Executive Summary using LLM (Gemini/Groq).
        """
        # Helper to format references
        def format_refs(refs):
            return "\n".join([f"- {r.get('title', 'Ref')} ({r.get('url', '#')})" for r in refs[:10]])

        # Prepare context data
        context = {
            "query": query,
            "clinical": {
                "summary": clinical_data.get('comprehensive_summary', 'No data'),
                "count": clinical_data.get('total_trials', 0),
                "refs": format_refs(clinical_data.get('references', []))
            },
            "market": {
                "summary": market_data.get('sections', {}).get('summary', 'No data') if market_data else 'No data',
                "confidence": market_data.get('confidence', {}).get('level', 'N/A') if market_data else 'N/A',
                "web_count": len(market_data.get('web_results', [])) if market_data else 0,
                "refs": format_refs([
                    {'title': r.get('title'), 'url': r.get('url')} 
                    for r in market_data.get('web_results', [])
                ] if market_data else [])
            },
            "patent": {
                "summary": patent_data.get('comprehensive_summary', 'No data'),
                "count": patent_data.get('total_patents', 0),
                "refs": format_refs(patent_data.get('references', []))
            },
            "literature": {
                "summary": literature_data.get('comprehensive_summary', 'No data'),
                "count": literature_data.get('total_publications', 0),
                "refs": format_refs(literature_data.get('references', []))
            }
        }

        # Construct prompt
        synthesis_prompt = f"""You are the Chief Research Officer of a pharmaceutical intelligence firm.
Write a comprehensive, scientific, and detailed **Multi-Agent Analysis Report** for the query: "{query}"

INPUT DATA:

1. CLINICAL TRIALS AGENT:
   - Trials Found: {context['clinical']['count']}
   - Summary: {context['clinical']['summary'][:4000]}
   - Key References:
{context['clinical']['refs']}

2. PATENT INTELLIGENCE AGENT:
   - Patents Found: {context['patent']['count']}
   - Summary: {context['patent']['summary'][:4000]}
   - Key References:
{context['patent']['refs']}

3. MARKET INTELLIGENCE AGENT:
   - Sources: {context['market']['web_count']}
   - Confidence: {context['market']['confidence']}
   - Summary: {context['market']['summary'][:4000]}
   - Key References:
{context['market']['refs']}

4. LITERATURE AGENT:
   - Publications: {context['literature']['count']}
   - Summary: {context['literature']['summary'][:4000]}
   - Key References:
{context['literature']['refs']}

MANDATORY REPORT STRUCTURE (Use Markdown):

### 1. Executive Overview
- High-level goal and hypothesis evaluation.
- Clinical and commercial significance.
- Summary of evidence volume.

### 2. Multi-Agent Analysis Framework
- Briefly describe MAESTRO's parallel execution (Clinical, Patent, Market, Literature).
- Mention AKGP normalization and conflict reasoning.

### 3. Clinical Evidence Agent Summary
- Detailed findings from clinical trials.
- Trial phases, outcomes, and trends.
- **MUST include clickable hyperlinks** to key trials using the provided references (e.g., [Title](url)).

### 4. Patent Intelligence Agent Summary
- Patent landscape, assignees, and FTO implications.
- **MUST include clickable hyperlinks** to patents.

### 5. Market Intelligence Agent Summary
- Market size, growth, and forecast analysis.
- **MUST include clickable hyperlinks** to sources.

### 6. Literature / Mechanistic Evidence Agent Summary
- Mechanistic pathways and biological plausibility.
- **MUST include clickable hyperlinks** to PubMed/journals.

### 7. Evidence Conflict & Reconciliation Analysis
- Discuss contradictions (e.g., clinical vs. literature).
- How conflicts affect confidence.

### 8. Confidence Score & ROS Interpretation
- Explain the Research Opportunity Score (ROS) and confidence level based on the evidence.

### 9. Consolidated Reference Index
- List ALL references again, grouped by agent.
- **Format:** - [Source Name/Title](URL)

STYLE RULES:
- **Tone:** Scientific, professional, executive-ready. NO marketing fluff.
- **Length:** Long-form (800+ words). Detail is critical.
- **References:** ABSOLUTELY MANDATORY. Use the provided URLs. Do not hallucinate links.
- **Formatting:** Clean Markdown with headers and bullet points.
"""

        # Call LLM (Gemini with fallback) - with robust timeout and retry logic
        import time
        import requests
        
        MAX_RETRIES = 3
        TIMEOUT = 30  # Shorter timeout to fail faster
        
        gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if gemini_api_key:
            for attempt in range(MAX_RETRIES):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={gemini_api_key}"
                    payload = {
                        "contents": [{"parts": [{"text": synthesis_prompt}]}],
                        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4000}
                    }
                    response = requests.post(url, json=payload, timeout=TIMEOUT)
                    
                    # Handle rate limit with exponential backoff
                    if response.status_code == 429:
                        wait_time = min(2 ** attempt, 10)  # Exponential backoff: 1s, 2s, 4s...
                        logger.warning(f"Rate limited (attempt {attempt+1}/{MAX_RETRIES}), waiting {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    
                    # For other errors, try other providers
                    if response.status_code >= 500:
                        logger.warning(f"Gemini server error {response.status_code}, trying next provider")
                        break
                    if response.status_code == 404:
                        logger.warning(f"Gemini 404 error, trying next provider")
                        break
                        
                    response.raise_for_status()
                    result = response.json()
                    synthesized = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if synthesized and len(synthesized.strip()) > 50:  # Ensure we got meaningful content
                        logger.info("✅ Gemini synthesis succeeded")
                        return synthesized.strip()
                except requests.Timeout:
                    logger.warning(f"Gemini timeout (attempt {attempt+1}/{MAX_RETRIES})")
                    continue
                except Exception as e:
                    logger.warning(f"Gemini synthesis failed (attempt {attempt+1}/{MAX_RETRIES}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        continue
                    break

        # Fallback to Groq - with timeout
        groq_api_key = os.getenv('GROQ_API_KEY')
        if groq_api_key:
            try:
                from config.llm.llm_config_sync import generate_llm_response
                logger.info("Trying Groq fallback for synthesis")
                synthesized = generate_llm_response(
                    prompt=synthesis_prompt,
                    system_prompt="You are a Chief Research Officer.",
                    temperature=0.3,
                    max_tokens=4000
                )
                if synthesized and len(synthesized.strip()) > 50:
                    logger.info("✅ Groq synthesis succeeded")
                    return synthesized.strip()
            except requests.Timeout:
                logger.warning("Groq timeout during synthesis")
            except Exception as e:
                logger.warning(f"Groq fallback failed: {e}")

        # If all LLM providers fail, use constructed summary
        logger.warning("All LLM providers exhausted for synthesis, using constructed fallback")
        return self._construct_summary_fallback(query, {}, {}, {}, {})

    def _construct_summary_fallback(
        self,
        query: str,
        clinical_data: Dict[str, Any],
        market_data: Dict[str, Any],
        patent_data: Dict[str, Any],
        literature_data: Dict[str, Any]
    ) -> str:
        """
        Construct a professional summary when LLM synthesis fails.
        Uses direct data extraction to build a readable executive summary.
        """
        try:
            parts = []
            parts.append(f"## Research Opportunity Analysis: {query}\n")
            
            # Clinical findings
            if clinical_data and clinical_data.get('total_trials', 0) > 0:
                trials = clinical_data.get('total_trials', 0)
                summary = clinical_data.get('comprehensive_summary') or clinical_data.get('summary', 'Clinical trial data analyzed.')
                parts.append(f"### Clinical Evidence\n**{trials} clinical trials analyzed:** {summary}\n")
            
            # Market findings
            if market_data:
                web_count = len(market_data.get('web_results', []))
                rag_count = len(market_data.get('rag_results', []))
                market_summary = market_data.get('sections', {}).get('summary', 'Market analysis complete.')
                parts.append(f"### Market Intelligence\n**{web_count} web sources + {rag_count} internal docs:** {market_summary}\n")
            
            # Patent findings
            if patent_data and patent_data.get('total_patents', 0) > 0:
                patents = patent_data.get('total_patents', 0)
                summary = patent_data.get('comprehensive_summary') or patent_data.get('summary', 'Patent landscape assessed.')
                parts.append(f"### Patent Landscape\n**{patents} patents reviewed:** {summary}\n")
            
            # Literature findings
            if literature_data and literature_data.get('total_publications', 0) > 0:
                pubs = literature_data.get('total_publications', 0)
                summary = literature_data.get('comprehensive_summary') or literature_data.get('summary', 'Literature reviewed.')
                parts.append(f"### Scientific Literature\n**{pubs} publications reviewed:** {summary}\n")
            
            # Consolidated assessment
            parts.append("### Overall Assessment\n")
            parts.append("This analysis synthesizes evidence from multiple pharmaceutical intelligence sources to evaluate the research opportunity. ")
            parts.append("Please review the detailed agent reports and supporting references below for comprehensive findings.\n")
            
            result = "\n".join(parts)
            logger.info(f"✅ Constructed fallback summary ({len(result)} chars)")
            return result
        except Exception as e:
            logger.error(f"Failed to construct summary fallback: {e}")
            return "Analysis complete. Please review the detailed agent reports and references below."