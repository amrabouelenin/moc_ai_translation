"""
MCP-based LLM client that exposes glossary, literal dictionary, and RAG as tools
"""
from typing import List, Optional, Dict, Any
from .client import LLMClient
from ..glossary.models import GlossaryMatch
from ..memory.models import TranslationMatch
from ..glossary.manager import GlossaryManager
from ..memory.literal_search import LiteralDictionarySearch
from ..memory.rag_search import RAGSearch
import json
import logging
# Change from synchronous to async client
from openai import AsyncAzureOpenAI  # Change this import
from ..core.config import settings
logger = logging.getLogger(__name__)


class MCPLLMClient(LLMClient):
    """LLM client using MCP protocol with tool access to translation resources"""
    
    def __init__(
        self,
        glossary_manager: GlossaryManager,
        literal_search: LiteralDictionarySearch,
        rag_search: RAGSearch,
        memory_mode: str = "rag",
        mcp_server_url: str = "http://localhost:3000"
    ):
        self.glossary_manager = glossary_manager
        self.literal_search = literal_search
        self.rag_search = rag_search
        self.memory_mode = memory_mode
        self.mcp_server_url = mcp_server_url
        self.tools_used = []  # Track which tools were called
        self.memory_has_match = False  # Track if memory found good match
        
        # TODO: Initialize MCP connection here
        # For now, we'll use Azure OpenAI with function calling
        from openai import AzureOpenAI
        from ..core.config import settings
        
        self.client = AsyncAzureOpenAI(  # Change to async client
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version
        )
        self.deployment_name = settings.azure_openai_deployment_name
    
    def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Define MCP tools for the LLM to use"""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "extract_and_search_glossary",
                    "description": "Extract technical terms from the source text and search for their translations in the glossary database. Returns terms with their glossary translations if found.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The source text to extract terms from"
                            },
                            "target_language": {
                                "type": "string",
                                "description": "Target language code (e.g., 'fr', 'es', 'ar')"
                            }
                        },
                        "required": ["text", "target_language"]
                    }
                }
            }
        ]
        
        # Add memory tool based on mode
        if self.memory_mode == "literal":
            tools.append({
                "type": "function",
                "function": {
                    "name": "search_literal_dictionary",
                    "description": "Search for exact translation matches in the literal dictionary. Use this FIRST to check if this exact phrase has been translated before.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The exact text to search for"
                            },
                            "target_language": {
                                "type": "string",
                                "description": "Target language code (e.g., 'fr', 'es', 'ar')"
                            }
                        },
                        "required": ["text", "target_language"]
                    }
                }
            })
        else:  # rag mode
            tools.append({
                "type": "function",
                "function": {
                    "name": "search_translation_memory",
                    "description": "Search for similar translations in the translation memory using semantic search. Use this to find similar previously translated content for context.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The text to search for similar translations"
                            },
                            "target_language": {
                                "type": "string",
                                "description": "Target language code (e.g., 'fr', 'es', 'ar')"
                            }
                        },
                        "required": ["text", "target_language"]
                    }
                }
            })
        
        return tools
        
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool call and return results as JSON string"""
        try:
            
            if tool_name == "extract_and_search_glossary":
                
                # Check if memory was already called in this iteration and found a match
                if "search_literal_dictionary" in self.current_iteration_results:
                    if self.current_iteration_results["search_literal_dictionary"].get("found", False):
                        return json.dumps({"found": False, "message": "Skipping glossary - literal dictionary found match"})
                
                if "search_translation_memory" in self.current_iteration_results:
                    mem_result = self.current_iteration_results["search_translation_memory"]
                    if mem_result.get("found", False):
                        matches = mem_result.get("matches", [])
                        if matches and matches[0].get("similarity", 0) >= 1.0:
                            return json.dumps({"found": False, "message": "Skipping glossary - RAG found exact match"})

                text = arguments["text"]
                target_lang = arguments["target_language"]
                
                # Step 1: Extract terms using existing Azure client
                from .client import AzureOpenAIClient
                import asyncio
                
                azure_client = AzureOpenAIClient()
                json_response = await azure_client.extract_terms(text, None, target_lang)
                
                # Parse extracted terms
                extracted_terms = json.loads(json_response)
                
                if not extracted_terms:
                    return json.dumps({"found": False, "message": "No technical terms found"})
                # Step 2: Search glossary for each extracted term
                glossary_results = []
                all_entries = self.glossary_manager.get_entries(target_lang)
                for term_obj in extracted_terms:
                    term = term_obj.get("term")
                    if term:
                        matches = [e for e in all_entries if term.lower() in e.term.lower() or e.term.lower() in term.lower()]
                        if matches:
                            glossary_results.append({
                                "term": term,
                                "translation": matches[0].preferred_translation,
                                "confidence": 1.0,
                                "notes": matches[0].notes
                            })
                
                if glossary_results:
                    return json.dumps({
                        "found": True,
                        "terms_with_translations": glossary_results,
                        "count": len(glossary_results)
                    })
                else:
                    return json.dumps({
                        "found": False,
                        "message": "Terms extracted but no glossary matches found",
                        "extracted_terms": [t.get("term") for t in extracted_terms]
                    })
            
            elif tool_name == "search_literal_dictionary":
                text = arguments["text"]
                target_lang = arguments["target_language"]
                    
                # Search literal dictionary
                result = self.literal_search.search_literal(text, target_lang)
                    
                if result.matches:
                    match = result.matches[0]
                    self.memory_has_match = True  # Mark that we found a match
                    return json.dumps({
                        "found": True,
                        "translation": match.target_text,
                        "confidence": match.confidence,
                        "message": "Literal dictionary match found"
                    })
                else:
                    return json.dumps({"found": False, "message": "No exact match found"})
            
            elif tool_name == "search_translation_memory":
                text = arguments["text"]
                target_lang = arguments["target_language"]
                
                # Search RAG
                result = self.rag_search.search_similar(text, target_lang)
                
                if result.matches:
                    # Check if we have an exact match
                    best_match = result.matches[0]
                    if best_match.similarity_score >= 1.0:
                        self.memory_has_match = True  # Mark that we found exact match
                    matches_data = [
                        {
                            "source": m.source_text,
                            "translation": m.target_text,
                            "similarity": m.similarity_score,
                            "confidence": m.confidence
                        }
                        for m in result.matches[:3]  # Top 3 matches
                    ]
                    return json.dumps({"found": True, "matches": matches_data, "message": "RAG Similar translations found"})
                else:
                    return json.dumps({"found": False, "message": "No similar translations found"})
            
            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return json.dumps({"error": str(e)})
    

    def _validate_translation(self, source_text: str, translation: str) -> bool:
        """Check if translation looks suspiciously incomplete."""
        source_words = len(source_text.split())
        trans_words = len(translation.split())
        
        # If source has 3+ words but translation is only 1 word, likely truncated
        if source_words >= 3 and trans_words == 1:
            return False
        
        # If translation is less than 30% of source word count (for multi-word sources)
        if source_words >= 4 and trans_words < source_words * 0.3:
            return False
        
        return True
    
    async def _retry_translation(self, text: str, bad_translation: str, target_language: str, source_language: str) -> str:
        """Retry translation with a stricter prompt when validation fails."""
        logger.warning(f"⚠️  Translation looks incomplete: '{text}' -> '{bad_translation}'. Retrying...")
        
        retry_messages = [
            {
                "role": "system",
                "content": f"You are a professional technical translator. Translate from {source_language} to {target_language}. You MUST translate EVERY single word. Do NOT summarize or shorten."
            },
            {
                "role": "user",
                "content": f"The translation \"{bad_translation}\" is INCOMPLETE for the source text \"{text}\". It is missing important words. Please provide the COMPLETE translation that includes ALL words and qualifiers from the source. Return ONLY the corrected translation."
            }
        ]
        
        response = await self.client.chat.completions.create(
            model=self.deployment_name,
            messages=retry_messages,
            temperature=0.1,
            max_tokens=1000
        )
        
        retried = response.choices[0].message.content.strip()
        logger.info(f"🔄 Retry translation: '{text}' -> '{retried}'")
        return retried

    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str = "en",
        glossary_matches: List[GlossaryMatch] = None,
        memory_matches: List[TranslationMatch] = None,
        domain: Optional[str] = None
    ) -> dict:
        """Translate text using MCP with tool access"""
        self.tools_used = []  # reset once at the start
        self.memory_has_match = False  # reset memory match flag
        self.current_iteration_results = {}  # ADD THIS - track results in current iteration

        # Build memory instruction based on mode
        if self.memory_mode == "literal":
            memory_instruction = "3. Use search_literal_dictionary to check for exact phrase matches FIRST"
        else:
            memory_instruction = "3. Use search_translation_memory to find similar previously translated content for context"
        
        
        messages = [
            {
                "role": "system",
                "content": f"""You are a professional technical translator. Translate from {source_language} to {target_language}.
            IMPORTANT INSTRUCTIONS:
            1. Use extract_and_search_glossary to identify technical terms and get their translations
            2. Apply glossary translations exactly as provided
            {memory_instruction}
            3. Return ONLY the translated text without explanations
            4. Maintain technical accuracy and consistency"""
            
            },
            {
                "role": "user",
                "content": f"Translate this text to {target_language}: {text}"
            }
        ]
        
        # Make initial call with tools
        response = await self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            tools=self._get_mcp_tools(),
            tool_choice="auto",
            temperature=0.3,
            max_tokens=1000
        )
        
        # Handle tool calls
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            message = response.choices[0].message
            
            # If no tool calls, we have the final answer
            if not message.tool_calls:
                final_translation = message.content.strip()
                
                # Validate translation completeness
                if not self._validate_translation(text, final_translation):
                    final_translation = await self._retry_translation(text, final_translation, target_language, source_language)
                
                return {
                    "translation": final_translation,
                    "tools_used": list(set(self.tools_used)),
                    "glossary_used": "extract_and_search_glossary" in self.tools_used,
                    "memory_used": any(t in self.tools_used for t in ["search_literal_dictionary", "search_translation_memory"])
                }
            
            # Add assistant message to conversation
            messages.append(message)
            # Execute each tool call
            self.current_iteration_results = {}  # Reset for this iteration
            tool_results = []
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"🔧 MCP Tool Call: {function_name}({function_args})")
                
                # Execute the tool
                function_response = await self._execute_tool(function_name, function_args)
                
                logger.info(f"📊 MCP Tool Response: {function_response}")
                response_data = json.loads(function_response)
                self.current_iteration_results[function_name] = response_data
                
                tool_results.append({
                    "tool_call": tool_call,
                    "function_name": function_name,
                    "response": function_response,
                    "response_data": response_data
                })

            # Post-process: if glossary was called but memory found exact match, override glossary result
            for result in tool_results:
                if result["function_name"] == "extract_and_search_glossary":
                    # Check if memory found exact match
                    should_skip = False
                    
                    if "search_literal_dictionary" in self.current_iteration_results:
                        if self.current_iteration_results["search_literal_dictionary"].get("found", False):
                            should_skip = True
                            
                    if "search_translation_memory" in self.current_iteration_results:
                        mem_result = self.current_iteration_results["search_translation_memory"]
                        if mem_result.get("found", False):
                            matches = mem_result.get("matches", [])
                            if matches and matches[0].get("similarity", 0) >= 1.0:
                                should_skip = True
                    
                    if should_skip:
                        # Override glossary result
                        result["response"] = json.dumps({"found": False, "message": "Skipping glossary - memory found exact match"})
                        result["response_data"] = json.loads(result["response"])
                        self.current_iteration_results[result["function_name"]] = result["response_data"]
                        logger.info(f"📊 MCP Tool Response (overridden): {result['response']}")

            # Add all tool responses to messages and track used tools
            for result in tool_results:
                if result["response_data"].get("found", False):
                    self.tools_used.append(result["function_name"])
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": result["tool_call"].id,
                    "name": result["function_name"],
                    "content": result["response"]
                })
            
            # Get next response
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                tools=self._get_mcp_tools(),
                tool_choice="auto",
                temperature=0.3,
                max_tokens=1000
            )
            
            iteration += 1
        
        # If we hit max iterations, return what we have
        final_translation = response.choices[0].message.content.strip()
        
        # Validate translation completeness
        if not self._validate_translation(text, final_translation):
            final_translation = await self._retry_translation(text, final_translation, target_language, source_language)
        
        # Return dict with metadata for MCP
        return {
            "translation": final_translation,
            "tools_used": list(set(self.tools_used)),
            "glossary_used": "extract_and_search_glossary" in self.tools_used,
            "memory_used": any(t in self.tools_used for t in ["search_literal_dictionary", "search_translation_memory"])
        }
    
    async def extract_terms(
        self,
        text: str,
        translation: Optional[str] = None,
        target_language: str = "fr"
    ) -> str:
        """Extract terms - delegate to existing Azure client for now"""
        # For term extraction, we can reuse the existing implementation
        # or implement MCP-based extraction later
        from .client import AzureOpenAIClient
        azure_client = AzureOpenAIClient()
        return await azure_client.extract_terms(text, translation, target_language)