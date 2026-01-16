"""
Test script for Patent Agent
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.patent_agent import PatentAgent
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_patent_agent():
    """Test Patent Agent with sample queries"""

    print("="*80)
    print("TESTING PATENT AGENT")
    print("="*80)

    # Initialize agent
    print("\n1. Initializing Patent Agent...")
    agent = PatentAgent(use_web_search=False)
    print("✅ Patent Agent initialized successfully")

    # Test queries
    test_queries = [
        "GLP-1 receptor agonist patents",
        "Alzheimer's disease therapeutics",
        "CRISPR gene editing"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test Query {i}: {query}")
        print(f"{'='*80}")

        try:
            result = agent.process(query)

            print(f"\n📊 Results Summary:")
            print(f"   Summary: {result['summary']}")
            print(f"   Patents Found: {len(result.get('patents', []))}")
            print(f"   FTO Risk: {result.get('fto_assessment', {}).get('risk_level', 'Unknown')}")
            print(f"   Litigation Risk: {result.get('litigation_risk', 'Unknown')}")
            print(f"   White Space Opportunities: {len(result.get('white_space', []))}")
            print(f"   Confidence Score: {result.get('confidence_score', 0.0):.2f}")

            if result.get('landscape'):
                landscape = result['landscape']
                print(f"\n📈 Landscape:")
                print(f"   Total Patents: {landscape.get('total_patents', 0)}")
                print(f"   Active Patents: {landscape.get('active_patents', 0)}")
                print(f"   Key Players: {', '.join(p['organization'] for p in landscape.get('key_players', [])[:3])}")

            print("\n✅ Test passed!")

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

        if i < len(test_queries):
            print(f"\nWaiting before next query...")
            import time
            time.sleep(2)

    print("\n" + "="*80)
    print("PATENT AGENT TESTING COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_patent_agent()
