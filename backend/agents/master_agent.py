"""
Master Agent - Simplified for Feature 1
Orchestrates query processing and agent coordination

Feature 1: Only uses Market Agent
Feature 2+: Will add multi-agent coordination with LangGraph
"""
from typing import Dict, Any, List
import asyncio
from agents.market_agent import MarketAgent
from config.llm.llm_config import generate_llm_response

class MasterAgent:
    """
    Master Agent - Orchestrates specialized agents
    
    Feature 1: Basic query routing to Market Agent
    Future: LangGraph-based multi-agent orchestration
    """
    
    def __init__(self):
        self.name = "Master Agent"
        
        # Initialize specialized agents
        # Feature 1: Only Market Agent
        self.market_agent = MarketAgent()
        
        # Feature 2+: Will add these
        # self.clinical_agent = ClinicalAgent()
        # self.patent_agent = PatentAgent()
        # self.trade_agent = TradeAgent()
        
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main query processing pipeline
        
        Feature 1 Flow:
        1. Receive query
        2. Route to Market Agent
        3. Format response for frontend
        
        Args:
            query: User's pharmaceutical intelligence query
            
        Returns:
            Formatted response matching frontend expectations
        """
        print(f"🎼 Master Agent processing query: {query[:100]}...")
        
        # Step 1: Classify query intent (simplified for Feature 1)
        intent = await self._classify_intent(query)
        print(f"   Intent: {intent}")
        
        # Step 2: Route to appropriate agent(s)
        # Feature 1: Always use Market Agent
        agent_results = await self._coordinate_agents(query, intent)
        
        # Step 3: Synthesize results into frontend format
        response = await self._synthesize_response(query, agent_results)
        
        print(f"✅ Master Agent completed. Insights: {len(response['insights'])}")
        
        return response
    
    async def _classify_intent(self, query: str) -> str:
        """
        Classify query intent
        
        Feature 1: Simplified - everything is 'market'
        Feature 2: Will use LLM to classify into multiple categories
        """
        query_lower = query.lower()
        
        # Simple keyword-based classification for Feature 1
        if any(word in query_lower for word in ['market', 'sales', 'revenue', 'forecast', 'glp-1', 'cagr']):
            return "market_intelligence"
        
        # Default to market intelligence in Feature 1
        return "market_intelligence"
    
    async def _coordinate_agents(self, query: str, intent: str) -> List[Dict[str, Any]]:
        """
        Coordinate specialized agents
        
        Feature 1: Only calls Market Agent
        Feature 2: Will call multiple agents in parallel
        """
        results = []
        
        # Feature 1: Only Market Agent
        print(f"   📊 Calling Market Agent...")
        market_result = await self.market_agent.process(query)
        results.append(market_result)
        
        # Feature 2: Will add parallel agent calls
        # tasks = [
        #     self.market_agent.process(query),
        #     self.clinical_agent.process(query),
        #     self.patent_agent.process(query),
        #     self.trade_agent.process(query)
        # ]
        # results = await asyncio.gather(*tasks)
        
        return results
    
    async def _synthesize_response(self, query: str, agent_results: List[Dict]) -> Dict[str, Any]:
        """
        Synthesize agent results into frontend-compatible format
        
        Converts agent outputs to match the QueryResponse schema:
        {
            summary: str,
            insights: List[Insight],
            recommendation: str,
            timelineSaved: str,
            references: List[Reference]
        }
        """
        # Extract insights from agent results
        insights = []
        all_references = []
        
        for result in agent_results:
            insights.append({
                "agent": result["agent"],
                "finding": result["finding"],
                "confidence": result["confidence"]
            })
            
            if "references" in result:
                all_references.extend(result["references"])
        
        # Generate summary using LLM
        summary = await self._generate_summary(query, insights)
        
        # Generate recommendation using LLM
        recommendation = await self._generate_recommendation(query, insights)
        
        # Calculate time saved
        timeline_saved = "8-10 hours"  # Mock for Feature 1
        
        return {
            "summary": summary,
            "insights": insights,
            "recommendation": recommendation,
            "timelineSaved": timeline_saved,
            "references": all_references
        }
    
    async def _generate_summary(self, query: str, insights: List[Dict]) -> str:
        """Generate executive summary of all insights"""
        insights_text = "\n".join([
            f"- {ins['agent']}: {ins['finding']}"
            for ins in insights
        ])
        
        prompt = f"""Create a concise executive summary (2-3 sentences) for this pharmaceutical intelligence query.

Query: {query}

Agent Insights:
{insights_text}

Summary should:
- Be professional and data-driven
- Highlight the most important finding
- Mention the scope of analysis"""
        
        system_prompt = "You are a pharmaceutical strategy consultant creating executive summaries."
        
        summary = await generate_llm_response(prompt, system_prompt)
        return summary.strip()
    
    async def _generate_recommendation(self, query: str, insights: List[Dict]) -> str:
        """Generate strategic recommendation based on insights"""
        insights_text = "\n".join([
            f"- {ins['agent']}: {ins['finding']}"
            for ins in insights
        ])
        
        prompt = f"""Based on the pharmaceutical intelligence analysis, provide a strategic recommendation (2-3 sentences).

Query: {query}

Insights:
{insights_text}

Recommendation should:
- Be actionable and specific
- Consider market dynamics
- Suggest next steps for decision-makers"""
        
        system_prompt = "You are a pharmaceutical strategy consultant providing recommendations."
        
        recommendation = await generate_llm_response(prompt, system_prompt)
        return recommendation.strip()