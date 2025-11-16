# backend/agents/master_agent.py

from langchain.agents import AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import Dict, List
import asyncio

class MasterAgent:
    """
    Coordinates all worker agents and synthesizes final output
    """
    
    def __init__(self, llm_model="gpt-4"):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.3)
        self.worker_agents = {
            'market': MarketAgent(),
            'clinical': ClinicalAgent(),
            'patent': PatentAgent(),
            'trade': TradeAgent()
        }
        
    async def process_query(self, user_query: str) -> Dict:
        """
        Main orchestration logic
        """
        # Step 1: Analyze query and determine relevant agents
        required_agents = await self._analyze_query(user_query)
        
        # Step 2: Dispatch tasks to worker agents in parallel
        agent_results = await self._dispatch_agents(user_query, required_agents)
        
        # Step 3: Synthesize results using LLM
        final_report = await self._synthesize_results(user_query, agent_results)
        
        return final_report
    
    async def _analyze_query(self, query: str) -> List[str]:
        """
        Determine which agents are needed for this query
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a pharmaceutical research coordinator.
            Analyze the query and determine which data sources are needed:
            - market: Market size, CAGR, competitive landscape
            - clinical: Clinical trials, efficacy data, safety
            - patent: IP status, FTO, patent expiry
            - trade: Import/export data, API dependencies
            
            Return a JSON list of required agents."""),
            ("user", "{query}")
        ])
        
        response = await self.llm.ainvoke(prompt.format(query=query))
        # Parse response and return agent list
        return ['market', 'clinical', 'patent', 'trade']  # Simplified
    
    async def _dispatch_agents(self, query: str, agents: List[str]) -> Dict:
        """
        Execute all required agents in parallel
        """
        tasks = []
        for agent_name in agents:
            agent = self.worker_agents[agent_name]
            tasks.append(agent.execute(query))
        
        results = await asyncio.gather(*tasks)
        return dict(zip(agents, results))
    
    async def _synthesize_results(self, query: str, agent_results: Dict) -> Dict:
        """
        Combine all agent outputs into coherent report
        """
        synthesis_prompt = f"""
        Original Query: {query}
        
        Agent Findings:
        {self._format_agent_results(agent_results)}
        
        Provide a structured analysis with:
        1. Executive summary
        2. Key insights from each domain
        3. Cross-domain patterns
        4. Strategic recommendations
        5. Risk assessment
        """
        
        response = await self.llm.ainvoke(synthesis_prompt)
        
        return {
            'query': query,
            'agent_results': agent_results,
            'synthesis': response.content,
            'metadata': {
                'agents_used': list(agent_results.keys()),
                'processing_time': '2.3s'
            }
        }