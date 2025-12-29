# Clinical Trials Agent with Mock Data

from typing import List, Dict, Any
import random
from datetime import date, timedelta

# --- MOCK DATA ---
MOCK_CLINICAL_TRIALS: Dict[str, List[Dict[str, Any]]] = {
    "GLP-1": [
        {
            "nct_id": f"NCT0{1000+i}",
            "title": f"Efficacy of GLP-1 Agonist in Type 2 Diabetes (Trial {i+1})",
            "phase": random.choice([1, 2, 3, 4]),
            "status": random.choice(["Recruiting", "Completed", "Terminated"]),
            "enrollment": random.randint(100, 2000),
            "start_date": str(date(2020, 1, 1) + timedelta(days=30*i)),
            "completion_date": str(date(2022, 1, 1) + timedelta(days=30*i)),
            "primary_outcome": "Change in HbA1c",
            "sponsor": random.choice(["Novo Nordisk", "Eli Lilly", "AstraZeneca"]),
            "location_count": random.randint(5, 50),
        } for i in range(25)
    ],
    "Alzheimer's": [
        {
            "nct_id": f"NCT1{1000+i}",
            "title": f"{drug} in Early Alzheimer's Disease (Trial {i+1})",
            "phase": random.choice([1, 2, 3]),
            "status": random.choice(["Recruiting", "Completed", "Terminated"]),
            "enrollment": random.randint(50, 1500),
            "start_date": str(date(2019, 6, 1) + timedelta(days=45*i)),
            "completion_date": str(date(2021, 6, 1) + timedelta(days=45*i)),
            "primary_outcome": "Cognitive function improvement",
            "sponsor": random.choice(["Eisai", "Biogen", "Roche"]),
            "location_count": random.randint(3, 30),
        } for i, drug in enumerate(["Leqembi", "Donanemab"]*13)
    ],
    "Oncology": [
        {
            "nct_id": f"NCT2{1000+i}",
            "title": f"{drug} for Advanced Cancer (Trial {i+1})",
            "phase": random.choice([1, 2, 3, 4]),
            "status": random.choice(["Recruiting", "Completed", "Terminated"]),
            "enrollment": random.randint(80, 3000),
            "start_date": str(date(2018, 3, 1) + timedelta(days=60*i)),
            "completion_date": str(date(2020, 3, 1) + timedelta(days=60*i)),
            "primary_outcome": "Progression-free survival",
            "sponsor": random.choice(["Merck", "Bristol-Myers Squibb"]),
            "location_count": random.randint(10, 100),
        } for i, drug in enumerate(["Keytruda", "Opdivo"]*15)
    ],
    "CRISPR": [
        {
            "nct_id": f"NCT3{1000+i}",
            "title": f"CRISPR Gene Editing for Rare Disease (Trial {i+1})",
            "phase": random.choice([1, 2]),
            "status": random.choice(["Recruiting", "Completed"]),
            "enrollment": random.randint(10, 200),
            "start_date": str(date(2021, 5, 1) + timedelta(days=90*i)),
            "completion_date": str(date(2023, 5, 1) + timedelta(days=90*i)),
            "primary_outcome": "Gene correction rate",
            "sponsor": random.choice(["CRISPR Therapeutics", "Editas Medicine"]),
            "location_count": random.randint(1, 10),
        } for i in range(20)
    ],
    "Rare Disease": [
        {
            "nct_id": f"NCT4{1000+i}",
            "title": f"Therapy for Rare Disease X (Trial {i+1})",
            "phase": random.choice([1, 2, 3]),
            "status": random.choice(["Recruiting", "Completed", "Terminated"]),
            "enrollment": random.randint(5, 300),
            "start_date": str(date(2017, 8, 1) + timedelta(days=120*i)),
            "completion_date": str(date(2019, 8, 1) + timedelta(days=120*i)),
            "primary_outcome": "Symptom reduction",
            "sponsor": random.choice(["RareGen", "Orphan Pharma"]),
            "location_count": random.randint(1, 8),
        } for i in range(22)
    ],
    "Cardiovascular": [
        {
            "nct_id": f"NCT5{1000+i}",
            "title": f"Cardiovascular Outcome Study (Trial {i+1})",
            "phase": random.choice([2, 3, 4]),
            "status": random.choice(["Recruiting", "Completed", "Terminated"]),
            "enrollment": random.randint(200, 5000),
            "start_date": str(date(2016, 2, 1) + timedelta(days=90*i)),
            "completion_date": str(date(2018, 2, 1) + timedelta(days=90*i)),
            "primary_outcome": "Major adverse cardiac events",
            "sponsor": random.choice(["Pfizer", "Novartis"]),
            "location_count": random.randint(10, 60),
        } for i in range(25)
    ],
}

# --- Helper Functions ---
def _get_relevant_trials(query: str) -> List[Dict[str, Any]]:
    query_lower = query.lower()
    relevant_trials = []
    for category, trials in MOCK_CLINICAL_TRIALS.items():
        if category.lower() in query_lower:
            relevant_trials.extend(trials)
        else:
            for keyword in ["ozempic", "wegovy", "mounjaro", "leqembi", "donanemab", "keytruda", "opdivo", "crispr"]:
                if keyword in query_lower and any(keyword in t["title"].lower() for t in trials):
                    relevant_trials.extend([t for t in trials if keyword in t["title"].lower()])
    return relevant_trials[:30]

def _calculate_confidence(trials: List[Dict[str, Any]]) -> float:
    if not trials:
        return 0.0
    phase_scores = {1: 0.5, 2: 0.7, 3: 0.9, 4: 1.0}
    avg_phase = sum(phase_scores.get(t["phase"], 0.5) for t in trials) / len(trials)
    count_score = min(len(trials) / 30, 1.0)
    return round(avg_phase * count_score, 2)

def _generate_references(trials: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    return [{"nct_id": t["nct_id"], "title": t["title"]} for t in trials]

# --- Agent Class ---
class ClinicalAgent:
    @staticmethod
    def process(query: str) -> Dict[str, Any]:
        trials = _get_relevant_trials(query)
        confidence = _calculate_confidence(trials)
        references = _generate_references(trials)
        # Simulate LLM analysis
        summary = f"Found {len(trials)} relevant clinical trials for query: '{query}'. "
        if trials:
            summary += f"Most are in phase {max(t['phase'] for t in trials)}. "
            summary += f"Top sponsors: {', '.join(set(t['sponsor'] for t in trials))}."
        else:
            summary += "No relevant trials found."
        return {
            "summary": summary,
            "confidence": confidence,
            "trials": trials,
            "references": references,
        }
