#!/usr/bin/env python3
"""
Test script: Gemini-based ROS scoring with brutally honest evaluation

This demonstrates the new calculate_ros_with_gemini() method that:
1. Takes the query directly
2. Passes evidence to Gemini
3. Gets a brutally honest research opportunity assessment
4. Extracts and returns the ROS score

Usage:
    python test_gemini_ros.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

from ros.scorer import calculate_ros_with_gemini, calculate_ros

# Sample test data
SAMPLE_QUERIES = [
    "GLP-1 for type 2 diabetes",
    "CRISPR for sickle cell disease",
    "Metformin for cancer prevention",
]

SAMPLE_REFERENCES = [
    {
        "title": "Phase 3 Trial of Drug X for Indication Y",
        "type": "clinical_trial",
        "phase": "Phase 3",
        "status": "Recruiting",
        "relevance": 0.9,
        "date": "2025-06-01",
        "agentId": "clinical"
    },
    {
        "title": "Market Analysis Report",
        "type": "market",
        "relevance": 0.7,
        "date": "2024-12-15",
        "agentId": "market"
    },
    {
        "title": "Published Research Paper",
        "type": "literature",
        "relevance": 0.8,
        "date": "2024-09-20",
        "agentId": "literature"
    },
    {
        "title": "Patent Application",
        "type": "patent",
        "relevance": 0.6,
        "date": "2024-01-10",
        "agentId": "market"
    },
]

SAMPLE_INSIGHTS = [
    {"text": "Strong evidence of efficacy in Phase 3 trials"},
    {"text": "Limited data on long-term safety profiles"},
    {"text": "Growing market demand for this indication"},
]


def test_deterministic_ros():
    """Test the original deterministic ROS calculation"""
    print("\n" + "="*70)
    print("DETERMINISTIC ROS (Original Method)")
    print("="*70)
    
    for query in SAMPLE_QUERIES:
        print(f"\nQuery: {query}")
        result = calculate_ros(query, SAMPLE_REFERENCES, SAMPLE_INSIGHTS)
        
        print(f"  ROS Score: {result['ros_score']:.2f}")
        print(f"  Confidence: {result['confidence_level']}")
        print(f"  Explanation: {result['explanation'][:150]}...")
        print(f"  Method: {result.get('calculation_method', 'deterministic')}")


def test_gemini_ros():
    """Test the new Gemini-based ROS calculation"""
    print("\n" + "="*70)
    print("GEMINI-BASED ROS (Brutally Honest Method)")
    print("="*70)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not set. Please set your API key:")
        print("   export GOOGLE_API_KEY='your-api-key'")
        return
    
    for query in SAMPLE_QUERIES:
        print(f"\nQuery: {query}")
        print("-" * 70)
        
        result = calculate_ros_with_gemini(query, SAMPLE_REFERENCES, SAMPLE_INSIGHTS)
        
        print(f"Method: {result.get('calculation_method', 'unknown')}")
        print(f"ROS Score: {result['ros_score']:.2f}")
        print(f"Confidence: {result['confidence_level']}")
        print(f"\nGemini's Brutal Assessment:")
        print("-" * 70)
        print(result.get('gemini_assessment', 'N/A'))
        print("-" * 70)


def compare_methods():
    """Compare deterministic vs Gemini-based scoring"""
    print("\n" + "="*70)
    print("COMPARISON: Deterministic vs Gemini-based ROS")
    print("="*70)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not set")
        return
    
    for query in SAMPLE_QUERIES[:1]:  # Just test one to save API calls
        print(f"\nQuery: {query}")
        
        # Deterministic
        det_result = calculate_ros(query, SAMPLE_REFERENCES, SAMPLE_INSIGHTS)
        det_score = det_result['ros_score']
        
        # Gemini
        gem_result = calculate_ros_with_gemini(query, SAMPLE_REFERENCES, SAMPLE_INSIGHTS)
        gem_score = gem_result['ros_score']
        
        print(f"\n  Deterministic ROS: {det_score:.2f} ({det_result['confidence_level']})")
        print(f"  Gemini ROS:        {gem_score:.2f} ({gem_result['confidence_level']})")
        print(f"  Difference:        {abs(gem_score - det_score):+.2f}")
        
        print(f"\n  Gemini's Reasoning (excerpt):")
        assessment = gem_result.get('gemini_assessment', '')
        lines = assessment.split('\n')
        for line in lines[:5]:
            if line.strip():
                print(f"    {line[:80]}")


if __name__ == "__main__":
    print("\n🔍 Testing ROS Scoring Methods\n")
    
    # Test deterministic
    test_deterministic_ros()
    
    # Test Gemini-based
    test_gemini_ros()
    
    # Compare
    compare_methods()
    
    print("\n✅ Tests complete!")
