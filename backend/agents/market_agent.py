# backend/agents/market_agent.py

from langchain.tools import Tool
import aiohttp
import pandas as pd

class MarketAgent:
    """
    Retrieves and analyzes market data from IQVIA and similar sources
    """
    
    def __init__(self):
        self.tools = [
            Tool(
                name="IQVIA_Query",
                func=self._query_iqvia,
                description="Query IQVIA for market size, trends, CAGR"
            ),
            Tool(
                name="Market_Analysis",
                func=self._analyze_market_data,
                description="Analyze competitive landscape"
            )
        ]
    
    async def execute(self, query: str) -> Dict:
        """
        Main execution logic for market intelligence
        """
        # Extract therapeutic area from query
        therapy_area = self._extract_therapy_area(query)
        
        # Fetch market data
        market_data = await self._query_iqvia(therapy_area)
        
        # Analyze trends
        analysis = self._analyze_market_data(market_data)
        
        return {
            'agent': 'market',
            'raw_data': market_data,
            'analysis': analysis,
            'confidence': 0.92
        }
    
    async def _query_iqvia(self, therapy_area: str) -> pd.DataFrame:
        """
        Query IQVIA API or mock data
        """
        # For demo, return mock data
        # In production, integrate with IQVIA API
        return pd.DataFrame({
            'year': [2022, 2023, 2024],
            'market_size_usd': [8.5e9, 10.2e9, 12.5e9],
            'cagr': [15.2, 15.8, 16.1]
        })
    
    def _analyze_market_data(self, data: pd.DataFrame) -> str:
        """
        Perform statistical analysis on market data
        """
        cagr = data['cagr'].mean()
        growth = ((data['market_size_usd'].iloc[-1] / 
                   data['market_size_usd'].iloc[0]) - 1) * 100
        
        return f"Market growing at {cagr:.1f}% CAGR with {growth:.1f}% total growth"