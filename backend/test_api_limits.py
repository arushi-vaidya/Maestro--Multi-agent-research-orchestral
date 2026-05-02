#!/usr/bin/env python3
"""Test API usage limits for all configured services"""

import os
import time
from dotenv import load_dotenv

load_dotenv()

print("📊 API Usage Limit Check")
print("=" * 60)

# Test Groq
print("\n🔷 Testing Groq API...")
try:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    response = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=10
    )
    print("✅ Groq: Working (no rate limit)")
except Exception as e:
    error_msg = str(e)
    if "429" in error_msg or "rate" in error_msg.lower():
        print(f"⚠️  Groq: RATE LIMITED - {error_msg[:80]}")
    elif "401" in error_msg or "invalid" in error_msg.lower():
        print(f"❌ Groq: INVALID KEY - {error_msg[:80]}")
    elif "quota" in error_msg.lower():
        print(f"❌ Groq: QUOTA EXCEEDED - {error_msg[:80]}")
    else:
        print(f"⚠️  Groq: {error_msg[:80]}")

time.sleep(1)

# Test Google Generative AI
print("\n🔵 Testing Google Generative AI...")
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("test", stream=False)
    print("✅ Google Generative AI: Working (no rate limit)")
except Exception as e:
    error_msg = str(e)
    if "429" in error_msg or "rate" in error_msg.lower():
        print(f"⚠️  Google: RATE LIMITED - {error_msg[:80]}")
    elif "401" in error_msg or "invalid" in error_msg.lower():
        print(f"❌ Google: INVALID KEY - {error_msg[:80]}")
    elif "quota" in error_msg.lower() or "Quota" in error_msg:
        print(f"❌ Google: QUOTA EXCEEDED - {error_msg[:80]}")
    elif "not found" in error_msg.lower() or "404" in error_msg:
        print(f"⚠️  Google: MODEL NOT FOUND - {error_msg[:80]}")
    else:
        print(f"⚠️  Google: {error_msg[:80]}")

time.sleep(1)

# Test SerpAPI
print("\n🟢 Testing SerpAPI...")
try:
    from serpapi import GoogleSearch
    params = {
        "q": "test",
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "engine": "google"
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    
    if "error" in results:
        print(f"⚠️  SerpAPI: {results['error']}")
    else:
        print("✅ SerpAPI: Working (no rate limit)")
except Exception as e:
    error_msg = str(e)
    if "429" in error_msg or "rate" in error_msg.lower():
        print(f"⚠️  SerpAPI: RATE LIMITED - {error_msg[:80]}")
    elif "401" in error_msg or "invalid" in error_msg.lower():
        print(f"❌ SerpAPI: INVALID KEY - {error_msg[:80]}")
    else:
        print(f"⚠️  SerpAPI: {error_msg[:80]}")

print("\n" + "=" * 60)
print("✨ Limit check complete!")
