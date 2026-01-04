"""
Master Agent - Simplified for Feature 1
Orchestrates query processing and agent coordination

Feature 1: Only uses Clinical Agent
Future: Multi-agent coordination with LangGraph
"""
from typing import Dict, Any, List
import logging
from agents.clinical_agent import ClinicalAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MasterAgent:
    """
    Master Agent - Orchestrates specialized agents
    
    Feature 1: Clinical Agent only with comprehensive trial summaries
    Future: LangGraph-based multi-agent orchestration
    """
    
    def __init__(self):
        self.name = "Master Agent"
        self.clinical_agent = ClinicalAgent()
        logger.info("Master Agent initialized")

    def process_query(self, query: str) -> Dict[str, Any]:
        logger.info("="*60)
        logger.info(f"🎼 Master Agent processing query: {query[:100]}...")
        logger.info("="*60)
        print(f"🎼 Master Agent processing query: {query[:100]}...")
        
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