#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROS Validation Test - Verify 7-Step Fix
Tests the new ROS engine against 4 test queries to verify score differentiation
"""

import sys
import logging
import os
from datetime import datetime, timedelta
from ros.scorer import ROSScorer

# Fix encoding for Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configure logging to see [ROS] debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

# Test data: Mock references for each query
TEST_QUERIES = {
    "metformin_t2d": {
        "query": "Metformin for Type 2 Diabetes",
        "expected_ros": 2.1,
        "expected_level": "weak",
        "description": "Saturated: 200+ trials, Phase 3-4, FDA approved, huge patent landscape",
        "references": [
            # High-quality clinical trials (many)
            *[{
                "id": f"trial_{i}",
                "type": "clinical_trial",
                "title": f"Metformin Phase {3+min(i%2, 1)} Trial {i}",
                "relevance": 0.95,
                "phase": "Phase 4" if i % 3 == 0 else "Phase 3",
                "date": (datetime.now() - timedelta(days=200 + i*5)).isoformat(),
                "status": "completed",
                "agentId": "clinical_agent"
            } for i in range(200)],  # 200 clinical trials
            # Patent references
            *[{
                "id": f"patent_{i}",
                "type": "patent",
                "title": f"Metformin Formulation Patent {i}",
                "relevance": 0.7,
                "date": (datetime.now() - timedelta(days=500 + i*10)).isoformat(),
                "agentId": "patent_agent"
            } for i in range(150)],  # 150 patents
            # Literature references
            *[{
                "id": f"literature_{i}",
                "type": "literature",
                "title": f"Metformin T2D Review {i}",
                "relevance": 0.8,
                "date": (datetime.now() - timedelta(days=100 + i*3)).isoformat(),
                "agentId": "literature_agent"
            } for i in range(50)],  # 50 literature refs
        ],
        "insights": [
            {"text": "Extensive clinical evidence supports metformin efficacy", "type": "supporting"},
            {"text": "Long-term safety profile well-established", "type": "supporting"},
            {"text": "FDA approved for Type 2 Diabetes", "type": "supporting"},
        ]
    },
    
    "metformin_parkinsons": {
        "query": "Metformin for Parkinson's Disease",
        "expected_ros": 5.2,
        "expected_level": "moderate",
        "description": "Emerging: 15 trials, Phase 2-3, moderate evidence, some patents",
        "references": [
            # Fewer clinical trials (emerging area)
            *[{
                "id": f"trial_{i}",
                "type": "clinical_trial",
                "title": f"Metformin Parkinson's Phase {2+i%2} Trial {i}",
                "relevance": 0.85 + (0.1 if i % 2 == 0 else 0),
                "phase": "Phase 3" if i % 2 == 0 else "Phase 2",
                "date": (datetime.now() - timedelta(days=100 + i*10)).isoformat(),
                "status": "recruiting" if i % 4 == 0 else ("active" if i % 3 == 0 else "completed"),
                "agentId": "clinical_agent"
            } for i in range(15)],  # 15 trials
            # Patents
            *[{
                "id": f"patent_{i}",
                "type": "patent",
                "title": f"Neuroprotective Patent {i}",
                "relevance": 0.6,
                "date": (datetime.now() - timedelta(days=600 + i*20)).isoformat(),
                "agentId": "patent_agent"
            } for i in range(8)],  # 8 patents
            # Literature
            *[{
                "id": f"literature_{i}",
                "type": "literature",
                "title": f"Metformin Neuroprotection Study {i}",
                "relevance": 0.75,
                "date": (datetime.now() - timedelta(days=200 + i*10)).isoformat(),
                "agentId": "literature_agent"
            } for i in range(12)],  # 12 literature refs
        ],
        "insights": [
            {"text": "Emerging evidence for neuroprotective effects", "type": "supporting"},
            {"text": "Phase 2-3 trials currently recruiting", "type": "supporting"},
            {"text": "Mechanistic plausibility for PD protection", "type": "supporting"},
            {"text": "Limited long-term safety data", "type": "contradicting"},
        ]
    },
    
    "propranolol_angiosarcoma": {
        "query": "Propranolol for Angiosarcoma",
        "expected_ros": 5.8,
        "expected_level": "strong",
        "description": "Highly novel: <5 trials, Phase 1-2, mechanistically plausible, high patents",
        "references": [
            # Very few clinical trials (highly novel)
            *[{
                "id": f"trial_{i}",
                "type": "clinical_trial",
                "title": f"Propranolol Angiosarcoma Phase {1+i%2} Trial {i}",
                "relevance": 0.9,
                "phase": "Phase 2" if i % 2 == 0 else "Phase 1",
                "date": (datetime.now() - timedelta(days=50 + i*5)).isoformat(),
                "status": "recruiting" if i < 2 else "active",
                "agentId": "clinical_agent"
            } for i in range(4)],  # 4 trials
            # High patent density
            *[{
                "id": f"patent_{i}",
                "type": "patent",
                "title": f"Propranolol Vasculature Patent {i}",
                "relevance": 0.8,
                "date": (datetime.now() - timedelta(days=300 + i*5)).isoformat(),
                "agentId": "patent_agent"
            } for i in range(8)],  # 8 patents (high ratio)
            # Mechanism studies
            *[{
                "id": f"mechanism_{i}",
                "type": "mechanistic",
                "title": f"Beta-blocker Angiogenesis Study {i}",
                "relevance": 0.85,
                "date": (datetime.now() - timedelta(days=150 + i*3)).isoformat(),
                "agentId": "literature_agent"
            } for i in range(6)],  # 6 mechanism refs
        ],
        "insights": [
            {"text": "Mechanistic evidence for anti-angiogenic effect", "type": "supporting"},
            {"text": "Early Phase trials showing promise", "type": "supporting"},
            {"text": "Very limited clinical experience", "type": "contradicting"},
            {"text": "High patent saturation in beta-blocker space", "type": "contradicting"},
        ]
    },
    
    "disulfiram_glioblastoma": {
        "query": "Disulfiram for Glioblastoma",
        "expected_ros": 6.1,
        "expected_level": "strong",
        "description": "Moderately novel: 20 trials, Phase 2, good evidence, moderate patents",
        "references": [
            # Moderate number of trials
            *[{
                "id": f"trial_{i}",
                "type": "clinical_trial",
                "title": f"Disulfiram Glioblastoma Phase 2 Trial {i}",
                "relevance": 0.88,
                "phase": "Phase 2",
                "date": (datetime.now() - timedelta(days=80 + i*8)).isoformat(),
                "status": "recruiting" if i < 5 else ("active" if i < 10 else "completed"),
                "agentId": "clinical_agent"
            } for i in range(20)],  # 20 trials
            # Moderate patents
            *[{
                "id": f"patent_{i}",
                "type": "patent",
                "title": f"Copper Chelation Patent {i}",
                "relevance": 0.75,
                "date": (datetime.now() - timedelta(days=400 + i*10)).isoformat(),
                "agentId": "patent_agent"
            } for i in range(10)],  # 10 patents
            # Literature
            *[{
                "id": f"literature_{i}",
                "type": "literature",
                "title": f"Disulfiram Anti-cancer Study {i}",
                "relevance": 0.82,
                "date": (datetime.now() - timedelta(days=180 + i*8)).isoformat(),
                "agentId": "literature_agent"
            } for i in range(20)],  # 20 literature refs
        ],
        "insights": [
            {"text": "Emerging clinical evidence for glioblastoma activity", "type": "supporting"},
            {"text": "Phase 2 trials showing encouraging results", "type": "supporting"},
            {"text": "Multiple active trials for glioblastoma", "type": "supporting"},
            {"text": "Mechanism involves copper chelation and NF-κB inhibition", "type": "supporting"},
        ]
    }
}


def run_validation():
    """Run ROS validation on all test queries"""
    print("\n" + "="*80)
    print("ROS ENGINE VALIDATION - 7-STEP FIX VERIFICATION")
    print("="*80 + "\n")
    
    scorer = ROSScorer()
    results = []
    
    for query_key, test_data in TEST_QUERIES.items():
        print(f"\n{'-'*80}")
        print(f"TEST: {test_data['query']}")
        print(f"Profile: {test_data['description']}")
        print(f"{'-'*80}")
        
        # Run ROS calculation
        result = scorer.calculate_ros(
            query=test_data['query'],
            references=test_data['references'],
            insights=test_data['insights'],
            akgp_stats=None
        )
        
        ros_score = result['ros_score']
        confidence_level = result['confidence_level']
        breakdown = result['feature_breakdown']
        weighted = result['weighted_breakdown']
        explanation = result['explanation']
        
        # Display results
        print(f"\n[OK] ROS Score: {ros_score:.2f} / 10.0")
        print(f"  Confidence Level: {confidence_level.upper()}")
        print(f"  Expected Range: ~{test_data['expected_ros']:.1f}")
        
        print(f"\n[BREAKDOWN] Component Breakdown:")
        print(f"   Evidence Strength:    {breakdown['evidence_strength']:.2f} (w: {weighted['evidence_strength_weighted']:.2f})")
        print(f"   Evidence Diversity:   {breakdown['evidence_diversity']:.2f} (w: {weighted['evidence_diversity_weighted']:.2f})")
        print(f"   Recency Boost:        {breakdown['recency_boost']:.2f} (w: {weighted['recency_boost_weighted']:.2f})")
        print(f"   Novelty Score:        {breakdown['novelty_score']:.2f} (w: {weighted['novelty_score_weighted']:.2f})")
        print(f"   Conflict Penalty:     {breakdown['conflict_penalty']:.2f} (w: {weighted['conflict_penalty_weighted']:.2f})")
        print(f"   Patent Risk:          {breakdown['patent_risk_penalty']:.2f} (w: {weighted['patent_risk_weighted']:.2f})")
        
        print(f"\n[REASON] Explanation: {explanation}")
        
        # Verify differentiation
        expected = test_data['expected_ros']
        diff = abs(ros_score - expected)
        status = "[PASS]" if diff < 1.0 else "[CLOSE]" if diff < 2.0 else "[FAIL]"
        print(f"\n{status}: Difference from expected: {diff:.2f} points")
        
        results.append({
            'query': test_data['query'],
            'ros_score': ros_score,
            'expected': expected,
            'difference': diff,
            'level': confidence_level,
            'status': status
        })
    
    # Summary table
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"\n{'Query':<40} {'ROS':<8} {'Expected':<10} {'Diff':<8} {'Status':<15}")
    print("─"*80)
    
    for r in results:
        status_str = "[PASS]" if r['status'].startswith("[PASS]") else "[CLOSE]" if r['status'].startswith("[CLOSE]") else "[FAIL]"
        print(f"{r['query']:<40} {r['ros_score']:>6.2f}  {r['expected']:>8.1f}  {r['difference']:>6.2f}  {status_str:<10}")
    
    # Key validation checks
    print("\n" + "="*80)
    print("KEY VALIDATION CHECKS")
    print("="*80)
    
    scores = [r['ros_score'] for r in results]
    
    # Check 1: Differentiation (not converging)
    score_range = max(scores) - min(scores)
    check1 = "[PASS]" if score_range > 2.0 else "[FAIL]"
    print(f"\n1. Score Differentiation: {check1}")
    print(f"   Range: {min(scores):.2f} - {max(scores):.2f} (spread: {score_range:.2f})")
    print(f"   Expected: Spread > 2.0 (was collapsing to 0.5 before fix)")
    
    # Check 2: Saturation penalty (T2D should be lowest)
    t2d_score = results[0]['ros_score']
    all_others = [results[i]['ros_score'] for i in range(1, 4)]
    check2 = "[PASS]" if t2d_score < min(all_others) else "[FAIL]"
    print(f"\n2. Saturation Penalty (T2D should be lowest): {check2}")
    print(f"   T2D: {t2d_score:.2f}, Others: {[f'{s:.2f}' for s in all_others]}")
    print(f"   Expected: T2D is the lowest (saturated area)")
    
    # Check 3: Novelty bonus (Angiosarcoma should be highest or equal to Glioblastoma)
    angiosarcoma_score = results[2]['ros_score']
    glioblastoma_score = results[3]['ros_score']
    check3 = "[PASS]" if angiosarcoma_score >= glioblastoma_score - 0.5 else "[FAIL]"
    print(f"\n3. Novelty Bonus (novel areas score high): {check3}")
    print(f"   Angiosarcoma: {angiosarcoma_score:.2f}, Glioblastoma: {glioblastoma_score:.2f}")
    print(f"   Expected: Novel indications score as high-opportunity (not penalized for fewer trials)")
    
    # Check 4: No convergence to 4-4.5
    avg_score = sum(scores) / len(scores)
    convergence_issue = all(3.5 <= s <= 4.5 for s in scores)
    check4 = "[FAIL - Still converging!]" if convergence_issue else "[PASS]"
    print(f"\n4. No Convergence to 4-4.5: {check4}")
    print(f"   Average: {avg_score:.2f}, Range: {score_range:.2f}")
    print(f"   Expected: Scores spread across 2-9 range")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    try:
        run_validation()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
