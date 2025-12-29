# Trade Data Agent with Mock Data

from typing import Dict, Any, List

# --- MOCK DATA ---
MOCK_TRADE_DATA: Dict[str, Dict[str, Any]] = {
    "glp-1": {
        "api_imports": {
            "india": {
                "2023": {"volume_kg": 1250, "value_usd": 45000000, "top_sources": ["China", "Denmark"]},
                "2024": {"volume_kg": 1890, "value_usd": 68000000, "top_sources": ["China", "Denmark"]}
            }
        },
        "finished_product_exports": {
            "india": {
                "2023": {"value_usd": 23000000, "top_destinations": ["USA", "UK", "Germany"]}
            }
        },
        "supply_chain_risk": {
            "china_dependency": "78%",
            "alternative_sources": ["Italy", "USA"],
            "lead_time_days": 45
        }
    },
    "alzheimer": {
        "api_imports": {
            "india": {
                "2023": {"volume_kg": 400, "value_usd": 12000000, "top_sources": ["USA", "Germany"]},
                "2024": {"volume_kg": 520, "value_usd": 17000000, "top_sources": ["USA", "Germany"]}
            }
        },
        "finished_product_exports": {
            "india": {
                "2023": {"value_usd": 8000000, "top_destinations": ["USA", "Japan"]}
            }
        },
        "supply_chain_risk": {
            "china_dependency": "22%",
            "alternative_sources": ["France", "UK"],
            "lead_time_days": 60
        }
    },
    "oncology": {
        "api_imports": {
            "india": {
                "2023": {"volume_kg": 900, "value_usd": 35000000, "top_sources": ["Switzerland", "China"]},
                "2024": {"volume_kg": 1100, "value_usd": 42000000, "top_sources": ["Switzerland", "China"]}
            }
        },
        "finished_product_exports": {
            "india": {
                "2023": {"value_usd": 27000000, "top_destinations": ["USA", "Brazil", "Russia"]}
            }
        },
        "supply_chain_risk": {
            "china_dependency": "41%",
            "alternative_sources": ["Germany", "USA"],
            "lead_time_days": 38
        }
    }
}

TRADE_INSIGHTS: Dict[str, Dict[str, Any]] = {
    "diabetes": {
        "market_access": ["India has strong generics capability", "US imports 45% from India"],
        "tariff_info": "0% import duty under pharma agreement",
        "regulatory_barriers": "FDA inspection required for US export"
    },
    "oncology": {
        "market_access": ["Growing demand in Latin America", "EU has strict labeling laws"],
        "tariff_info": "5% import duty in Brazil",
        "regulatory_barriers": "ANVISA approval required for Brazil"
    }
}

# --- Helper Functions ---
def _get_trade_data(category: str) -> Dict[str, Any]:
    return MOCK_TRADE_DATA.get(category, {})

def _get_trade_insights(category: str) -> Dict[str, Any]:
    return TRADE_INSIGHTS.get(category, {})

# --- Agent Class ---
class TradeAgent:
    @staticmethod
    def process(query: str) -> Dict[str, Any]:
        category = None
        query_lower = query.lower()
        for cat in MOCK_TRADE_DATA.keys():
            if cat in query_lower:
                category = cat
                break
        if not category:
            for k in ["glp-1", "alzheimer", "oncology"]:
                if k in query_lower:
                    category = k
                    break
        if not category:
            return {"summary": "No relevant trade data found.", "trade_data": {}, "insights": {}}
        trade_data = _get_trade_data(category)
        # Map to insights category (e.g., glp-1 → diabetes)
        insights_category = "diabetes" if category == "glp-1" else category
        insights = _get_trade_insights(insights_category)
        summary = f"Trade data for {category}: "
        if trade_data:
            if "api_imports" in trade_data:
                summary += f"API imports for India in 2023: {trade_data['api_imports']['india']['2023']['volume_kg']} kg, "
                summary += f"value ${trade_data['api_imports']['india']['2023']['value_usd']}. "
            if "finished_product_exports" in trade_data:
                summary += f"Finished product exports from India in 2023: ${trade_data['finished_product_exports']['india']['2023']['value_usd']}. "
            if "supply_chain_risk" in trade_data:
                summary += f"China dependency: {trade_data['supply_chain_risk']['china_dependency']}. "
        else:
            summary += "No data available."
        return {
            "summary": summary,
            "trade_data": trade_data,
            "insights": insights,
        }
