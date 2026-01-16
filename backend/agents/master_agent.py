"""
Master Agent - Simplified for Feature 1
Orchestrates query processing and agent coordination

Feature 1: Clinical Agent and Patent Agent
Future: Multi-agent coordination with LangGraph
"""
from typing import Dict, Any, List
import logging
from agents.clinical_agent import ClinicalAgent
from agents.patent_agent import PatentAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MasterAgent:
    """
    Master Agent - Orchestrates specialized agents

    Features:
    - Clinical Agent: Clinical trials analysis
    - Patent Agent: Patent landscape, FTO, IP strategy
    Future: LangGraph-based multi-agent orchestration
    """

    def __init__(self):
        self.name = "Master Agent"
        self.clinical_agent = ClinicalAgent()
        self.patent_agent = PatentAgent()
        logger.info("Master Agent initialized with Clinical and Patent agents")

    def _detect_query_type(self, query: str) -> str:
        """
        Detect query type based on keywords

        Args:
            query: User query

        Returns:
            Query type: 'patent', 'clinical', or 'clinical' (default)
        """
        query_lower = query.lower()

        # Patent-related keywords
        patent_keywords = [
            'patent', 'ip', 'intellectual property', 'fto', 'freedom to operate',
            'patent landscape', 'patent expir', 'licensing', 'patent cliff',
            'white space', 'patent strategy', 'ip strategy', 'patent portfolio',
            'patent litigation', 'patent protection', 'exclusivity'
        ]

        if any(keyword in query_lower for keyword in patent_keywords):
            return 'patent'

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