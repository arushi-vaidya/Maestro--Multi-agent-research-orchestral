#!/usr/bin/env python3
"""
Quick diagnostic test for Clinical and Market agents
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s'
)

print("="*60)
print("AGENT DIAGNOSTIC TEST")
print("="*60)

# Test 1: Clinical Agent
print("\n1. Testing Clinical Agent...")
print("-"*60)

try:
    from agents.clinical_agent import ClinicalAgent

    clinical_agent = ClinicalAgent()
    print("✅ Clinical Agent initialized")

    query = "GLP-1 agonist"
    print(f"\n📊 Processing query: '{query}'")

    result = clinical_agent.process(query)

    print(f"\n📈 Results:")
    print(f"   - Trials found: {len(result.get('trials', []))}")
    print(f"   - Summary length: {len(result.get('comprehensive_summary', ''))}")
    print(f"   - Summary preview: {result.get('comprehensive_summary', '')[:200]}...")

    if len(result.get('trials', [])) == 0:
        print("\n❌ ISSUE: Clinical Agent returned 0 trials!")
        print(f"   Full result keys: {result.keys()}")

except Exception as e:
    print(f"\n❌ Clinical Agent FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Market Agent
print("\n\n2. Testing Market Agent...")
print("-"*60)

try:
    from agents.market_agent_hybrid import MarketAgentHybrid

    market_agent = MarketAgentHybrid(
        use_rag=True,
        use_web_search=True,
        initialize_corpus=False
    )
    print("✅ Market Agent initialized")

    query = "GLP-1 market size"
    print(f"\n📊 Processing query: '{query}'")

    result = market_agent.process(query, top_k_rag=5, top_k_web=10)

    print(f"\n📈 Results:")
    print(f"   - Web results: {len(result.get('web_results', []))}")
    print(f"   - RAG results: {len(result.get('rag_results', []))}")
    print(f"   - Sections: {list(result.get('sections', {}).keys())}")
    print(f"   - Summary: {result['sections'].get('summary', 'N/A')[:200]}...")
    print(f"   - Market Overview: {result['sections'].get('market_overview', 'N/A')[:200]}...")
    print(f"   - Confidence: {result['confidence']['score']:.2%} ({result['confidence']['level']})")

    if result['sections'].get('summary') == 'See summary':
        print("\n❌ ISSUE: Market Agent returned fallback sections (LLM synthesis failed)!")

except Exception as e:
    print(f"\n❌ Market Agent FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 3: LLM Configuration
print("\n\n3. Testing LLM Configuration...")
print("-"*60)

try:
    from config.llm.llm_config_sync import generate_llm_response

    test_prompt = "What is 2+2? Answer in one word."
    print(f"📊 Test prompt: '{test_prompt}'")

    response = generate_llm_response(test_prompt, temperature=0, max_tokens=50)
    print(f"✅ LLM Response: {response}")

except Exception as e:
    print(f"❌ LLM FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("DIAGNOSTIC TEST COMPLETE")
print("="*60)
