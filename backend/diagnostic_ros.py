#!/usr/bin/env python3
"""
Diagnostic tool to analyze ROS component breakdown for actual queries
"""

import logging
from datetime import datetime, timedelta
from ros.scorer import ROSScorer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_realistic_references(trial_count: int, indication_name: str, recency_ratio: float = 0.3):
    """
    Create realistic references with varied recency
    recency_ratio: fraction of trials that are recent (< 1 year old)
    """
    refs = []
    now = datetime.utcnow()
    
    # Determine phases based on trial count (established indications have more Phase 3-4)
    if trial_count < 10:
        phases = ["Phase 1", "Phase 2"]
    elif trial_count < 30:
        phases = ["Phase 2", "Phase 3"]
    elif trial_count < 100:
        phases = ["Phase 3", "Phase 4"]
    else:
        phases = ["Phase 4"]
    
    # Create references with varied dates
    for i in range(trial_count):
        # Some trials are recent, some old
        if i < int(trial_count * recency_ratio):
            # Recent trial (within last 365 days)
            days_old = int(365 * (i / int(trial_count * recency_ratio)))
        else:
            # Older trial (1-5 years old)
            days_old = 365 + int(1825 * ((i - int(trial_count * recency_ratio)) / (trial_count - int(trial_count * recency_ratio))))
        
        trial_date = (now - timedelta(days=days_old)).isoformat()
        
        # Determine status based on date and trial phase
        if days_old < 365:
            status = "recruiting"
        elif days_old < 1095:  # < 3 years
            status = "active"
        else:
            status = "completed"
        
        refs.append({
            "type": "clinical_trial",
            "title": f"Trial {i+1}: {indication_name}",
            "source": f"ClinicalTrials.gov NCT{str(i+1).zfill(8)}",
            "date": trial_date,
            "url": f"https://clinicaltrials.gov/study/NCT{str(i+1).zfill(8)}",
            "relevance": 80 + (i % 20),
            "agentId": "clinical",
            "status": status,
            "phase": phases[i % len(phases)],
            "nct_id": f"NCT{str(i+1).zfill(8)}",
            "summary": f"Mock {indication_name} trial"
        })
    
    return refs

def analyze_query_scenario(query_name: str, trial_count: int, recency_ratio: float = 0.1):
    """Analyze ROS for a specific query scenario"""
    
    scorer = ROSScorer()
    refs = create_realistic_references(trial_count, query_name, recency_ratio)
    
    result = scorer.calculate_ros(
        query=query_name,
        references=refs,
        insights=[]
    )
    
    breakdown = result['feature_breakdown']
    
    print(f"\n{'='*80}")
    print(f"QUERY: {query_name}")
    print(f"{'='*80}")
    print(f"Trial Count: {trial_count}")
    print(f"Recency Ratio: {recency_ratio*100:.0f}% recent")
    print(f"\n[ROS SCORE]: {result['ros_score']:.2f}/10.0")
    print(f"Confidence: {result['confidence_level']}")
    print(f"\nComponent Breakdown:")
    print(f"  Evidence Strength:    {breakdown['evidence_strength']:.2f}")
    print(f"  Evidence Diversity:   {breakdown['evidence_diversity']:.2f}")
    print(f"  Recency Boost:        {breakdown['recency_boost']:.2f}")
    print(f"  Novelty Score:        {breakdown['novelty_score']:.2f}")
    print(f"  Conflict Penalty:     {breakdown['conflict_penalty']:.2f}")
    print(f"  Patent Risk:          {breakdown['patent_risk_penalty']:.2f}")
    
    weighted = result['weighted_breakdown']
    print(f"\nWeighted Contributions:")
    print(f"  Evidence Strength:    {weighted['evidence_strength_weighted']:.2f}")
    print(f"  Evidence Diversity:   {weighted['evidence_diversity_weighted']:.2f}")
    print(f"  Recency Boost:        {weighted['recency_boost_weighted']:.2f}")
    print(f"  Novelty Score:        {weighted['novelty_score_weighted']:.2f}")
    print(f"  Conflict Penalty:     {weighted['conflict_penalty_weighted']:.2f}")
    print(f"  Patent Risk:          {weighted['patent_risk_weighted']:.2f}")
    
    return result['ros_score']

if __name__ == "__main__":
    print("\n" + "="*80)
    print("ROS DIAGNOSTIC: REAL-WORLD QUERY SCENARIOS")
    print("="*80)
    
    # Simulate realistic scenarios
    scenarios = [
        ("Metformin for Type 2 Diabetes", 100, 0.05),      # Saturated, few recent
        ("Novel CAR-T for Leukemia", 25, 0.40),            # Emerging, many recent
        ("Experimental Drug for Rare Disease", 8, 0.75),   # Novel, very recent
        ("Aspirin for Pain Relief", 350, 0.02),            # Highly saturated, ancient
        ("Immunotherapy for Melanoma", 45, 0.30),          # Moderate, some recent
    ]
    
    scores = []
    for query, trial_count, recency in scenarios:
        score = analyze_query_scenario(query, trial_count, recency)
        scores.append((query, score))
    
    print(f"\n\n{'='*80}")
    print("SCORE SUMMARY")
    print(f"{'='*80}")
    print(f"{'Query':<40} {'Score':>10}")
    print(f"{'-'*80}")
    for query, score in sorted(scores, key=lambda x: x[1], reverse=True):
        print(f"{query:<40} {score:>10.2f}")
    
    print(f"\nScore Range: {min(s[1] for s in scores):.2f} - {max(s[1] for s in scores):.2f}")
    print(f"Score Spread: {max(s[1] for s in scores) - min(s[1] for s in scores):.2f}")
    
    if max(s[1] for s in scores) - min(s[1] for s in scores) > 1.5:
        print("\n[SUCCESS] Scores differentiate well!")
    else:
        print("\n[ISSUE] Scores not differentiating enough - adjust weights")
