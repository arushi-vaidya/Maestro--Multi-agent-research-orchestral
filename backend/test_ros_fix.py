#!/usr/bin/env python3
"""
Test script to verify ROS scoring fix
Tests that different queries produce different scores (not stuck at 6.6)
"""

import logging
from ros.scorer import ROSScorer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_mock_references(trial_count: int, phase: str, status: str, agent_id: str = "clinical"):
    """Create mock references for testing"""
    refs = []
    for i in range(trial_count):
        refs.append({
            "type": "clinical_trial",
            "title": f"Trial {i+1}: {phase} study",
            "source": f"ClinicalTrials.gov NCT{str(i+1).zfill(8)}",
            "date": "2023-01-01",
            "url": f"https://clinicaltrials.gov/study/NCT{str(i+1).zfill(8)}",
            "relevance": 85 + (i % 10),
            "agentId": agent_id,
            "status": status,
            "phase": phase,
            "nct_id": f"NCT{str(i+1).zfill(8)}",
            "summary": "Mock trial summary"
        })
    return refs

def test_ros_scoring():
    """Test ROS scoring with different trial scenarios"""
    
    scorer = ROSScorer()
    
    print("\n" + "="*80)
    print("ROS SCORING FIX VERIFICATION TEST")
    print("="*80)
    
    # Test 1: Highly novel indication (few trials, early phase)
    print("\n[TEST 1] HIGHLY NOVEL INDICATION (3 Phase 1 trials)")
    print("-" * 80)
    refs_novel = create_mock_references(trial_count=3, phase="Phase 1", status="recruiting")
    result_novel = scorer.calculate_ros(
        query="New Drug for Rare Disease",
        references=refs_novel,
        insights=[]
    )
    score_novel = result_novel['ros_score']
    print(f"ROS Score: {score_novel:.2f} / 10.0")
    print(f"Novelty Component: {result_novel['feature_breakdown']['novelty_score']:.2f}")
    print(f"Expected: HIGH (>7.5)")
    
    # Test 2: Saturated indication (many trials, late phase)
    print("\n[TEST 2] SATURATED INDICATION (120 Phase 4 trials)")
    print("-" * 80)
    refs_saturated = create_mock_references(trial_count=120, phase="Phase 4", status="completed")
    result_saturated = scorer.calculate_ros(
        query="Standard Treatment for Diabetes",
        references=refs_saturated,
        insights=[]
    )
    score_saturated = result_saturated['ros_score']
    print(f"ROS Score: {score_saturated:.2f} / 10.0")
    print(f"Novelty Component: {result_saturated['feature_breakdown']['novelty_score']:.2f}")
    print(f"Expected: LOW (<6.0)")
    
    # Test 3: Emerging indication (medium trials, mixed phase)
    print("\n[TEST 3] EMERGING INDICATION (15 Phase 2-3 trials)")
    print("-" * 80)
    refs_emerging = create_mock_references(trial_count=15, phase="Phase 2, Phase 3", status="active")
    result_emerging = scorer.calculate_ros(
        query="Novel Therapy for Cancer",
        references=refs_emerging,
        insights=[]
    )
    score_emerging = result_emerging['ros_score']
    print(f"ROS Score: {score_emerging:.2f} / 10.0")
    print(f"Novelty Component: {result_emerging['feature_breakdown']['novelty_score']:.2f}")
    print(f"Expected: MEDIUM (6.0-7.0)")
    
    # Test 4: Mixed references (clinical + market + patents)
    print("\n[TEST 4] MIXED REFERENCES (5 clinical + 3 market + 2 patents)")
    print("-" * 80)
    refs_mixed = (
        create_mock_references(trial_count=5, phase="Phase 2", status="recruiting", agent_id="clinical") +
        [
            {
                "type": "market-report",
                "title": "Market Report",
                "source": "Web",
                "date": "2024",
                "url": "https://example.com",
                "relevance": 80,
                "agentId": "market",
                "status": "published",
                "phase": "Market",
                "summary": "Market data"
            },
            {
                "type": "patent",
                "title": "Patent",
                "source": "USPTO",
                "date": "2023",
                "url": "https://patent.com",
                "relevance": 75,
                "agentId": "patent",
                "status": "issued",
                "phase": "Patent",
                "summary": "Patent data"
            }
        ]
    )
    result_mixed = scorer.calculate_ros(
        query="Drug for Multiple Indications",
        references=refs_mixed,
        insights=[]
    )
    score_mixed = result_mixed['ros_score']
    print(f"ROS Score: {score_mixed:.2f} / 10.0")
    print(f"Expected: MEDIUM-HIGH (7.0+ due to few clinical trials)")
    
    # VERIFICATION
    print("\n" + "="*80)
    print("VERIFICATION RESULTS")
    print("="*80)
    
    differences = [
        ("Novel vs Saturated", abs(score_novel - score_saturated)),
        ("Novel vs Emerging", abs(score_novel - score_emerging)),
        ("Saturated vs Emerging", abs(score_saturated - score_emerging)),
    ]
    
    all_pass = True
    for label, diff in differences:
        status = "PASS" if diff > 0.5 else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"{label:30s}: diff={diff:.2f} [{status}]")
    
    print(f"\nNovel score:     {score_novel:.2f}")
    print(f"Saturated score: {score_saturated:.2f}")
    print(f"Emerging score:  {score_emerging:.2f}")
    print(f"Mixed score:     {score_mixed:.2f}")
    
    if score_novel > score_saturated and score_emerging > score_saturated:
        print("\n[SUCCESS] Scores differentiate properly!")
        print("[SUCCESS] Novel and Emerging > Saturated")
        return True
    else:
        print("\n[FAILURE] Scores NOT differentiating!")
        print(f"[FAILURE] Expected: Novel/Emerging > Saturated, Got: {score_novel:.2f}/{score_emerging:.2f} vs {score_saturated:.2f}")
        return False

if __name__ == "__main__":
    success = test_ros_scoring()
    exit(0 if success else 1)
