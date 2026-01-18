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
        logger.info("Master Agent initialized with Clinical, Patent, Market, and Literature agents")

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
        general_clinical_keywords = ['trial', 'patient', 'study']

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
            if has_market and has_clinical and not has_patent:
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
        """
        from datetime import datetime

        logger.info("="*60)
        logger.info(f"🎼 Master Agent processing query: {query[:100]}...")
        logger.info("="*60)
        print(f"\n🎼 Master Agent processing query: {query[:100]}...")

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

                # Update to COMPLETED status
                execution_status[-1].update({
                    'status': 'completed',
                    'completed_at': datetime.now().isoformat(),
                    'result_count': patent_count
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

                # Update to COMPLETED status
                execution_status[-1].update({
                    'status': 'completed',
                    'completed_at': datetime.now().isoformat(),
                    'result_count': trial_count
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

                # Update to COMPLETED status
                execution_status[-1].update({
                    'status': 'completed',
                    'completed_at': datetime.now().isoformat(),
                    'result_count': source_count
                })
            except Exception as e:
                logger.error(f"❌ Market Agent FAILED: {e}", exc_info=True)
                print(f"   ❌ Market Agent FAILED: {e}")
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
        results = {}
        execution_status = []  # Track execution status for frontend

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

                # Update to COMPLETED status
                execution_status[-1].update({
                    'status': 'completed',
                    'completed_at': datetime.now().isoformat(),
                    'result_count': trial_count
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

                # Update to COMPLETED status
                execution_status[-1].update({
                    'status': 'completed',
                    'completed_at': datetime.now().isoformat(),
                    'result_count': source_count
                })
            except Exception as e:
                logger.error(f"❌ Market Agent FAILED: {e}", exc_info=True)
                print(f"   ❌ Market Agent FAILED: {e}")
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

        logger.info(f"📄 Fetching detailed summaries for {trial_count} trials...")
        print(f"   📄 Fetching detailed summaries for {trial_count} trials...")

        references = []
        for i, trial in enumerate(clinical_result.get('trials', []), 1):
            try:
                if i <= 5:  # Log first 5 for debugging
                    logger.info(f"   Fetching trial {i}/{trial_count}: {trial['nct_id']}")
                trial_summary = self.clinical_agent.get_trial_summary(trial['nct_id'])
                references.append({
                    "type": "clinical-trial",
                    "title": trial_summary['title'],
                    "source": f"ClinicalTrials.gov {trial_summary['nct_id']}",
                    "date": "2024",
                    "url": f"https://clinicaltrials.gov/study/{trial_summary['nct_id']}",
                    "relevance": 90,
                    "agentId": "clinical",
                    "nct_id": trial_summary['nct_id'],
                    "summary": trial_summary['summary']
                })
            except Exception as e:
                logger.warning(f"Failed to fetch summary for {trial['nct_id']}: {e}")
                references.append({
                    "type": "clinical-trial",
                    "title": trial['title'],
                    "source": f"ClinicalTrials.gov {trial['nct_id']}",
                    "date": "2024",
                    "url": f"https://clinicaltrials.gov/study/{trial['nct_id']}",
                    "relevance": 85,
                    "agentId": "clinical",
                    "nct_id": trial['nct_id'],
                    "summary": "Summary unavailable"
                })

        logger.info(f"✅ Clinical Agent wrapper completed: {len(references)} trial references created")

        return {
            'summary': clinical_result.get('comprehensive_summary', clinical_result.get('summary', '')),
            'comprehensive_summary': clinical_result.get('comprehensive_summary', ''),
            'trials': clinical_result.get('trials', []),
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
                    if patent.get('patent_abstract') else 'No abstract available'
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
                    if pub.get('abstract') else 'No abstract available'
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
        - Generate intelligent overview summary (LLM synthesis)
        """
        clinical_data = results.get('clinical', {})
        market_data = results.get('market', {})
        execution_status = execution_status or []

        # 1. BUILD OVERVIEW SUMMARY (Intelligent Synthesis)
        summary = self._synthesize_overview_summary(query, clinical_data, market_data)

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

        # 3. BUILD RECOMMENDATION
        if clinical_data and market_data:
            web_count = len(market_data.get('web_results', []))
            rag_count = len(market_data.get('rag_results', []))
            market_total = web_count + rag_count
            recommendation = (
                f"Review {len(clinical_data['references'])} clinical trials and "
                f"{market_total} market intelligence sources ({web_count} web + {rag_count} internal)."
            )
        elif clinical_data:
            recommendation = f"Review the {len(clinical_data['references'])} detailed trial summaries below."
        elif market_data:
            web_count = len(market_data.get('web_results', []))
            rag_count = len(market_data.get('rag_results', []))
            market_total = web_count + rag_count
            recommendation = (
                f"Review {market_total} market intelligence sources ({web_count} web + {rag_count} internal). "
                f"Confidence: {market_data['confidence']['level']} ({market_data['confidence']['score']:.0%})."
            )
        else:
            recommendation = "No recommendations available"

        # 4. MERGE REFERENCES WITH STRICT SCHEMA ENFORCEMENT
        references = []

        # Add clinical references with defensive agentId check
        if clinical_data:
            clinical_refs = clinical_data.get('references', [])
            for ref in clinical_refs:
                # CRITICAL: Ensure every reference has agentId set
                if 'agentId' not in ref or ref['agentId'] != 'clinical':
                    logger.warning(f"Clinical reference missing or incorrect agentId: {ref.get('title', 'unknown')}")
                    ref['agentId'] = 'clinical'
                references.append(ref)
            logger.info(f"Added {len(clinical_refs)} clinical references")

        # Add market references (convert web results AND RAG results to reference format)
        if market_data:
            market_refs = []

            # Add web search results as references with domain tier quality indicator
            for web_result in market_data.get('web_results', []):
                url = web_result.get('url', '')
                domain_tier = web_result.get('domain_tier', 2)

                # Determine relevance score based on tier
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
                    "domain_tier": domain_tier
                })

            # CRITICAL: Also add RAG results as references (internal knowledge base)
            for rag_result in market_data.get('rag_results', []):
                market_refs.append({
                    "type": "market-report",
                    "title": rag_result.get('metadata', {}).get('title', 'Internal Market Intelligence'),
                    "source": "Internal Knowledge Base",
                    "date": rag_result.get('metadata', {}).get('date', '2024'),
                    "url": "",
                    "relevance": 90,
                    "agentId": "market",
                    "summary": rag_result.get('content', '')[:500]
                })

            references.extend(market_refs)
            web_count = len(market_data.get('web_results', []))
            rag_count = len(market_data.get('rag_results', []))
            logger.info(f"Added {web_count} web + {rag_count} RAG = {len(market_refs)} total market references")
            print(f"      → Market references: {web_count} web + {rag_count} RAG = {len(market_refs)} total")

        # 5. CALCULATE AGGREGATE CONFIDENCE
        if clinical_data and market_data:
            aggregate_confidence = (95 + market_data['confidence']['score'] * 100) / 2
        elif market_data:
            aggregate_confidence = market_data['confidence']['score'] * 100
        else:
            aggregate_confidence = 95

        # 6. BUILD UNIFIED RESPONSE
        response = {
            # Backward-compatible fields (existing API contract)
            "summary": summary,
            "insights": insights,
            "recommendation": recommendation,
            "timelineSaved": "6-8 hours",
            "references": references,

            # New additive fields (non-breaking)
            "confidence_score": aggregate_confidence,
            "active_agents": list(results.keys()),
            "agent_execution_status": execution_status,  # Detailed execution tracking for UI
            "market_intelligence": market_data if market_data else None,
            "patent_intelligence": results.get('patent', {}) if 'patent' in results else None,
            "total_trials": clinical_data.get('total_trials', 0) if clinical_data else 0
        }

        logger.info(f"🔀 Fusion complete: {len(references)} references, {len(insights)} insights")

        return response

    def _synthesize_overview_summary(self, query: str, clinical_data: Dict[str, Any], market_data: Dict[str, Any]) -> str:
        """
        Generate intelligent overview summary by synthesizing insights from all agents.

        This is executed AFTER all agents complete, ensuring comprehensive synthesis.
        Uses LLM to create a coherent, evidence-backed summary.
        
        FIXED: Now correctly prioritizes multi-agent synthesis over single-agent summaries
        FIXED: Added retry logic for rate limit errors (429) and Groq fallback
        """
        # Check what data we have
        has_clinical = bool(clinical_data and clinical_data.get('total_trials', 0) > 0)
        has_market = bool(market_data and market_data.get('sections', {}).get('summary'))
        
        logger.info(f"Overview synthesis: clinical={has_clinical}, market={has_market}")
        
        # If BOTH agents ran successfully, synthesize intelligently
        if has_clinical and has_market:
            logger.info("🔀 Both agents completed - generating multi-agent synthesis")
            
            clinical_summary = clinical_data.get('comprehensive_summary', clinical_data.get('summary', ''))
            clinical_trial_count = clinical_data.get('total_trials', 0)
            
            market_summary = market_data['sections']['summary']
            market_confidence = market_data['confidence']['level']
            web_source_count = len(market_data.get('web_results', []))
            
            # Try Gemini first (with retry for rate limits), then fall back to Groq, then concatenation
            import time
            
            # Attempt 1: Gemini with retry
            gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if gemini_api_key:
                for attempt in range(2):  # Max 2 attempts
                    try:
                        import requests
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={gemini_api_key}"
                        
                        synthesis_prompt = f"""You are a pharmaceutical intelligence analyst synthesizing insights from multiple specialized research agents.

QUERY: {query}

CLINICAL INTELLIGENCE ({clinical_trial_count} trials analyzed):
{clinical_summary[:3000]}

MARKET INTELLIGENCE ({web_source_count} sources, {market_confidence} confidence):
{market_summary[:3000]}

Create a comprehensive executive overview (300-400 words) that:
1. Synthesizes key insights from BOTH clinical and market perspectives
2. Highlights critical intersections (e.g., how clinical trial outcomes inform market potential)
3. Provides actionable intelligence for decision-makers
4. Balances clinical evidence with market dynamics

Write in clear paragraphs. Do NOT simply concatenate the summaries - synthesize intelligently by drawing connections between clinical and market data."""

                        payload = {
                            "contents": [{
                                "parts": [{"text": synthesis_prompt}]
                            }],
                            "generationConfig": {
                                "temperature": 0.5,
                                "maxOutputTokens": 2000
                            }
                        }
                        
                        response = requests.post(url, json=payload, timeout=60)
                        
                        # Check for rate limit error
                        if response.status_code == 429:
                            if attempt == 0:
                                logger.warning(f"Gemini rate limit hit (attempt {attempt + 1}/2), retrying in 2s...")
                                time.sleep(2)
                                continue
                            else:
                                logger.warning("Gemini rate limit exhausted after retries, falling back to Groq")
                                break
                        
                        response.raise_for_status()
                        
                        result = response.json()
                        synthesized = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        
                        if synthesized and len(synthesized) > 100:
                            logger.info("✅ Multi-agent overview synthesis completed with Gemini")
                            return synthesized.strip()
                        else:
                            logger.warning("Gemini synthesis too short or empty")
                            break
                            
                    except Exception as e:
                        logger.error(f"Gemini synthesis attempt {attempt + 1} failed: {e}")
                        if attempt == 0:
                            time.sleep(1)
                            continue
                        break
            
            # Attempt 2: Fall back to Groq
            groq_api_key = os.getenv('GROQ_API_KEY')
            if groq_api_key:
                try:
                    logger.info("Attempting overview synthesis with Groq fallback...")
                    
                    from config.llm.llm_config_sync import generate_llm_response
                    
                    synthesis_prompt = f"""Synthesize a comprehensive overview from both clinical and market intelligence.

Query: {query}

Clinical Findings ({clinical_trial_count} trials):
{clinical_summary[:2000]}

Market Findings ({web_source_count} sources, {market_confidence} confidence):
{market_summary[:2000]}

Create a 200-300 word executive overview that combines both perspectives. Focus on actionable insights."""
                    
                    synthesized = generate_llm_response(
                        prompt=synthesis_prompt,
                        system_prompt="You are a pharmaceutical intelligence analyst. Synthesize clinical and market insights.",
                        temperature=0.5,
                        max_tokens=1500
                    )
                    
                    if synthesized and len(synthesized) > 100:
                        logger.info("✅ Multi-agent overview synthesis completed with Groq fallback")
                        return synthesized.strip()
                        
                except Exception as e:
                    logger.error(f"Groq fallback also failed: {e}")
            
            # Final fallback: Structured concatenation
            logger.warning("All LLM synthesis failed, using structured concatenation")
            return f"""**Overview: {query}**

**Clinical Perspective** ({clinical_trial_count} trials analyzed):
{clinical_summary[:1500]}

**Market Perspective** ({web_source_count} sources, {market_confidence} confidence):
{market_summary[:1500]}

This analysis combines clinical trial evidence with market intelligence to provide comprehensive therapeutic insights."""
        
        # Only clinical data available
        elif has_clinical and not has_market:
            logger.info("📊 Clinical-only query - returning clinical summary")
            return clinical_data.get('comprehensive_summary', clinical_data.get('summary', 'No clinical data available'))
        
        # Only market data available
        elif has_market and not has_clinical:
            logger.info("📊 Market-only query - returning market summary")
            return market_data['sections']['summary']
        
        # No data from either agent
        else:
            logger.warning("⚠️ No data from any agent")
            return "No data available from agents. Please check agent configurations and API keys."
