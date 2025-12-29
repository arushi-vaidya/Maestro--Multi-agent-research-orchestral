"""
Market Intelligence Agent
Provides pharmaceutical market data and analysis
Feature 1: Uses mock IQVIA-style data
"""
from typing import Dict, Any, List
import json
from config.llm.llm_config import generate_llm_response

class MarketAgent:
    """
    Market Intelligence Agent
    Analyzes pharmaceutical market data, trends, and opportunities
    """
    
    def __init__(self):
        self.name = "Market Intelligence Agent"
        self.agent_id = "market"
        self.data_source = "IQVIA Market Intelligence (Mock)"
        
    def get_system_prompt(self) -> str:
        """System prompt for market intelligence analysis"""
        return """You are a pharmaceutical market intelligence specialist with expertise in:
        - Market size analysis and forecasting
        - Competitive landscape assessment
        - Therapy area trends
        - Pricing and market access strategies
        - CAGR (Compound Annual Growth Rate) calculations
        
        Provide data-driven insights based on the market data provided.
        Always cite specific numbers and trends.
        Be concise but informative."""
    
    async def process(self, query: str) -> Dict[str, Any]:
        """
        Process market intelligence query
        
        Args:
            query: User query about pharmaceutical markets
            
        Returns:
            Dict with findings, confidence, and references
        """
        # Get relevant market data based on query keywords
        market_data = self._get_relevant_data(query)
        
        # Generate analysis using LLM
        analysis_prompt = self._create_analysis_prompt(query, market_data)
        
        analysis = await generate_llm_response(
            prompt=analysis_prompt,
            system_prompt=self.get_system_prompt()
        )
        
        # Extract insights and create structured response
        result = {
            "agent": self.name,
            "agent_id": self.agent_id,
            "finding": analysis,
            "confidence": self._calculate_confidence(query, market_data),
            "data_points": market_data,
            "references": self._generate_references(query)
        }
        
        return result
    
    def _get_relevant_data(self, query: str) -> Dict[str, Any]:
        """
        Retrieve relevant market data based on query
        In Feature 1, this is mock data. In Feature 3, this will query real IQVIA API
        """
        query_lower = query.lower()
        
        # Mock market data database
        market_database = {
            "glp-1": {
                "therapy_area": "Diabetes & Obesity",
                "market_size_usd": "23.5B",
                "cagr": "18.2%",
                "forecast_2030": "45.8B",
                "key_players": ["Novo Nordisk", "Eli Lilly", "AstraZeneca"],
                "top_products": {
                    "Ozempic": {"sales_2023": "14.2B", "growth": "59%"},
                    "Wegovy": {"sales_2023": "4.5B", "growth": "320%"},
                    "Mounjaro": {"sales_2023": "5.1B", "growth": "launched 2022"}
                },
                "regional_breakdown": {
                    "North America": "62%",
                    "Europe": "24%",
                    "Asia-Pacific": "11%",
                    "Rest of World": "3%"
                }
            },
            "diabetes": {
                "therapy_area": "Diabetes",
                "market_size_usd": "68.5B",
                "cagr": "9.3%",
                "forecast_2030": "112.4B",
                "key_players": ["Novo Nordisk", "Sanofi", "Eli Lilly"],
                "segments": {
                    "Insulin": "32.1B",
                    "GLP-1 agonists": "23.5B",
                    "SGLT2 inhibitors": "8.9B",
                    "DPP-4 inhibitors": "4.0B"
                }
            },
            "oncology": {
                "therapy_area": "Oncology",
                "market_size_usd": "185.3B",
                "cagr": "11.7%",
                "forecast_2030": "356.2B",
                "key_players": ["Roche", "Bristol Myers Squibb", "Merck"],
                "segments": {
                    "Immunotherapy": "78.2B",
                    "Targeted therapy": "62.1B",
                    "Chemotherapy": "32.5B",
                    "Hormone therapy": "12.5B"
                }
            },
            "alzheimer": {
                "therapy_area": "Neurology - Alzheimer's Disease",
                "market_size_usd": "4.8B",
                "cagr": "35.2%",
                "forecast_2030": "28.5B",
                "key_players": ["Biogen", "Eisai", "Eli Lilly"],
                "recent_launches": {
                    "Leqembi": {"approval": "2023", "mechanism": "Anti-amyloid"},
                    "Donanemab": {"status": "Phase 3", "expected_approval": "2024"}
                }
            },
            "crispr": {
                "therapy_area": "Gene Therapy",
                "market_size_usd": "2.1B",
                "cagr": "42.8%",
                "forecast_2030": "18.9B",
                "key_players": ["CRISPR Therapeutics", "Editas", "Intellia"],
                "pipeline_size": "78 trials globally"
            }
        }
        
        # Find relevant data
        relevant_data = {}
        for keyword, data in market_database.items():
            if keyword in query_lower:
                relevant_data[keyword] = data
        
        # If no specific match, return general pharmaceutical market data
        if not relevant_data:
            relevant_data = {
                "global_pharma": {
                    "market_size_usd": "1.48T",
                    "cagr": "6.8%",
                    "forecast_2030": "2.1T",
                    "top_therapy_areas": [
                        "Oncology (185.3B)",
                        "Immunology (92.1B)",
                        "Diabetes (68.5B)",
                        "Cardiovascular (54.3B)"
                    ]
                }
            }
        
        return relevant_data
    
    def _create_analysis_prompt(self, query: str, market_data: Dict) -> str:
        """Create analysis prompt for LLM"""
        data_str = json.dumps(market_data, indent=2)
        
        prompt = f"""Analyze the following pharmaceutical market query using the provided market data.

Query: {query}

Market Data:
{data_str}

Provide a concise market intelligence insight (2-3 sentences) that:
1. Answers the query directly with specific numbers
2. Highlights key market opportunities or trends
3. Mentions competitive dynamics if relevant

Keep it professional and data-driven."""
        
        return prompt
    
    def _calculate_confidence(self, query: str, market_data: Dict) -> int:
        """
        Calculate confidence score based on data availability
        Returns: Confidence score 0-100
        """
        if not market_data:
            return 60  # Low confidence with no specific data
        
        # Higher confidence if we have specific matching data
        if len(market_data) > 0:
            return 92  # High confidence with relevant data
        
        return 75  # Medium confidence
    
    def _generate_references(self, query: str) -> List[Dict[str, Any]]:
        """Generate mock references for market data"""
        query_lower = query.lower()
        
        references = []
        
        # Add relevant market report references based on query
        if "glp-1" in query_lower or "diabetes" in query_lower:
            references.append({
                "type": "market-report",
                "title": "Global GLP-1 Agonist Market Analysis 2024-2030",
                "source": "IQVIA Market Intelligence",
                "date": "2024-02-01",
                "url": "https://www.iqvia.com/insights/market-reports",
                "relevance": 95,
                "agentId": "market"
            })
            references.append({
                "type": "market-report",
                "title": "Diabetes Drug Market Size and Forecast",
                "source": "Grand View Research",
                "date": "2024-01-15",
                "url": "https://www.grandviewresearch.com",
                "relevance": 90,
                "agentId": "market"
            })
        
        if "oncology" in query_lower or "cancer" in query_lower:
            references.append({
                "type": "market-report",
                "title": "Global Oncology Drug Market Report 2024",
                "source": "IQVIA Oncology Trends",
                "date": "2024-03-01",
                "url": "https://www.iqvia.com/insights/oncology",
                "relevance": 94,
                "agentId": "market"
            })
        
        if "alzheimer" in query_lower:
            references.append({
                "type": "market-report",
                "title": "Alzheimer's Disease Therapeutics Market Outlook",
                "source": "Evaluate Pharma",
                "date": "2024-01-20",
                "url": "https://www.evaluate.com",
                "relevance": 93,
                "agentId": "market"
            })
        
        # Always include a general pharmaceutical market reference
        if not references:
            references.append({
                "type": "market-report",
                "title": "Global Pharmaceutical Market Report 2024",
                "source": "IQVIA Institute",
                "date": "2024-01-01",
                "url": "https://www.iqvia.com/insights/institute",
                "relevance": 85,
                "agentId": "market"
            })
        
        return references