# Patent Agent with Mock Data

from typing import List, Dict, Any
import random
from datetime import date, timedelta

# --- MOCK DATA ---
MOCK_PATENTS: Dict[str, List[Dict[str, Any]]] = {
    "glp-1": [
        {
            "patent_number": f"US11{random.randint(1000000,9999999)}B2",
            "title": f"Methods for GLP-1 receptor agonist synthesis (Patent {i+1})",
            "assignee": random.choice(["Novo Nordisk A/S", "Eli Lilly", "AstraZeneca"]),
            "filing_date": str(date(2015, 1, 1) + timedelta(days=365*i)),
            "grant_date": str(date(2020, 1, 1) + timedelta(days=365*i)),
            "expiration_date": str(date(2035, 1, 1) + timedelta(days=365*i)),
            "claims_count": random.randint(10, 40),
            "citations_received": random.randint(5, 30),
            "family_size": random.randint(2, 10),
            "legal_status": random.choice(["Active", "Expired", "Pending"]),
            "classification": "A61K38/26"
        } for i in range(18)
    ],
    "alzheimer": [
        {
            "patent_number": f"US12{random.randint(1000000,9999999)}B2",
            "title": f"Therapeutics for Alzheimer's Disease (Patent {i+1})",
            "assignee": random.choice(["Biogen", "Eisai", "Roche"]),
            "filing_date": str(date(2014, 6, 1) + timedelta(days=400*i)),
            "grant_date": str(date(2019, 6, 1) + timedelta(days=400*i)),
            "expiration_date": str(date(2034, 6, 1) + timedelta(days=400*i)),
            "claims_count": random.randint(8, 35),
            "citations_received": random.randint(2, 25),
            "family_size": random.randint(1, 7),
            "legal_status": random.choice(["Active", "Expired", "Pending"]),
            "classification": "A61K31/00"
        } for i in range(16)
    ],
    "crispr": [
        {
            "patent_number": f"US13{random.randint(1000000,9999999)}B2",
            "title": f"CRISPR Gene Editing Methods (Patent {i+1})",
            "assignee": random.choice(["Editas Medicine", "CRISPR Therapeutics", "Intellia"]),
            "filing_date": str(date(2016, 3, 1) + timedelta(days=300*i)),
            "grant_date": str(date(2021, 3, 1) + timedelta(days=300*i)),
            "expiration_date": str(date(2036, 3, 1) + timedelta(days=300*i)),
            "claims_count": random.randint(12, 38),
            "citations_received": random.randint(3, 20),
            "family_size": random.randint(2, 9),
            "legal_status": random.choice(["Active", "Expired", "Pending"]),
            "classification": "C12N15/113"
        } for i in range(17)
    ],
    "oncology": [
        {
            "patent_number": f"US14{random.randint(1000000,9999999)}B2",
            "title": f"Immunotherapy for Cancer (Patent {i+1})",
            "assignee": random.choice(["Merck", "Bristol-Myers Squibb", "Roche"]),
            "filing_date": str(date(2013, 9, 1) + timedelta(days=350*i)),
            "grant_date": str(date(2018, 9, 1) + timedelta(days=350*i)),
            "expiration_date": str(date(2033, 9, 1) + timedelta(days=350*i)),
            "claims_count": random.randint(15, 45),
            "citations_received": random.randint(4, 28),
            "family_size": random.randint(3, 12),
            "legal_status": random.choice(["Active", "Expired", "Pending"]),
            "classification": "A61P35/00"
        } for i in range(19)
    ],
}

PATENT_LANDSCAPES: Dict[str, Dict[str, Any]] = {
    "glp-1": {
        "total_patents": 234,
        "active_patents": 187,
        "expiring_2024_2026": 23,
        "key_players": ["Novo Nordisk", "Eli Lilly", "AstraZeneca"],
        "white_space_areas": ["Oral delivery", "Once-monthly formulations"],
        "litigation_risk": "Medium"
    },
    "alzheimer": {
        "total_patents": 142,
        "active_patents": 98,
        "expiring_2024_2026": 12,
        "key_players": ["Biogen", "Eisai", "Roche"],
        "white_space_areas": ["Tau protein targeting", "Early diagnosis"],
        "litigation_risk": "Low"
    },
    "crispr": {
        "total_patents": 88,
        "active_patents": 70,
        "expiring_2024_2026": 7,
        "key_players": ["Editas Medicine", "CRISPR Therapeutics", "Intellia"],
        "white_space_areas": ["In vivo editing", "Delivery systems"],
        "litigation_risk": "High"
    },
    "oncology": {
        "total_patents": 312,
        "active_patents": 245,
        "expiring_2024_2026": 34,
        "key_players": ["Merck", "Bristol-Myers Squibb", "Roche"],
        "white_space_areas": ["Personalized vaccines", "Checkpoint inhibitors"],
        "litigation_risk": "Medium"
    },
}

# --- Analysis Functions ---
def _analyze_patent_landscape(category: str) -> Dict[str, Any]:
    return PATENT_LANDSCAPES.get(category, {})

def _check_freedom_to_operate(category: str) -> List[str]:
    landscape = PATENT_LANDSCAPES.get(category, {})
    return landscape.get("white_space_areas", [])

def _assess_expiration_cliff(category: str) -> Dict[str, Any]:
    landscape = PATENT_LANDSCAPES.get(category, {})
    return {
        "expiring_2024_2026": landscape.get("expiring_2024_2026", 0),
        "active_patents": landscape.get("active_patents", 0),
    }

def _identify_key_patents(category: str) -> List[Dict[str, Any]]:
    patents = MOCK_PATENTS.get(category, [])
    return sorted(patents, key=lambda x: x["citations_received"], reverse=True)[:5]

# --- Agent Class ---
class PatentAgent:
    @staticmethod
    def process(query: str) -> Dict[str, Any]:
        category = None
        query_lower = query.lower()
        for cat in MOCK_PATENTS.keys():
            if cat in query_lower:
                category = cat
                break
        if not category:
            for k in ["glp-1", "alzheimer", "crispr", "oncology"]:
                if k in query_lower:
                    category = k
                    break
        if not category:
            return {"summary": "No relevant patent data found.", "patents": [], "landscape": {}, "key_patents": []}
        patents = MOCK_PATENTS[category]
        landscape = _analyze_patent_landscape(category)
        white_space = _check_freedom_to_operate(category)
        expiration = _assess_expiration_cliff(category)
        key_patents = _identify_key_patents(category)
        summary = (
            f"Patent landscape for {category}: {landscape.get('total_patents', 0)} total, "
            f"{landscape.get('active_patents', 0)} active. Key players: {', '.join(landscape.get('key_players', []))}. "
            f"Litigation risk: {landscape.get('litigation_risk', 'Unknown')}. "
            f"White space: {', '.join(white_space)}. "
            f"Patents expiring 2024-2026: {expiration.get('expiring_2024_2026', 0)}."
        )
        return {
            "summary": summary,
            "patents": patents,
            "landscape": landscape,
            "key_patents": key_patents,
        }
