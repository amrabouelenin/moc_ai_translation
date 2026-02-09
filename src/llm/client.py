import os
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from openai import OpenAI, AzureOpenAI, AsyncAzureOpenAI
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
    
    @abstractmethod
    async def extract_terms(
        self,
        text: str,
        translation: Optional[str] = None,
        target_language: str = "fr"
    ) -> str:
        """Extract technical terminology from text"""
        pass
    
    def _debug_translation_info(self, text: str, prompt: str, glossary_matches: List[GlossaryMatch]):
        """Debug helper to print information about important terms"""
        import logging
        # Check for specific terms of interest
        important_terms = ["data present bit-map", "table de corrélation", "table binaire de présence de données"]
        
        if any(term in text.lower() for term in important_terms):
            logging.info(f"🔍 TRANSLATION DEBUG - Text contains important term")
            logging.info(f"🔍 Source text: {text}")
            for match in glossary_matches or []:
                if any(term in match.term.lower() for term in important_terms):
                    logging.info(f"🔍 Glossary match: '{match.term}' -> '{match.translation}'")
                    if hasattr(match, 'original_translation') and match.original_translation:
                        logging.info(f"🔍 Original translation: '{match.original_translation}'")
            logging.info(f"🔍 Prompt excerpt: {prompt[:300]}...")
            logging.info(f"🔍 End of debug info for important term")


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
                {"role": "system", "content": "You are a professional translator. Return ONLY the translated text without ANY explanations or additional comments."},
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
        self.async_client = AsyncAzureOpenAI(
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
        
        # Add debug information for specific terms
        # self._debug_translation_info(text, prompt, glossary_matches)
        
        response = await self.async_client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are a professional technical translator. Return ONLY the translated text without ANY explanations or additional comments."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        # Print only length of prompt instead of the full content
        return response.choices[0].message.content.strip()
    
    
    async def extract_terms(
        self,
        text: str, 
        translation: Optional[str] = None,
        target_language: str = "fr"
    ) -> str:
        """Extract technical terminology from text using Azure OpenAI"""
        
        # Build extraction prompt instead of translation prompt
        if translation:
            extraction_prompt = f"""

            You are a terminology extraction expert. Extract technical terms from source text and find their exact translations in the target text.

            CRITICAL RULES:
            1. Identify complete technical terms - these are often multi-word compounds that represent a single technical concept
            2. Technical terms should be extracted as complete units, not split into parts
            3. A compound technical term (e.g., "data backup system", "error correction code") should be kept whole
            4. Match each complete source term to its complete translation equivalent
            5. Focus on domain-specific technical vocabulary
            6. Exclude modifiers that are not part of the core term (like "use", "defined", "new", "current", etc.).
            7. limit terms to max  3 words.

            IDENTIFICATION PROCESS:
            - Scan the source for technical terms (look for specialized vocabulary, compound nouns, technical phrases)
            - For each term, identify what constitutes the complete technical concept
            - Find the complete corresponding translation in the target text
            - Verify semantic equivalence between source and target

            PRINCIPLES:
            - Technical compounds are single concepts: treat them as atomic units
            - Avoid splitting technical phrases that function together
            - If multiple words form a specialized meaning together, extract them together
            SYMMETRY PRINCIPLE:
            - If "word" is excluded from source, "it's translation" must be excluded from target

            Output format (JSON only):

            [
                {{"term": "<english term>", "translation": "<translation equivalent>"}}
            ]
  
            Input:

                English: '{text}'

                Translation: {target_language.upper()}: '{translation}'

            """
        else:
            # When no translation is provided, just extract terms from source
            extraction_prompt = f"""
            You are a terminology extraction expert. Extract technical terms from source text.
            
            English: '{text}'
            
            CRITICAL RULES:
            1. Identify complete technical terms - these are often multi-word compounds that represent a single technical concept
            2. Technical terms should be extracted as complete units, not split into parts
            3. A compound technical term (e.g., "data backup system", "error correction code") should be kept whole
            4. Focus on domain-specific technical vocabulary
            5. Exclude modifiers that are not part of the core term (like "use", "defined", "new", "current", etc.).
            6. limit terms to max  3 words.
            
            IDENTIFICATION PROCESS:
            - Scan the source for technical terms (look for specialized vocabulary, compound nouns, technical phrases)
            - For each term, identify what constitutes the complete technical concept
        
            PRINCIPLES:
            - Technical compounds are single concepts: treat them as atomic units
            - Avoid splitting technical phrases that function together
            - If multiple words form a specialized meaning together, extract them together
            
            Output format (JSON only):

                [{{"term": "compound technical term"}}, {{"term": "technical noun phrase"}}]
  
            Input:

                English: '{text}'

            
            """
    
        response = await self.async_client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are a technical terminology extraction system. Return ONLY the JSON array of extracted terms."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.3,
            max_tokens=500
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
                prompt_parts.append(f"- {match.term} → {match.prefered_translation}")
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
        prompt_parts.append("- IMPORTANT: Return ONLY the translated text without ANY explanation, introduction, or additional commentary")
        prompt_parts.append(f"\nText to translate: {text}")
        
        final_prompt = "\n".join(prompt_parts)
        # Only log length for debugging purposes
        print(f"Prompt length: {len(final_prompt)} characters")

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
        
        # Add a system instruction to Claude
        direct_prompt = "You are a professional translator. Return ONLY the translated text without ANY explanations or additional comments. Do not include any notes, clarifications, or alternative translations. Only return the direct translation.\n\n" + prompt
        
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": direct_prompt}
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
        prompt_parts.append("You are a professional translator. Return ONLY the translated text without ANY explanations or additional comments.")
        prompt_parts.append(f"Translate from {source_language} to {target_language}:")
        
        if glossary_matches:
            prompt_parts.append("\nTerms:")
            for match in glossary_matches:
                prompt_parts.append(f"- {match.term}={match.translation}")
        
        prompt_parts.append(f"\nText: {text}")
        prompt_parts.append("\nTranslation only without any explanations:")
        
        return " ".join(prompt_parts)


class LLMFactory:
    @staticmethod
    def create_client(
        provider: str = None,
        backend: str = None,
        memory_mode: str = "rag",
        glossary_manager = None,
        literal_search = None,
        rag_search = None
    ) -> LLMClient:
        """Create appropriate LLM client based on provider and backend"""
        backend = backend or settings.llm_backend
        provider = provider or settings.llm_provider
        
        # If MCP backend is requested, return MCP client
        if backend == "mcp":
            from .mcp_client import MCPLLMClient
            if not all([glossary_manager, literal_search, rag_search]):
                raise ValueError("MCP backend requires glossary_manager, literal_search, and rag_search")
            return MCPLLMClient(
                glossary_manager=glossary_manager,
                literal_search=literal_search,
                rag_search=rag_search,
                memory_mode=memory_mode
            )
        
        # Otherwise use standard LLM clients
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

