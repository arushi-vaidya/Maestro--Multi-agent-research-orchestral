"""
Synchronous LLM Configuration for MAESTRO
Simple synchronous wrapper for Groq and Gemini APIs with rate limit handling
"""

import os
import requests
from typing import Optional
import logging
import time
import random

logger = logging.getLogger(__name__)

def _backoff_sleep(attempt: int, base: float = 1.0, cap: float = 8.0) -> None:
    """Sleep with exponential backoff + jitter to ease rate limits."""
    delay = min(cap, base * (2 ** attempt))
    jitter = random.uniform(0, delay / 2)
    time.sleep(delay + jitter)


def generate_llm_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    max_retries: int = 4  # Slightly higher to absorb transient 429s
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
                status = e.response.status_code if e.response else "unknown"
                if status == 429 and attempt < max_retries - 1:
                    logger.warning(f"Groq rate limit hit (attempt {attempt + 1}/{max_retries}), backing off...")
                    _backoff_sleep(attempt)
                    continue
                else:
                    logger.warning("Groq API failed (status %s): %s, trying Gemini...", status, e)
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
                status = e.response.status_code if e.response else "unknown"
                body = e.response.text[:400] if e.response and e.response.text else ""
                if status == 429 and attempt < max_retries - 1:
                    logger.warning(
                        "Gemini rate limit hit (attempt %s/%s), backing off...",
                        attempt + 1,
                        max_retries,
                    )
                    _backoff_sleep(attempt)
                    continue
                else:
                    logger.error("Gemini API failed (status %s): %s", status, body)
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
    """Generate using Gemini API with multi-model and multi-endpoint fallback."""
    # Try different model + endpoint combinations
    # Format: (model_name, api_version)
    model_configs = [
        ("gemini-2.5-flash", "v1"),
        ("gemini-2.5-flash", "v1beta"),
        ("gemini-2.5-pro", "v1"),
        ("gemini-2.5-pro", "v1beta"),
        ("gemini-pro", "v1"),
        ("gemini-pro", "v1beta"),
    ]
    
    # Combine system prompt with user prompt for Gemini
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"

    payload_template = {
        "contents": [{
            "parts": [{"text": full_prompt}]
        }],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": min(max_tokens, 8192)
        }
    }

    last_error = None
    for model, api_version in model_configs:
        try:
            url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent?key={api_key}"
            response = requests.post(url, json=payload_template, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Gemini model {model} ({api_version}) succeeded")
            return result["candidates"][0]["content"]["parts"][0]["text"]
            
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "unknown"
            error_body = e.response.text[:200] if e.response and e.response.text else "no response body"
            logger.warning(f"Gemini {model} ({api_version}) failed (status {status}): {error_body}")
            last_error = e
            continue
        except Exception as e:
            logger.warning(f"Gemini {model} ({api_version}) failed: {str(e)[:200]}")
            last_error = e
            continue
    
    # If all models failed, raise the last error
    if last_error:
        raise last_error
    else:
        raise Exception("All Gemini model/endpoint combinations failed")


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    test_prompt = "What is the capital of France?"
    try:
        response = generate_llm_response(test_prompt)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
