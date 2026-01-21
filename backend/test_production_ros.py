#!/usr/bin/env python3
"""
Test script to diagnose why ROS scores are stuck in 6s for production queries.
Tests the actual master_agent and scorer with realistic queries.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.master_agent import MasterAgent
from ros.scorer import ROSScorer
from ros import ros_config
import json
from datetime import datetime, timedelta

def analyze_ros_components(query: str, references: list):
    """Analyze individual ROS components"""
    scorer = ROSScorer()
    
    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print(f"{'='*80}")
    print(f"Total References: {len(references)}")
    
    # Count by type
    clinical_trials = [r for r in references if r.get('type') in ['clinical_trial', 'clinical-trial']]
    patents = [r for r in references if r.get('type') == 'patent']
    literature = [r for r in references if r.get('type') == 'literature']
    market_reports = [r for r in references if r.get('type') == 'market-report']
    
    print(f"Clinical Trials: {len(clinical_trials)}")
    print(f"Patents: {len(patents)}")
    print(f"Literature: {len(literature)}")
    print(f"Market Reports: {len(market_reports)}")
    
    # Analyze dates for recency
    today = datetime.now()
    recent_trials = [r for r in clinical_trials if 'date' in r]
    if recent_trials:
        dates = []
        for r in recent_trials:
            try:
                date_obj = datetime.fromisoformat(r['date'].split('T')[0])
                days_old = (today - date_obj).days
                dates.append(days_old)
            except:
                pass
        if dates:
            print(f"Trial Dates - Min age: {min(dates)} days, Max age: {max(dates)} days, Avg: {sum(dates)/len(dates):.0f} days")
            recent_ratio = sum(1 for d in dates if d < 730) / len(dates) * 100
            print(f"Trials <2 years old: {recent_ratio:.1f}%")
    
    # Calculate ROS
    ros_score = scorer.calculate_ros(references)
    
    # Get component breakdown
    print(f"\n--- ROS Component Breakdown ---")
    print(f"Evidence Strength: {scorer._calculate_evidence_strength(references):.2f}")
    print(f"Evidence Diversity: {scorer._calculate_evidence_diversity(references):.2f}")
    print(f"Recency Boost: {scorer._calculate_recency_boost(references):.2f}")
    print(f"Novelty Score: {scorer._calculate_novelty_factor(references):.2f}")
    print(f"Conflict Penalty: {scorer._calculate_conflict_penalty(references):.2f}")
    print(f"Patent Risk: {scorer._calculate_patent_risk(references):.2f}")
    
    print(f"\n*** FINAL ROS SCORE: {ros_score:.2f}/10 ***\n")
    
    return ros_score, {
        'clinical_trials': len(clinical_trials),
        'patents': len(patents),
        'literature': len(literature),
        'market_reports': len(market_reports),
        'ros_score': ros_score
    }

def test_query(query: str):
    """Test a single query through the master agent"""
    try:
        master = MasterAgent()
        print(f"\nFetching evidence for: '{query}'")
        result = master.process_query(query)
        
        if not result or 'references' not in result:
            print("ERROR: No references returned!")
            return None
        
        references = result.get('references', [])
        return analyze_ros_components(query, references)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    queries = [
        # Novel/Rare
        "Angiosarcoma treatment trial",
        # Established/Saturated
        "Metformin for Type 2 Diabetes",
        # Emerging
        "CAR-T cell therapy for leukemia",
        # Novel intervention on old disease
        "CRISPR gene therapy for sickle cell",
        # Common
        "Aspirin for stroke prevention",
    ]
    
    print("\n" + "="*80)
    print("PRODUCTION ROS SCORE DIAGNOSTIC")
    print("="*80)
    print(f"Testing {len(queries)} realistic queries")
    print(f"ROS Configuration Weights: {ros_config.WEIGHTS}")
    print("="*80)
    
    results = []
    for query in queries:
        result = test_query(query)
        if result:
            results.append(result)
    
    if results:
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        scores = [r[0] for r in results]
        print(f"Score Range: {min(scores):.2f} - {max(scores):.2f}")
        print(f"Score Spread: {max(scores) - min(scores):.2f}")
        
        if max(scores) - min(scores) > 2.0:
            print("[SUCCESS] Scores differentiate well!")
        else:
            print("[WARNING] Scores not differentiating enough - need further investigation")
        
        print("\nDetailed Results:")
        for i, (query, (score, details)) in enumerate(zip(queries, results)):
            print(f"{i+1}. {query}")
            print(f"   Trials: {details['clinical_trials']}, Score: {score:.2f}")
