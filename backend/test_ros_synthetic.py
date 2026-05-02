#!/usr/bin/env python3
"""
Test ROS scoring with synthetic references - avoids API calls
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ros.scorer import ROSScorer
from ros import ros_config
from datetime import datetime, timedelta

def create_test_references(trial_count: int, recent_ratio: float = 0.3) -> list:
    """Create synthetic references for testing"""
    today = datetime.now()
    references = []
    
    # Add clinical trials
    for i in range(trial_count):
        # Distribute dates: some recent, some old
        if i < trial_count * recent_ratio:
            date = (today - timedelta(days=30 * (i % 12 + 1))).isoformat()  # 1-12 months old
            status = "recruiting"
        else:
            date = (today - timedelta(days=365 * (2 + i % 3))).isoformat()  # 2-5 years old
            status = "completed"
        
        phase = ["Phase 1", "Phase 2", "Phase 3", "Phase 4"][i % 4]
        
        references.append({
            "type": "clinical_trial",
            "date": date,
            "status": status,
            "phase": phase,
            "relevance": 85 + (i % 15),
            "agentId": "clinical"
        })
    
    # Add 5 patents
    for i in range(5):
        references.append({
            "type": "patent",
            "date": (today - timedelta(days=365 * (1 + i))).isoformat(),
            "status": "issued",
            "phase": "Patent",
            "relevance": 70,
            "agentId": "patent"
        })
    
    # Add 3 literature papers
    for i in range(3):
        references.append({
            "type": "literature",
            "date": (today - timedelta(days=180 + 30*i)).isoformat(),
            "status": "published",
            "phase": "Review",
            "relevance": 75,
            "agentId": "literature"
        })
    
    return references

def test_scenario(name: str, trial_count: int, recent_ratio: float = 0.3):
    """Test a specific scenario"""
    references = create_test_references(trial_count, recent_ratio)
    scorer = ROSScorer()
    
    # Prepare insights (can be empty for testing)
    insights = []
    
    result = scorer.calculate_ros(
        query=name,
        references=references,
        insights=insights,
        akgp_stats={}
    )
    
    ros_score = result.get('ros_score', 0)
    breakdown = result.get('breakdown', {})
    
    print(f"\n{name}")
    print(f"  Trials: {trial_count}, Recent%: {recent_ratio*100:.0f}%")
    print(f"  Components:")
    print(f"    - Evidence Strength: {breakdown.get('evidence_strength', 0):.2f}")
    print(f"    - Evidence Diversity: {breakdown.get('evidence_diversity', 0):.2f}")
    print(f"    - Recency Boost: {breakdown.get('recency_boost', 0):.2f}")
    print(f"    - Novelty Score: {breakdown.get('novelty_score', 0):.2f}")
    print(f"    - Conflict Penalty: {breakdown.get('conflict_penalty', 0):.2f}")
    print(f"    - Patent Risk: {breakdown.get('patent_risk', 0):.2f}")
    print(f"  === ROS SCORE: {ros_score:.2f}/10 ===")
    
    return ros_score

if __name__ == "__main__":
    print("="*80)
    print("ROS SCORING TEST - Synthetic References (No API Calls)")
    print("="*80)
    print(f"Current Weights: {ros_config.WEIGHTS}")
    print("="*80)
    
    scenarios = [
        ("Rare/Novel Indication (8 trials, 75% recent)", 8, 0.75),
        ("Emerging Indication (25 trials, 40% recent)", 25, 0.40),
        ("Moderate Indication (45 trials, 30% recent)", 45, 0.30),
        ("Established Indication (100 trials, 5% recent)", 100, 0.05),
        ("Saturated Indication (350 trials, 2% recent)", 350, 0.02),
    ]
    
    scores = []
    for name, trials, recent in scenarios:
        score = test_scenario(name, trials, recent)
        scores.append(score)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Score Range: {min(scores):.2f} - {max(scores):.2f}")
    print(f"Score Spread: {max(scores) - min(scores):.2f}")
    
    if max(scores) - min(scores) > 2.5:
        print("[SUCCESS] Scores differentiate well!")
    elif max(scores) - min(scores) > 1.5:
        print("[WARNING] Moderate differentiation - could be better")
    else:
        print("[CRITICAL] Scores not differentiating enough!")
