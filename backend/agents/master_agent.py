"""
Master Agent - Simplified for Feature 1
Orchestrates query processing and agent coordination

Feature 1: Clinical Agent, Patent Agent, and Market Agent
Future: Multi-agent coordination with LangGraph
"""
from typing import Dict, Any, List
import logging
from agents.clinical_agent import ClinicalAgent
from agents.patent_agent import PatentAgent
from agents.market_agent_hybrid import MarketAgentHybrid

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
        logger.info("Master Agent initialized with Clinical, Patent, and Market agents")

    def _detect_query_type(self, query: str) -> str:
        """
        Detect query type based on keywords

        Args:
            query: User query

        Returns:
            Query type: 'patent', 'market', 'clinical' (default)
        """
        query_lower = query.lower()

        # Patent-related keywords
        patent_keywords = [
            'patent', 'ip', 'intellectual property', 'fto', 'freedom to operate',
            'patent landscape', 'patent expir', 'licensing', 'patent cliff',
            'white space', 'patent strategy', 'ip strategy', 'patent portfolio',
            'patent litigation', 'patent protection', 'exclusivity'
        ]

        # Market-related keywords
        market_keywords = [
            'market', 'market size', 'market share', 'forecast', 'cagr',
            'revenue', 'sales', 'commercial', 'pricing', 'reimbursement',
            'competitive landscape', 'market dynamics', 'market opportunity',
            'market analysis', 'market trends', 'market growth', 'market intelligence',
            'blockbuster', 'peak sales', 'market leader', 'market outlook'
        ]

        if any(keyword in query_lower for keyword in patent_keywords):
            return 'patent'

        if any(keyword in query_lower for keyword in market_keywords):
            return 'market'

        # Default to clinical
        return 'clinical'

    def process_query(self, query: str) -> Dict[str, Any]:
        logger.info("="*60)
        logger.info(f"🎼 Master Agent processing query: {query[:100]}...")
        logger.info("="*60)
        print(f"🎼 Master Agent processing query: {query[:100]}...")

        # Detect query type
        query_type = self._detect_query_type(query)
        logger.info(f"🔍 Query type detected: {query_type}")
        print(f"   🔍 Query type: {query_type}")

        if query_type == 'patent':
            return self._process_patent_query(query)
        elif query_type == 'market':
            return self._process_market_query(query)
        else:
            return self._process_clinical_query(query)

    def _process_clinical_query(self, query: str) -> Dict[str, Any]:
        """Process clinical trials query"""
        logger.info("🏥 Delegating to Clinical Agent...")
        print(f"   🏥 Calling Clinical Agent...")

        # Get clinical trials data
        clinical_result = self.clinical_agent.process(query)
        
        # Get detailed summaries for each trial
        trial_count = len(clinical_result.get('trials', []))
        logger.info(f"📄 Fetching detailed summaries for all {trial_count} trials...")
        print(f"   📄 Fetching detailed summaries for trials...")
        references = []
        for i, trial in enumerate(clinical_result.get('trials', []), 1):
            try:
                logger.info(f"   Fetching trial {i}/{trial_count}: {trial['nct_id']}")
                trial_summary = self.clinical_agent.get_trial_summary(trial['nct_id'])
                references.append({
                    "type": "clinical-trial",
                    "title": trial_summary['title'],
                    "source": f"ClinicalTrials.gov {trial_summary['nct_id']}",
                    "date": "2024",  # You can extract actual date from trial details if needed
                    "url": f"https://clinicaltrials.gov/study/{trial_summary['nct_id']}",
                    "relevance": 90,
                    "agentId": "clinical",
                    "nct_id": trial_summary['nct_id'],
                    "summary": trial_summary['summary']
                })
            except Exception as e:
                logger.warning(f"Failed to fetch summary for {trial['nct_id']}: {e}")
                print(f"   ⚠️  Failed to fetch summary for {trial['nct_id']}: {e}")
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
        
        # Create insights
        insights = [{
            "agent": "Clinical Trials Agent",
            "finding": clinical_result.get('comprehensive_summary', clinical_result.get('summary', 'No data available')),
            "confidence": 95,
            "total_trials": len(clinical_result.get('trials', []))
        }]
        
        logger.info(f"✅ Master Agent completed processing")
        logger.info(f"   Total trials found: {trial_count}")
        logger.info(f"   Detailed summaries retrieved: {len(references)}")
        logger.info("="*60)
        
        return {
            "summary": clinical_result.get('comprehensive_summary', clinical_result.get('summary', 'No data available')),
            "insights": insights,
            "recommendation": f"Review the {len(references)} detailed trial summaries below for comprehensive information.",
            "timelineSaved": "6-8 hours",
            "references": references,
            "total_trials": len(clinical_result.get('trials', []))
        }

    def _process_patent_query(self, query: str) -> Dict[str, Any]:
        """Process patent intelligence query"""
        logger.info("📄 Delegating to Patent Agent...")
        print(f"   📄 Calling Patent Agent...")

        # Get patent intelligence data
        patent_result = self.patent_agent.process(query)

        # Extract key patent data
        patents = patent_result.get('patents', [])
        landscape = patent_result.get('landscape', {})
        fto_assessment = patent_result.get('fto_assessment', {})
        expiring_analysis = patent_result.get('expiring_analysis', {})

        # Create references from patents
        logger.info(f"📄 Processing {len(patents)} patent records...")
        print(f"   📄 Processing {len(patents)} patents...")
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

        # Create insights
        key_players = [p['organization'] for p in landscape.get('key_players', [])[:5]]
        insights = [{
            "agent": "Patent Intelligence Agent",
            "finding": patent_result.get('comprehensive_summary', patent_result.get('summary', 'No data available')),
            "confidence": int(patent_result.get('confidence_score', 0.85) * 100),
            "total_patents": len(patents),
            "fto_risk": fto_assessment.get('risk_level', 'Unknown'),
            "litigation_risk": patent_result.get('litigation_risk', 'Unknown'),
            "white_space_opportunities": len(patent_result.get('white_space', []))
        }]

        # Create strategic recommendations
        recommendations = []
        recommendations.append(f"Found {len(patents)} relevant patents in this technology space.")

        if fto_assessment.get('risk_level') == 'High':
            recommendations.append("⚠️ High FTO risk detected - detailed patent clearance recommended before proceeding.")
        elif fto_assessment.get('risk_level') == 'Medium':
            recommendations.append("⚠️ Moderate FTO risk - careful analysis of blocking patents required.")

        if expiring_analysis.get('count', 0) > 0:
            recommendations.append(f"📅 {expiring_analysis['count']} patents expiring in next 3 years - potential generic/biosimilar opportunities.")

        if patent_result.get('white_space'):
            recommendations.append(f"💡 {len(patent_result['white_space'])} white space opportunities identified for innovation.")

        recommendation_text = " ".join(recommendations)

        logger.info(f"✅ Master Agent completed patent processing")
        logger.info(f"   Total patents found: {len(patents)}")
        logger.info(f"   FTO Risk: {fto_assessment.get('risk_level', 'Unknown')}")
        logger.info(f"   Key players: {', '.join(key_players[:3])}")
        logger.info("="*60)

        return {
            "summary": patent_result.get('comprehensive_summary', patent_result.get('summary', 'No data available')),
            "insights": insights,
            "recommendation": recommendation_text,
            "timelineSaved": "4-6 hours",
            "references": references,
            "total_patents": len(patents),
            "landscape": landscape,
            "fto_assessment": fto_assessment,
            "patent_metrics": {
                "total_patents": landscape.get('total_patents', 0),
                "active_patents": landscape.get('active_patents', 0),
                "key_players": key_players,
                "fto_risk": fto_assessment.get('risk_level', 'Unknown'),
                "litigation_risk": patent_result.get('litigation_risk', 'Unknown'),
                "white_space": patent_result.get('white_space', []),
                "expiring_count": expiring_analysis.get('count', 0)
            }
        }

    def _process_market_query(self, query: str) -> Dict[str, Any]:
        """Process market intelligence query"""
        logger.info("📊 Delegating to Market Agent...")
        print(f"   📊 Calling Market Agent...")

        # Get market intelligence data
        market_result = self.market_agent.process(query)

        # Extract sections
        sections = market_result.get('sections', {})
        confidence = market_result.get('confidence', {})
        web_results = market_result.get('web_results', [])
        rag_results = market_result.get('rag_results', [])

        # Create references from web and RAG results
        logger.info(f"📊 Processing {len(web_results)} web sources and {len(rag_results)} RAG documents...")
        print(f"   📊 Processing {len(web_results)} web + {len(rag_results)} RAG sources...")
        references = []

        # Add web results
        for i, result in enumerate(web_results[:15], 1):  # Top 15 web sources
            references.append({
                "type": "market-report",
                "title": result.get('title', 'No title'),
                "source": result.get('url', 'Unknown source'),
                "date": result.get('date', 'N/A'),
                "url": result.get('url', ''),
                "relevance": 95 - i,  # Decreasing relevance
                "agentId": "market",
                "summary": result.get('snippet', 'No summary available')[:300]
            })

        # Add RAG results
        for i, result in enumerate(rag_results[:10], 1):  # Top 10 RAG documents
            references.append({
                "type": "market-report",
                "title": result.get('title', 'Internal Document'),
                "source": result.get('source', 'Internal Knowledge Base'),
                "date": 'N/A',
                "url": '',
                "relevance": 80 - i,  # Decreasing relevance
                "agentId": "market",
                "summary": result.get('snippet', 'No summary available')[:300]
            })

        # Create insights from market intelligence
        insights = [{
            "agent": "Market Intelligence Agent",
            "finding": sections.get('summary', 'No data available'),
            "confidence": int(confidence.get('score', 0.5) * 100),
            "confidence_level": confidence.get('level', 'medium'),
            "web_sources": len(web_results),
            "rag_sources": len(rag_results)
        }]

        # Create recommendations based on market intelligence
        recommendations = []
        if sections.get('market_overview'):
            recommendations.append("📈 Market overview analysis available in detailed sections.")

        if sections.get('drivers_and_trends'):
            recommendations.append("🔍 Key market drivers and trends identified.")

        if sections.get('competitive_landscape'):
            recommendations.append("🏢 Competitive landscape analysis included.")

        if confidence.get('level') in ['high', 'very_high']:
            recommendations.append(f"✅ High confidence ({confidence.get('score', 0)*100:.0f}%) - data quality is strong.")
        elif confidence.get('level') == 'low':
            recommendations.append(f"⚠️ Low confidence ({confidence.get('score', 0)*100:.0f}%) - consider additional data sources.")

        recommendation_text = " ".join(recommendations) if recommendations else "Review market intelligence sections for detailed analysis."

        logger.info(f"✅ Master Agent completed market intelligence processing")
        logger.info(f"   Web sources: {len(web_results)}")
        logger.info(f"   RAG sources: {len(rag_results)}")
        logger.info(f"   Confidence: {confidence.get('score', 0):.2%} ({confidence.get('level', 'unknown')})")
        logger.info("="*60)

        return {
            "summary": sections.get('summary', 'No market intelligence data available'),
            "insights": insights,
            "recommendation": recommendation_text,
            "timelineSaved": "3-5 hours",
            "references": references,
            "market_sections": {
                "market_overview": sections.get('market_overview', ''),
                "key_metrics": sections.get('key_metrics', ''),
                "drivers_and_trends": sections.get('drivers_and_trends', ''),
                "competitive_landscape": sections.get('competitive_landscape', ''),
                "risks_and_opportunities": sections.get('risks_and_opportunities', ''),
                "future_outlook": sections.get('future_outlook', '')
            },
            "confidence": confidence,
            "web_sources_count": len(web_results),
            "rag_sources_count": len(rag_results)
        }