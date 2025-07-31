import os
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from openai import OpenAI, AzureOpenAI
import anthropic
from ..core.config import settings
from ..glossary.models import GlossaryMatch
from ..memory.models import TranslationMatch


class LLMClient(ABC):
    @abstractmethod
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str = "en",
        glossary_matches: List[GlossaryMatch] = None,
        memory_matches: List[TranslationMatch] = None,
        domain: Optional[str] = None
    ) -> str:
        pass


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or settings.openai_api_key)
        self.model = settings.model_name
    
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str = "en",
        glossary_matches: List[GlossaryMatch] = None,
        memory_matches: List[TranslationMatch] = None,
        domain: Optional[str] = None
    ) -> str:
        """Translate text using OpenAI GPT"""
        
        prompt = self._build_prompt(
            text=text,
            target_language=target_language,
            source_language=source_language,
            glossary_matches=glossary_matches or [],
            memory_matches=memory_matches or [],
            domain=domain
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a professional translator specializing in technical and business content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content.strip()
    
    def _build_prompt(
        self,
        text: str,
        target_language: str,
        source_language: str,
        glossary_matches: List[GlossaryMatch],
        memory_matches: List[TranslationMatch],
        domain: Optional[str]
    ) -> str:
        """Build MCP-style prompt with context"""
        
        prompt_parts = []
        
        # Translation instructions
        prompt_parts.append(f"Translate the following text from {source_language} to {target_language}:")
        
        # Domain context
        if domain:
            prompt_parts.append(f"Domain: {domain}")
        
        # Glossary terms
        if glossary_matches:
            prompt_parts.append("\nGlossary Terms:")
            for match in glossary_matches:
                prompt_parts.append(f"- {match.term} → {match.translation}")
                if match.notes:
                    prompt_parts.append(f"  Note: {match.notes}")
        
        # Translation memory matches
        if memory_matches:
            prompt_parts.append("\nTranslation Memory Matches:")
            for match in memory_matches:
                prompt_parts.append(f"- Source: {match.source_text}")
                prompt_parts.append(f"  Translation: {match.target_text}")
                prompt_parts.append(f"  Confidence: {match.confidence}")
        
        # Final instruction
        prompt_parts.append("\nTranslation Instructions:")
        prompt_parts.append("- Maintain the original meaning and tone")
        prompt_parts.append("- Use the provided glossary terms exactly as specified")
        prompt_parts.append("- Follow the style shown in the translation memory examples")
        prompt_parts.append(f"\nText to translate: {text}")
        
        return "\n".join(prompt_parts)


class AzureOpenAIClient(LLMClient):
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version
        )
        self.deployment_name = settings.azure_openai_deployment_name
    
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str = "en",
        glossary_matches: List[GlossaryMatch] = None,
        memory_matches: List[TranslationMatch] = None,
        domain: Optional[str] = None
    ) -> str:
        """Translate text using Azure OpenAI"""
        
        prompt = self._build_prompt(
            text=text,
            target_language=target_language,
            source_language=source_language,
            glossary_matches=glossary_matches or [],
            memory_matches=memory_matches or [],
            domain=domain
        )
        
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are a professional translator specializing in technical and business content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        print(f"Constructed prompt: {prompt}")
        return response.choices[0].message.content.strip()
    
    def _build_prompt(
        self,
        text: str,
        target_language: str,
        source_language: str,
        glossary_matches: List[GlossaryMatch],
        memory_matches: List[TranslationMatch],
        domain: Optional[str]
    ) -> str:
        """Build MCP-style prompt with context"""
        
        prompt_parts = []
        
        # Translation instructions
        prompt_parts.append(f"Translate the following text from {source_language} to {target_language}:")
        
        # Domain context
        if domain:
            prompt_parts.append(f"Domain: {domain}")
        
        # Glossary terms
        if glossary_matches:
            prompt_parts.append("\nGlossary Terms:")
            for match in glossary_matches:
                prompt_parts.append(f"- {match.term} → {match.translation}")
                if match.notes:
                    prompt_parts.append(f"  Note: {match.notes}")
        
        # Translation memory matches
        if memory_matches:
            prompt_parts.append("\nTranslation Memory Matches:")
            for match in memory_matches:
                prompt_parts.append(f"- Source: {match.source_text}")
                prompt_parts.append(f"  Translation: {match.target_text}")
                prompt_parts.append(f"  Confidence: {match.confidence}")
        
        # Final instruction
        prompt_parts.append("\nTranslation Instructions:")
        prompt_parts.append("- Maintain the original meaning and tone")
        prompt_parts.append("- Use the provided glossary terms exactly as specified")
        prompt_parts.append("- Follow the style shown in the translation memory examples")
        prompt_parts.append(f"\nText to translate: {text}")
        
        final_prompt = "\n".join(prompt_parts)
        print(f"Constructed prompt: {final_prompt}.")  # Log first 100 characters for debugging
        print(f"Full prompt length: {len(final_prompt)} characters")

        return final_prompt


class AnthropicClient(LLMClient):
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key or settings.anthropic_api_key)
    
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str = "en",
        glossary_matches: List[GlossaryMatch] = None,
        memory_matches: List[TranslationMatch] = None,
        domain: Optional[str] = None
    ) -> str:
        """Translate text using Anthropic Claude"""
        
        prompt = self._build_prompt(
            text=text,
            target_language=target_language,
            source_language=source_language,
            glossary_matches=glossary_matches or [],
            memory_matches=memory_matches or [],
            domain=domain
        )
        
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text.strip()
    
    def _build_prompt(
        self,
        text: str,
        target_language: str,
        source_language: str,
        glossary_matches: List[GlossaryMatch],
        memory_matches: List[TranslationMatch],
        domain: Optional[str]
    ) -> str:
        """Build MCP-style prompt with context"""
        
        prompt_parts = []
        
        # Translation instructions
        prompt_parts.append(f"Translate the following text from {source_language} to {target_language}:")
        
        # Domain context
        if domain:
            prompt_parts.append(f"Domain: {domain}")
        
        # Glossary terms
        if glossary_matches:
            prompt_parts.append("\nGlossary Terms:")
            for match in glossary_matches:
                prompt_parts.append(f"- {match.term} → {match.translation}")
                if match.notes:
                    prompt_parts.append(f"  Note: {match.notes}")
        
        # Translation memory matches
        if memory_matches:
            prompt_parts.append("\nTranslation Memory Matches:")
            for match in memory_matches:
                prompt_parts.append(f"- Source: {match.source_text}")
                prompt_parts.append(f"  Translation: {match.target_text}")
                prompt_parts.append(f"  Confidence: {match.confidence}")
        
        # Final instruction
        prompt_parts.append("\nTranslation Instructions:")
        prompt_parts.append("- Maintain the original meaning and tone")
        prompt_parts.append("- Use the provided glossary terms exactly as specified")
        prompt_parts.append("- Follow the style shown in the translation memory examples")
        prompt_parts.append(f"\nText to translate: {text}")
        
        return "\n".join(prompt_parts)


class LocalModelClient(LLMClient):
    def __init__(self, model_name: str = "llama2"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/generate"
    
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str = "en",
        glossary_matches: List[GlossaryMatch] = None,
        memory_matches: List[TranslationMatch] = None,
        domain: Optional[str] = None
    ) -> str:
        """Translate text using local Ollama model"""
        
        prompt = self._build_prompt(
            text=text,
            target_language=target_language,
            source_language=source_language,
            glossary_matches=glossary_matches or [],
            memory_matches=memory_matches or [],
            domain=domain
        )
        
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
            ) as response:
                result = await response.json()
                return result.get("response", "").strip()
    
    def _build_prompt(
        self,
        text: str,
        target_language: str,
        source_language: str,
        glossary_matches: List[GlossaryMatch],
        memory_matches: List[TranslationMatch],
        domain: Optional[str]
    ) -> str:
        """Build MCP-style prompt with context"""
        
        prompt_parts = []
        
        # Translation instructions
        prompt_parts.append(f"Translate from {source_language} to {target_language}:")
        
        if glossary_matches:
            prompt_parts.append("\nTerms:")
            for match in glossary_matches:
                prompt_parts.append(f"- {match.term}={match.translation}")
        
        prompt_parts.append(f"\nText: {text}")
        prompt_parts.append("\nTranslation:")
        
        return " ".join(prompt_parts)


class LLMFactory:
    @staticmethod
    def create_client(provider: str = None) -> LLMClient:
        """Create appropriate LLM client based on provider"""
        provider = provider or settings.llm_provider
        
        if provider == "openai":
            return OpenAIClient()
        elif provider == "azure":
            return AzureOpenAIClient()
        elif provider == "anthropic":
            return AnthropicClient()
        elif provider == "local":
            return LocalModelClient()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
