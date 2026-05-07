#!/usr/bin/env python3
"""
Test Gemini ROS using its own knowledge (no evidence data)
Tests cases that should get low scores based on scientific validity
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
    print(f"✅ Loaded .env from {env_file}")
else:
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded .env from {env_file}")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY not found")
    sys.exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

def test_query(query: str, drug: str, disease: str):
    """Test a single query using Gemini's own knowledge"""
    print(f"\n{'='*80}")
    print(f"TESTING: {query}")
    print(f"Drug: {drug}, Disease: {disease}")
    print(f"{'='*80}")
    
    system_prompt = """You are a brutally honest pharmaceutical research analyst with deep expertise in pharmacology, pathophysiology, and drug mechanisms.

Your job is to evaluate research opportunities using YOUR OWN KNOWLEDGE:
- Does the drug's mechanism of action actually address the disease?
- Is there ANY scientific basis for this combination?
- What does your knowledge tell you about efficacy potential?
- What is the current market saturation for this indication?
- Are there approved competitors already?

SCORING GUIDE (BE BRUTALLY HONEST):
- 9-10: Exceptional opportunity (rare). Novel, scientifically sound, clear unmet need.
- 7-8: Good opportunity. Mechanism makes sense, some market gap, feasible.
- 5-6: Moderate opportunity. Some scientific basis, but limited novelty or questionable mechanism.
- 3-4: Weak opportunity. Questionable mechanism OR saturated market.
- 0-2: Poor opportunity. NO scientific basis OR clearly wrong mechanism/indication combo.

CRITICAL: If the drug-disease combination doesn't make sense pharmacologically, give it a LOW score.
Don't be influenced by trial volume - score based on SCIENTIFIC MERIT first."""

    user_prompt = f"""Using YOUR KNOWLEDGE, evaluate this research opportunity:

DRUG: {drug}
DISEASE: {disease}
QUERY: {query}

Based on what you know about:
1. {drug}'s mechanism of action
2. {disease}'s pathophysiology
3. Existing treatments and market saturation
4. Scientific plausibility of this drug-disease combination

PROVIDE:
1. Does this drug-disease combination make pharmacological sense? Why or why not?
2. What is the mechanism of action and does it address the disease?
3. Are there existing approved treatments? How saturated is the market?
4. What are the major scientific limitations?
5. Your HONEST research opportunity score (0-10).

Be direct and harsh. If it doesn't make sense, say so."""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            user_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1500,
            )
        )
        
        assessment = response.text
        print("\n📊 GEMINI ASSESSMENT:")
        print(assessment)
        
        # Extract score
        import re
        patterns = [
            r'(?:score|ros)\s*[:\s=]+\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*(?:/10|out of 10)',
            r'research opportunity score.*?(\d+\.?\d*)',
        ]
        
        score = None
        for pattern in patterns:
            match = re.search(pattern, assessment, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    score = max(0.0, min(10.0, score))
                    break
                except (ValueError, IndexError):
                    continue
        
        if score is not None:
            print(f"\n🎯 EXTRACTED SCORE: {score:.1f}/10")
        else:
            print(f"\n⚠️  Could not extract score")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# Test cases
print("\n" + "="*80)
print("KNOWLEDGE-BASED ROS TESTING")
print("Testing if Gemini correctly identifies scientifically invalid combinations")
print("="*80)

# Test 1: Should be VERY LOW - paracetamol for hantavirus
test_query(
    "paracetamol as a cure for hantavirus",
    "Paracetamol (Acetaminophen)",
    "Hantavirus"
)

# Test 2: Should be VERY LOW - aspirin for cancer
test_query(
    "aspirin for treating lung cancer",
    "Aspirin",
    "Lung Cancer"
)

# Test 3: Should be HIGH - GLP-1 for diabetes (real mechanism)
test_query(
    "GLP-1 receptor agonists for type 2 diabetes management",
    "GLP-1 Receptor Agonists",
    "Type 2 Diabetes"
)

# Test 4: Should be MODERATE - CRISPR for sickle cell (real but immature)
test_query(
    "CRISPR-Cas9 for sickle cell disease treatment",
    "CRISPR-Cas9",
    "Sickle Cell Disease"
)

print("\n" + "="*80)
print("✅ Knowledge-based ROS testing complete")
print("="*80 + "\n")
