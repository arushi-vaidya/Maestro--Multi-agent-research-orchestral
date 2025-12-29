# Web Intelligence Agent with Mock Data

from typing import Dict, Any, List

# --- MOCK DATA ---
MOCK_WEB_RESULTS: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "glp-1": {
        "news": [
            {
                "title": "FDA approves Zepbound for chronic weight management",
                "source": "FDA News Release",
                "date": "2024-11-15",
                "url": "https://www.fda.gov/news-events",
                "snippet": "FDA has approved Zepbound (tirzepatide) for chronic weight management..."
            }
        ],
        "pubmed": [
            {
                "pmid": "38234567",
                "title": "Efficacy of GLP-1 agonists in Type 2 Diabetes: Meta-Analysis",
                "authors": ["Smith J", "Kumar R"],
                "journal": "Nature Medicine",
                "date": "2024-03-20",
                "abstract": "This meta-analysis of 45 RCTs...",
                "citations": 12
            }
        ],
        "regulatory": [
            {
                "title": "EMA recommends approval of semaglutide for new indication",
                "date": "2024-09-10",
                "source": "EMA"
            }
        ]
    },
    "alzheimer": {
        "news": [
            {
                "title": "Breakthrough in Alzheimer's early detection",
                "source": "Science Daily",
                "date": "2024-10-01",
                "url": "https://www.sciencedaily.com/releases/2024/10/011.htm",
                "snippet": "Researchers have developed a blood test for early Alzheimer's..."
            }
        ],
        "pubmed": [
            {
                "pmid": "38234999",
                "title": "Tau-targeting therapies in Alzheimer's: Current status",
                "authors": ["Lee A", "Patel S"],
                "journal": "JAMA Neurology",
                "date": "2024-05-10",
                "abstract": "Review of tau-targeting drugs in clinical trials...",
                "citations": 7
            }
        ],
        "regulatory": [
            {
                "title": "FDA grants fast track to new Alzheimer's drug",
                "date": "2024-08-12",
                "source": "FDA"
            }
        ]
    },
    "oncology": {
        "news": [
            {
                "title": "Immunotherapy combination shows promise in lung cancer",
                "source": "Oncology Times",
                "date": "2024-07-22",
                "url": "https://www.oncology-times.com/news/2024/07/22/oncology-combo.htm",
                "snippet": "A new combination of checkpoint inhibitors..."
            }
        ],
        "pubmed": [
            {
                "pmid": "38235555",
                "title": "Checkpoint inhibitors in NSCLC: Real-world outcomes",
                "authors": ["Garcia M", "Wong T"],
                "journal": "Lancet Oncology",
                "date": "2024-06-15",
                "abstract": "Analysis of NSCLC patients treated with checkpoint inhibitors...",
                "citations": 15
            }
        ],
        "regulatory": [
            {
                "title": "NICE updates guidance on immunotherapy",
                "date": "2024-09-30",
                "source": "NICE"
            }
        ]
    }
}

# --- Helper Functions ---
def _get_web_results(category: str) -> Dict[str, List[Dict[str, Any]]]:
    return MOCK_WEB_RESULTS.get(category, {})

# --- Agent Class ---
class WebAgent:
    @staticmethod
    def process(query: str) -> Dict[str, Any]:
        category = None
        query_lower = query.lower()
        for cat in MOCK_WEB_RESULTS.keys():
            if cat in query_lower:
                category = cat
                break
        if not category:
            for k in ["glp-1", "alzheimer", "oncology"]:
                if k in query_lower:
                    category = k
                    break
        if not category:
            return {"summary": "No relevant web intelligence found.", "web_results": {}}
        web_results = _get_web_results(category)
        summary = f"Recent news and publications for {category}: "
        if web_results:
            if web_results.get("news"):
                summary += f"Top news: {web_results['news'][0]['title']} ({web_results['news'][0]['date']}). "
            if web_results.get("pubmed"):
                summary += f"Recent paper: {web_results['pubmed'][0]['title']} ({web_results['pubmed'][0]['date']}). "
            if web_results.get("regulatory"):
                summary += f"Regulatory update: {web_results['regulatory'][0]['title']} ({web_results['regulatory'][0]['date']})."
        else:
            summary += "No data available."
        return {
            "summary": summary,
            "web_results": web_results,
        }
