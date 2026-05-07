#!/usr/bin/env python3
"""
Standalone test: Gemini-based ROS scoring with brutally honest evaluation

This is a simplified test that doesn't import the full backend to avoid dependency issues.
"""

import os
import sys
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Load environment variables from .env
from dotenv import load_dotenv

# Find .env file - check backend/.env first, then .env
env_path = Path(__file__).parent / "backend" / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    env_path = ".env"

load_dotenv(env_path)

# Direct Gemini import (no dependencies)
import google.generativeai as genai

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY not found in .env file")
    print(f"Searched for .env at: {env_path}")
    print("Please ensure backend/.env contains GOOGLE_API_KEY")
    sys.exit(1)

print(f"✅ Loaded GOOGLE_API_KEY from .env: {GOOGLE_API_KEY[:20]}...")
genai.configure(api_key=GOOGLE_API_KEY)


def prepare_evidence_summary(references: List[Dict[str, Any]], insights: List[Dict[str, Any]]) -> str:
    """Prepare a human-readable evidence summary for Gemini"""
    
    trial_count = len([r for r in references if r.get('type') in ['clinical_trial', 'clinical-trial']])
    literature_count = len([r for r in references if r.get('type') == 'literature'])
    patent_count = len([r for r in references if r.get('type') == 'patent'])
    market_count = len([r for r in references if r.get('type') == 'market'])
    
    high_relevance = len([r for r in references if r.get('relevance', 0) > 0.7])
    medium_relevance = len([r for r in references if 0.4 <= r.get('relevance', 0) <= 0.7])
    low_relevance = len([r for r in references if r.get('relevance', 0) < 0.4])
    
    phases = set()
    for ref in references:
        phase = ref.get('phase', '')
        if phase:
            phases.add(phase)
    
    statuses = set()
    for ref in references:
        status = ref.get('status', '')
        if status:
            statuses.add(status.strip())
    
    top_insights = insights[:3] if insights else []
    
    summary = f"""Total Evidence: {len(references)} references
- Clinical Trials: {trial_count}
- Literature: {literature_count}
- Patents: {patent_count}
- Market Data: {market_count}

Evidence Quality:
- High Relevance: {high_relevance}
- Medium Relevance: {medium_relevance}
- Low Relevance: {low_relevance}

Trial Phases Present: {', '.join(sorted(phases)) if phases else 'Unknown'}

Trial Statuses: {', '.join(sorted(statuses)) if statuses else 'Unknown'}

Key Insights from Research:
"""
    for i, insight in enumerate(top_insights, 1):
        text = insight.get('text', str(insight))[:200]
        summary += f"{i}. {text}\n"
    
    return summary


def extract_score_from_gemini(response: str) -> float:
    """Extract numeric ROS score from Gemini response"""
    
    patterns = [
        r'(?:score|ros)\s*[:\s=]+\s*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*(?:/10|out of 10)',
        r'research opportunity score.*?(\d+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            try:
                score = float(match.group(1))
                return max(0.0, min(10.0, score))
            except (ValueError, IndexError):
                continue
    
    numbers = re.findall(r'\b([0-9]\.[0-9]|[0-9])\b', response)
    for num_str in numbers:
        try:
            num = float(num_str)
            if 0 <= num <= 10:
                return num
        except ValueError:
            continue
    
    print("[WARNING] Could not extract score from Gemini response, defaulting to 5.0")
    return 5.0


def calculate_ros_with_gemini_honest(
    query: str,
    references: List[Dict[str, Any]],
    insights: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate ROS using Gemini with BRUTALLY HONEST evaluation.
    """
    
    print(f"\n📞 Calling Gemini API for brutal honesty evaluation...")
    
    # Prepare evidence summary
    evidence_summary = prepare_evidence_summary(references, insights)
    
    # Build brutally honest prompt
    system_prompt = """You are a brutally honest pharmaceutical research analyst. 
Your job is to evaluate research opportunities with NO sugar-coating. 
Be direct about limitations, risks, and market saturation. 
Don't inflate scores - be conservative and realistic.

SCORING GUIDE:
- 9-10: Exceptional opportunity (rare). Novel indication, strong evidence, clear market gap.
- 7-8: Good opportunity. Strong evidence, moderate novelty, real potential.
- 5-6: Moderate opportunity. Mixed signals, some novelty or good evidence but not both.
- 3-4: Weak opportunity. Limited evidence OR high market saturation OR unproven mechanism.
- 0-2: Poor opportunity. Insufficient evidence, saturated market, or major red flags.

Be harsh about: market saturation, conflicting evidence, patent risks, limited trial data."""

    user_prompt = f"""Evaluate the research opportunity for this query:

QUERY: {query}

EVIDENCE SUMMARY:
{evidence_summary}

DETAILED ASSESSMENT:
1. What is the actual novelty level? (be honest about saturation)
2. What are the major limitations of the evidence?
3. What are the realistic market risks?
4. What would need to be true for this to be a GOOD opportunity?
5. Give your HONEST research opportunity score (0-10).

Provide a realistic ROS score, not an inflated one."""

    # Call Gemini
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(
        [system_prompt, user_prompt],
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            max_output_tokens=1500,
        )
    )
    
    gemini_response = response.text
    
    # Extract score
    gemini_score = extract_score_from_gemini(gemini_response)
    
    return {
        "ros_score": gemini_score,
        "gemini_assessment": gemini_response,
        "extraction_method": "gemini_honest",
    }


# Test data
SAMPLE_QUERIES = [
    "GLP-1 receptor agonists for type 2 diabetes",
    "CRISPR gene editing for sickle cell disease",
    "Metformin for cancer prevention",
    "Artificial intelligence for drug discovery",
    "Probiotics for inflammatory bowel disease",
]

SAMPLE_REFERENCES = [
    {
        "title": "Phase 3 Randomized Controlled Trial",
        "type": "clinical_trial",
        "phase": "Phase 3",
        "status": "Recruiting",
        "relevance": 0.9,
        "date": "2025-06-01",
        "agentId": "clinical"
    },
    {
        "title": "Global Market Analysis 2024",
        "type": "market",
        "relevance": 0.7,
        "date": "2024-12-15",
        "agentId": "market"
    },
    {
        "title": "Peer-reviewed Research Publication",
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
    {"text": "Phase 3 data shows strong efficacy in primary endpoints"},
    {"text": "Safety profile similar to current standard of care"},
    {"text": "Market size estimated at $50B globally"},
    {"text": "Multiple competitors in clinical development"},
    {"text": "Patent landscape shows limited freedom to operate"},
]


def main():
    print("\n" + "="*80)
    print("🔬 GEMINI-BASED ROS SCORING - BRUTALLY HONEST EVALUATION")
    print("="*80)
    
    # Test with first few queries
    for i, query in enumerate(SAMPLE_QUERIES[:2], 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {query}")
        print("="*80)
        
        result = calculate_ros_with_gemini_honest(query, SAMPLE_REFERENCES, SAMPLE_INSIGHTS)
        
        print(f"\n✅ ROS Score: {result['ros_score']:.1f}/10")
        print(f"\n📋 Gemini's Brutal Assessment:")
        print("-" * 80)
        print(result['gemini_assessment'])
        print("-" * 80)


if __name__ == "__main__":
    main()
    print("\n✅ Test complete!")
