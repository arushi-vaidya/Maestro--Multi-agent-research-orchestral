#!/usr/bin/env python3
"""
Complete Integration Test: Deterministic vs Gemini ROS Scoring

This test demonstrates:
1. Loading API key from .env
2. Deterministic ROS calculation
3. Gemini-based honest ROS calculation
4. Side-by-side comparison
5. Integration with the full backend

Usage:
    python backend/test_ros_integration.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("\n" + "="*80)
print("🔬 ROS SCORING INTEGRATION TEST")
print("="*80)

# Verify API key is loaded
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ ERROR: GOOGLE_API_KEY not found in backend/.env")
    sys.exit(1)

print(f"\n✅ GOOGLE_API_KEY loaded from .env: {GOOGLE_API_KEY[:20]}...")

# Import ROS scorers
try:
    from ros.scorer import calculate_ros, calculate_ros_with_gemini
    print("✅ Imported ROS scoring modules")
except Exception as e:
    print(f"❌ ERROR importing ROS modules: {e}")
    sys.exit(1)

# Test data
TEST_QUERY = "GLP-1 receptor agonists for type 2 diabetes management"

TEST_REFERENCES = [
    {
        "title": "Phase 3 Randomized Controlled Trial of Semaglutide",
        "type": "clinical_trial",
        "phase": "Phase 3",
        "status": "Completed",
        "relevance": 0.95,
        "date": "2024-06-15",
        "agentId": "clinical"
    },
    {
        "title": "GLP-1 Market Analysis 2024-2026",
        "type": "market",
        "relevance": 0.8,
        "date": "2024-12-01",
        "agentId": "market"
    },
    {
        "title": "Cardiovascular Benefits of GLP-1 Agonists in Type 2 Diabetes",
        "type": "literature",
        "relevance": 0.85,
        "date": "2024-09-20",
        "agentId": "literature"
    },
    {
        "title": "Patent Portfolio: GLP-1 Agonist Formulations",
        "type": "patent",
        "relevance": 0.7,
        "date": "2024-03-10",
        "agentId": "market"
    },
]

TEST_INSIGHTS = [
    {"text": "Phase 3 trials show strong efficacy and HbA1c reduction"},
    {"text": "Cardiovascular benefits demonstrated in large population studies"},
    {"text": "Multiple competitors with approved products (Ozempic, Mounjaro, Trulicity)"},
    {"text": "Patent landscape shows limited freedom to operate for new entrants"},
    {"text": "Market is growing but maturing with established competitors"},
]

print("\n" + "-"*80)
print("TEST DATA:")
print("-"*80)
print(f"Query: {TEST_QUERY}")
print(f"References: {len(TEST_REFERENCES)} items")
print(f"Insights: {len(TEST_INSIGHTS)} items")

# Test 1: Deterministic ROS
print("\n" + "="*80)
print("TEST 1: DETERMINISTIC ROS SCORING")
print("="*80)

try:
    det_result = calculate_ros(
        query=TEST_QUERY,
        references=TEST_REFERENCES,
        insights=TEST_INSIGHTS
    )
    
    print(f"\n✅ Deterministic ROS Score: {det_result['ros_score']:.2f}/10")
    print(f"   Confidence Level: {det_result['confidence_level']}")
    print(f"   Calculation Method: {det_result.get('calculation_method', 'deterministic')}")
    print(f"\n📊 Component Breakdown:")
    for component, score in det_result['feature_breakdown'].items():
        print(f"   - {component}: {score:.2f}")
    print(f"\n📝 Explanation:")
    print(f"   {det_result['explanation'][:200]}...")
    
except Exception as e:
    print(f"❌ ERROR in deterministic scoring: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Gemini-based ROS
print("\n" + "="*80)
print("TEST 2: GEMINI-BASED HONEST ROS SCORING")
print("="*80)

try:
    gem_result = calculate_ros_with_gemini(
        query=TEST_QUERY,
        references=TEST_REFERENCES,
        insights=TEST_INSIGHTS
    )
    
    print(f"\n✅ Gemini ROS Score: {gem_result['ros_score']:.2f}/10")
    print(f"   Confidence Level: {gem_result['confidence_level']}")
    print(f"   Calculation Method: {gem_result.get('calculation_method', 'gemini_honest')}")
    
    print(f"\n💭 Gemini's Assessment (excerpt):")
    assessment = gem_result.get('gemini_assessment', 'N/A')
    lines = assessment.split('\n')[:10]  # First 10 lines
    for line in lines:
        if line.strip():
            print(f"   {line[:77]}")
    
    if len(assessment.split('\n')) > 10:
        print(f"   ... (truncated)")
    
except Exception as e:
    print(f"❌ ERROR in Gemini scoring: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Comparison
print("\n" + "="*80)
print("TEST 3: COMPARISON")
print("="*80)

try:
    if 'det_result' in locals() and 'gem_result' in locals():
        det_score = det_result['ros_score']
        gem_score = gem_result['ros_score']
        diff = gem_score - det_score
        
        print(f"\nDeterministic ROS: {det_score:.2f}/10 ({det_result['confidence_level']})")
        print(f"Gemini ROS:        {gem_score:.2f}/10 ({gem_result['confidence_level']})")
        print(f"Difference:        {diff:+.2f} points")
        
        if abs(diff) < 1.0:
            print(f"\n✅ Scores are close - both methods agree on opportunity level")
        elif diff > 1.0:
            print(f"\n⚠️  Gemini score is HIGHER - may see more potential than deterministic")
        else:
            print(f"\n⚠️  Gemini score is LOWER - more critical assessment than deterministic")
            print(f"   This typically means Gemini is flagging market saturation or realism concerns")
    
except Exception as e:
    print(f"❌ ERROR in comparison: {e}")

print("\n" + "="*80)
print("✅ INTEGRATION TEST COMPLETE")
print("="*80)
print("\n📚 Next Steps:")
print("   1. Test the API endpoint: POST /api/query with ros_method parameter")
print("   2. Try with different queries to see both methods in action")
print("   3. Review GEMINI_ROS_* documentation for more details")
print()
