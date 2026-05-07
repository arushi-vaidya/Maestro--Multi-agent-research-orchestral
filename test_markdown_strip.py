#!/usr/bin/env python3
"""
Test Gemini ROS - Verify markdown stripping and metadata counts
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
import google.generativeai as genai

# Load .env
env_file = Path(__file__).parent / "backend" / ".env"
if env_file.exists():
    load_dotenv(env_file)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY not found")
    sys.exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

# Test markdown stripping
test_response = """Here's an evaluation:

1. **Does this drug-disease combination make pharmacological sense?** No, not as a disease-modifying treatment. **Paracetamol** is an analgesic and *antipyretic*.

2. **What is the mechanism of action and does it address the disease?**
   - Paracetamol's MOA: Inhibition of prostaglandin synthesis
   - Does it address the disease? **No**, it only treats symptoms

3. **Your HONEST research opportunity score (0-10).**
   **0/10** - This is a fundamental mismatch."""

def strip_markdown(text: str) -> str:
    """Strip markdown formatting from text"""
    import re
    # Remove bold/italic markers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **text** -> text
    text = re.sub(r'\*(.+?)\*', r'\1', text)      # *text* -> text
    text = re.sub(r'__(.+?)__', r'\1', text)       # __text__ -> text
    text = re.sub(r'_(.+?)_', r'\1', text)         # _text_ -> text
    # Remove heading markers
    text = re.sub(r'^#+\s', '', text, flags=re.MULTILINE)  # # Heading -> Heading
    # Remove numbered/bullet lists markers
    text = re.sub(r'^\d+\.\s', '', text, flags=re.MULTILINE)  # 1. text -> text
    text = re.sub(r'^[-*]\s', '', text, flags=re.MULTILINE)   # - text -> text
    return text.strip()

print("\n" + "="*80)
print("TESTING MARKDOWN STRIPPING")
print("="*80)

print("\n❌ WITH MARKDOWN:")
print(test_response)

print("\n✅ STRIPPED:")
clean = strip_markdown(test_response)
print(clean)

print("\n" + "="*80)
print("TESTING METADATA COUNTS")
print("="*80)

# Mock references to test counts
mock_references = [
    {"type": "clinical_trial", "relevance": 0.95, "agentId": "clinical"},
    {"type": "clinical_trial", "relevance": 0.85, "agentId": "clinical"},
    {"type": "patent", "relevance": 0.25, "agentId": "patent"},
    {"type": "literature", "relevance": 0.75, "agentId": "literature"},
]

supporting_count = len([r for r in mock_references if r.get('relevance', 0) > 0.6])
contradicting_count = len([r for r in mock_references if r.get('relevance', 0) < 0.3])

agents = set()
for ref in mock_references:
    if 'agentId' in ref:
        agents.add(ref['agentId'])

print(f"\nReferences: {len(mock_references)}")
print(f"Supporting (relevance > 0.6): {supporting_count}")
print(f"Contradicting (relevance < 0.3): {contradicting_count}")
print(f"Agents: {len(agents)} -> {list(agents)}")

print("\n" + "="*80)
print("✅ TEST COMPLETE")
print("="*80 + "\n")
