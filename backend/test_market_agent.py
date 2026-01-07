"""
Detailed test of Market Agent Hybrid
Shows full JSON output and validates functionality
"""

import json
import logging
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_market_agent_detailed():
    """Detailed test with full JSON output"""

    print("\n" + "="*70)
    print("MARKET AGENT HYBRID - DETAILED TEST")
    print("="*70 + "\n")

    # Check environment
    groq_key = os.getenv("GROQ_API_KEY", "")
    google_key = os.getenv("GOOGLE_API_KEY", "")

    print("📋 Environment Check:")
    print(f"   GROQ_API_KEY: {'✅ Set' if groq_key else '❌ Not set'}")
    print(f"   GOOGLE_API_KEY: {'✅ Set' if google_key else '❌ Not set'}")
    print()

    # Import agent
    try:
        from agents.market_agent_hybrid import MarketAgentHybrid
        print("✅ Successfully imported MarketAgentHybrid\n")
    except Exception as e:
        print(f"❌ Failed to import: {e}\n")
        return False

    # Initialize agent
    print("📦 Initializing Market Agent...")
    try:
        agent = MarketAgentHybrid(
            use_rag=True,
            use_web_search=True,
            initialize_corpus=True,
            search_provider="duckduckgo"
        )
        print(f"✅ Agent initialized")
        print(f"   - RAG enabled: {agent.use_rag}")
        print(f"   - Web search enabled: {agent.use_web_search}")
        print()
    except Exception as e:
        print(f"❌ Initialization failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

    # Test query
    test_query = "What is the GLP-1 agonist market size and forecast?"

    print("="*70)
    print(f"TEST QUERY: {test_query}")
    print("="*70 + "\n")

    try:
        result = agent.process(test_query, top_k_rag=3, top_k_web=3)

        print("✅ Query processed successfully!\n")

        # Display results
        print("📊 RESULT OVERVIEW:")
        print("="*70)
        print(f"Agent ID: {result['agentId']}")
        print(f"Query: {result['query']}")

        # Display new confidence structure
        confidence = result.get('confidence', {})
        print(f"\nConfidence Score: {confidence.get('score', result.get('confidence_score', 0)):.2%}")
        print(f"Confidence Level: {confidence.get('level', 'N/A').upper()}")
        if 'explanation' in confidence:
            print(f"Explanation: {confidence['explanation']}")

        # Display confidence breakdown
        if 'breakdown' in confidence and confidence['breakdown']:
            print(f"\nConfidence Breakdown:")
            for component, score in confidence['breakdown'].items():
                print(f"  - {component.replace('_', ' ').title()}: {score:.3f}")
        print()

        print("🔍 RETRIEVAL USED:")
        print(f"   - Web Search: {result['retrieval_used']['web_search']}")
        print(f"   - RAG: {result['retrieval_used']['rag']}")
        print()

        if result['search_keywords']:
            print("🔑 SEARCH KEYWORDS:")
            for keyword in result['search_keywords']:
                print(f"   - {keyword}")
            print()

        print("🌐 WEB RESULTS:")
        print(f"   Found: {len(result['web_results'])} sources")
        for i, web_result in enumerate(result['web_results'][:3], 1):
            print(f"\n   [{i}] {web_result['title']}")
            print(f"       URL: {web_result['url']}")
            print(f"       Date: {web_result.get('date', 'N/A')}")
            print(f"       Snippet: {web_result['snippet'][:100]}...")
        print()

        print("📚 RAG RESULTS:")
        print(f"   Found: {len(result['rag_results'])} documents")
        for i, rag_result in enumerate(result['rag_results'][:3], 1):
            print(f"\n   [{i}] {rag_result['title']}")
            print(f"       Source: {rag_result['source']}")
            print(f"       Snippet: {rag_result['snippet'][:100]}...")
        print()

        print("📝 GENERATED SECTIONS:")
        print("="*70)
        for section_name, section_content in result['sections'].items():
            print(f"\n{section_name.upper().replace('_', ' ')}:")
            if isinstance(section_content, dict):
                print(json.dumps(section_content, indent=2)[:300] + "...")
            else:
                print(str(section_content)[:300] + "...")
            print()

        print("🔗 SOURCES:")
        print(f"   - Web sources: {len(result['sources']['web'])}")
        print(f"   - Internal sources: {len(result['sources']['internal'])}")
        print()

        # Show full JSON
        print("="*70)
        print("FULL JSON OUTPUT:")
        print("="*70)
        print(json.dumps(result, indent=2))
        print()

        # Validation
        print("="*70)
        print("VALIDATION:")
        print("="*70)

        checks = [
            ("Agent ID is 'market'", result['agentId'] == 'market'),
            ("Query matches input", result['query'] == test_query),
            ("Confidence score is valid", 0 <= result['confidence_score'] <= 1),
            ("Has retrieval_used field", 'retrieval_used' in result),
            ("Has sections field", 'sections' in result),
            ("Has sources field", 'sources' in result),
            ("Summary section exists", 'summary' in result['sections']),
            ("Market overview exists", 'market_overview' in result['sections']),
        ]

        all_passed = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"{status} {check_name}")
            if not check_result:
                all_passed = False

        print()
        if all_passed:
            print("🎉 ALL VALIDATION CHECKS PASSED!")
        else:
            print("⚠️  SOME VALIDATION CHECKS FAILED")

        return all_passed

    except Exception as e:
        print(f"❌ Query processing failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_market_agent_detailed()
    print("\n" + "="*70)
    if success:
        print("✅ MARKET AGENT HYBRID: FULLY FUNCTIONAL")
    else:
        print("❌ MARKET AGENT HYBRID: ISSUES DETECTED")
    print("="*70 + "\n")

    sys.exit(0 if success else 1)
