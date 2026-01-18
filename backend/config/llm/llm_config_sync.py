"""
Synchronous LLM Configuration for MAESTRO
Simple synchronous wrapper for Groq and Gemini APIs with rate limit handling
"""

import os
import requests
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)

def generate_llm_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    max_retries: int = 2  # NEW: Add retry parameter
) -> str:
    """
    Generate LLM response using available APIs
    Tries Groq first, falls back to Gemini, with retry logic for rate limits

    Args:
        prompt: User prompt
        system_prompt: System prompt (optional)
        temperature: Temperature for generation
        max_tokens: Maximum tokens to generate
        max_retries: Maximum retry attempts for rate limits (default: 2)

    Returns:
        Generated text
    """
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    gemini_api_key = os.getenv("GOOGLE_API_KEY", "")

    # Try Groq first (faster, free tier available)
    if groq_api_key:
        for attempt in range(max_retries):
            try:
                return _generate_groq(prompt, system_prompt, temperature, max_tokens, groq_api_key)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s...
                    logger.warning(f"Groq rate limit hit (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.warning(f"Groq API failed: {e}, trying Gemini...")
                    break
            except Exception as e:
                logger.warning(f"Groq API failed: {e}, trying Gemini...")
                break

    # Fall back to Gemini
    if gemini_api_key:
        for attempt in range(max_retries):
            try:
                return _generate_gemini(prompt, system_prompt, temperature, max_tokens, gemini_api_key)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = (2 ** attempt)
                    logger.warning(f"Gemini rate limit hit (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Gemini API failed: {e}")
                    raise
            except Exception as e:
                logger.error(f"Gemini API failed: {e}")
                raise

    raise Exception("No LLM API key configured or all attempts exhausted. Set GROQ_API_KEY or GOOGLE_API_KEY")


def _generate_groq(
    prompt: str,
    system_prompt: Optional[str],
    temperature: float,
    max_tokens: int,
    api_key: str
) -> str:
    """Generate using Groq API"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "llama-3.3-70b-versatile",  # Groq's most capable model for complex tasks
        "messages": messages,
        "temperature": temperature,
        "max_tokens": min(max_tokens, 8000)  # Groq limit: 8000 tokens
    }

    response = requests.post(url, json=payload, headers=headers, timeout=60)  # Increased timeout
    response.raise_for_status()

    result = response.json()
    return result["choices"][0]["message"]["content"]


def _generate_gemini(
    prompt: str,
    system_prompt: Optional[str],
    temperature: float,
    max_tokens: int,
    api_key: str
) -> str:
    """Generate using Gemini API"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"

    # Combine system prompt with user prompt for Gemini
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"

    payload = {
        "contents": [{
            "parts": [{"text": full_prompt}]
        }],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": min(max_tokens, 8192)  # Gemini 2.0 limit: 8192 tokens
        }
    }

    response = requests.post(url, json=payload, timeout=60)  # Increased timeout
    response.raise_for_status()

    result = response.json()
    return result["candidates"][0]["content"]["parts"][0]["text"]


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    test_prompt = "What is the capital of France?"
    try:
        response = generate_llm_response(test_prompt)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
