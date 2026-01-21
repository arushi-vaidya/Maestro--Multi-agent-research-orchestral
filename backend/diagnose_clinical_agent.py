#!/usr/bin/env python3
"""
Diagnostic to check if Clinical Agent API calls are working
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.clinical_agent import ClinicalAgent
import logging

logging.basicConfig(level=logging.DEBUG)

def test_clinical_agent():
    """Test clinical agent with various queries"""
    agent = ClinicalAgent()
    
    queries = [
        "Metformin for Type 2 Diabetes",
        "CAR-T cell therapy for leukemia",
        "CRISPR for sickle cell disease",
        "Angiosarcoma treatment",
    ]
    
    for query in queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print('='*80)
        
        try:
            result = agent.process(query)
            
            print(f"Trials found: {len(result.get('trials', []))}")
            print(f"Has comprehensive_summary: {'comprehensive_summary' in result}")
            
            summary = result.get('comprehensive_summary', result.get('summary', 'NO SUMMARY'))
            
            if 'Unable to generate detailed summary' in summary:
                print("ERROR: AI generation failed! Using fallback.")
            elif not summary or len(summary) < 50:
                print("WARNING: Summary is very short or empty")
            else:
                print(f"Summary length: {len(summary)} chars")
                print(f"First 200 chars:\n{summary[:200]}")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("Testing Clinical Agent...")
    test_clinical_agent()
