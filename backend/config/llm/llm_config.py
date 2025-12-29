"""
LLM Configuration for MAESTRO
Supports both Google Gemini and OpenAI
"""
import os
from typing import Optional
import google.generativeai as genai
from openai import AsyncOpenAI

class LLMConfig:
    """Configure and manage LLM connections"""
    
    def __init__(self):
        # Get API keys from environment
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Default model preferences
        self.use_gemini = bool(self.google_api_key)  # Prefer Gemini if available
        self.use_openai = bool(self.openai_api_key)
        
        # Model configurations
        self.gemini_model = "gemini-2.5-flash"
        self.openai_model = "gpt-4o-mini"  # or gpt-4
        
        # Generation parameters
        self.temperature = 0.7
        self.max_tokens = 2000
        
        # Initialize clients
        self._init_clients()
    
    def _init_clients(self):
        """Initialize LLM clients"""
        if self.use_gemini and self.google_api_key:
            genai.configure(api_key=self.google_api_key)
            print("✅ Google Gemini configured")
        
        if self.use_openai and self.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
            print("✅ OpenAI configured")
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text using available LLM
        Tries Gemini first, falls back to OpenAI
        """
        # Try Gemini first
        if self.use_gemini:
            try:
                return await self._generate_gemini(prompt, system_prompt)
            except Exception as e:
                print(f"Gemini error: {e}, trying OpenAI...")
        
        # Fallback to OpenAI
        if self.use_openai:
            try:
                return await self._generate_openai(prompt, system_prompt)
            except Exception as e:
                print(f"OpenAI error: {e}")
                raise
        
        raise Exception("No LLM API key configured. Set GOOGLE_API_KEY or OPENAI_API_KEY")
    
    async def _generate_gemini(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using Google Gemini"""
        model = genai.GenerativeModel(self.gemini_model)
        
        # Combine system prompt with user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
        )
        
        return response.text
    
    async def _generate_openai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using OpenAI"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = await self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content

# Global LLM config instance
llm_config = LLMConfig()

async def generate_llm_response(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Helper function to generate LLM response"""
    return await llm_config.generate_text(prompt, system_prompt)