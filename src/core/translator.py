import asyncio
import time
import logging
from typing import List, Optional, Dict, Any
from ..glossary.manager import GlossaryManager
from ..memory.rag_search import RAGSearch
from ..llm.client import LLMFactory
from ..api.models import TranslationResponse, TranslationRequest
from ..glossary.models import GlossaryExtractionResult
from ..memory.models import SearchResult
from ..core.config import settings
from ..memory.models import TranslationMemoryEntry
from ..memory.literal_search import LiteralDictionarySearch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranslationOrchestrator:
    def __init__(self, llm_backend: str = "azure", memory_mode: str = "rag"):
        self.glossary_manager = GlossaryManager()
        self.rag_search = RAGSearch()
        self.literal_search = LiteralDictionarySearch()
        self.llm_backend = llm_backend
        self.memory_mode = memory_mode
        
        try:
            self.llm_client = LLMFactory.create_client(
                backend=llm_backend,
                memory_mode=memory_mode,
                glossary_manager=self.glossary_manager,
                literal_search=self.literal_search,
                rag_search=self.rag_search
            )
            logger.info("✅ LLM client initialized successfully (backend=%s)", llm_backend)
        except Exception as e:
            logger.warning("⚠️  LLM client initialization failed: %s", str(e))
            self.llm_client = None
    
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """Main translation orchestrator"""
        start_time = time.time()
        
        # More concise logging
        logger.info("🔄 '%s' -> %s", request.text, request.target_language)        
        
        # Step 1: Search translation memory
        memory_result = SearchResult()
        if request.use_memory and self.llm_backend != "mcp":
            
            search_mode = request.memory_search_mode or "rag"  # default to rag
            
            if search_mode == "literal":
                memory_result = self.literal_search.search_literal(
                    request.text,
                    request.target_language,
                    request.source_language
                )
                logger.info("📖 Literal dictionary matches: %d", len(memory_result.matches))
                logger.info("memory_result.matches: %s", memory_result.matches)
            else:  # rag mode
                memory_result = self.rag_search.search_similar(
                    request.text,
                    request.target_language,
                    request.source_language
                )
                logger.info("🧠 RAG semantic matches: %d", len(memory_result.matches))
          
                

        # Step 2: Extract glossary terms
        glossary_result = GlossaryExtractionResult()
        if request.use_glossary and self.llm_backend != "mcp":
            # Always use LLM-based extraction with no fallback to traditional extraction
            translation_so_far = ""

            # Use the already-fetched memory result for term extraction
            if memory_result.matches and memory_result.matches[0].similarity_score > 0.9:
                translation_so_far = memory_result.matches[0].target_text

            # Extract terms from english sentence using LLM provided the translation of that sentence
            glossary_result = await self.glossary_manager.extract_terms(
                request.text,
                translation_so_far,
                request.target_language
            )

            logger.info("📚 Glossary matches found: %d", len(glossary_result.matches))

        # Step 3: Get translation
        translation = ""
        glossary_corrected = False
        translation_source = "unknown"  # Track actual source used
        if self.llm_client:
            if self.llm_backend == "mcp":
                mcp_result = await self.llm_client.translate(
                    request.text,
                    request.target_language,
                    request.source_language,
                    glossary_result.matches,
                    memory_result.matches,
                    request.domain
                )

                # MCP returns dict with metadata
                if isinstance(mcp_result, dict):
                    translation = mcp_result["translation"]
                    glossary_used = mcp_result.get("glossary_used", False)
                    memory_used = mcp_result.get("memory_used", False)
                    memory_type = "RAG" if request.memory_search_mode == "rag" else "Literal"
                    translation_source = f"MCP (active retrieval, {memory_type})"
                    # if glossary_used:
                    #     translation_source += ", Glossary Used"
                    # if memory_used:
                    #     translation_source += ", Previous Translation Used"
                else:
                    # Fallback for backward compatibility
                    raise ValueError("MCP returned unexpected result type: ")
                logger.info("✅ MCP Translation: '%s'", translation)
                
                # MCP handles its own memory, but we still add to literal dictionary for future use
                if request.memory_search_mode == "literal":
                    self.literal_search.add_translation(
                        source_text=request.text,
                        target_text=translation,
                        target_language=request.target_language,
                        metadata=request.metadata
                    )
                elif request.memory_search_mode == "rag":
                    # Store MCP translation to RAG for future reference
                    entry = TranslationMemoryEntry(
                        source_text=request.text,
                        target_text=translation,
                        source_language=request.source_language,
                        target_language=request.target_language,
                        confidence=0.95,
                        metadata={"source": "mcp"}
                    )
                    self.rag_search.add_and_update_index(entry)
                    
            else: # standard Azure LLM
                if memory_result.matches:
        
                    best_match = max(memory_result.matches, key=lambda x: x.similarity_score)
                    if best_match.similarity_score > 0.9:
                    
                        translation = best_match.target_text
                        original_translation = translation
                        # Set source based on memory mode
                        if request.memory_search_mode == "literal":
                            translation_source = "Using Literal Dictionary"
                        else:
                            translation_source = "Using RAG=Similar translation used"

                        # Apply glossary terms to the translation
                        if glossary_result and glossary_result.matches:
                            translation = await self._apply_glossary_terms(translation, glossary_result)

                            # Check if translation was modified
                            if translation != original_translation:
                                glossary_corrected = True
                                logger.info("📝 Glossary applied: '%s' → '%s'", original_translation, translation)
                                
                                # Update RAG database with corrected translation
                                corrected_entry = TranslationMemoryEntry(
                                    source_text=request.text,
                                    target_text=translation,
                                    source_language=request.source_language,
                                    target_language=request.target_language,
                                    confidence=0.95,
                                    metadata={
                                        "glossary_corrected": True,
                                        "original_translation": original_translation,
                                        "glossary_terms_applied": len(glossary_result.matches)
                                    }
                                )
                                self.rag_search.add_and_update_index(corrected_entry)
                                logger.debug("🔄 Updated RAG with corrected translation")

                    else: # mean there is no match found from RAG similar search
                        # No high-confidence match found, use LLM
                        translation = None

                else:
                    # No memory matches at all, use LLM
                    translation = None
                # If we don't have a translation yet (no RAG match or low confidence), use LLM
                if translation is None:
                    translation = await self.llm_client.translate(
                        request.text,
                        request.target_language,
                        request.source_language,
                        glossary_result.matches,
                        memory_result.matches,
                        request.domain
                    )
                    logger.info("✅ LLM: '%s'", translation)
                    translation_source = settings.llm_provider
                    
                    # If using literal mode, add to dictionary immediately
                    if request.memory_search_mode == "literal":
                        self.literal_search.add_translation(
                            source_text=request.text,
                            target_text=translation,
                            target_language=request.target_language,
                            metadata=request.metadata
                        )
                    # Only store to database if using RAG mode
                    if request.memory_search_mode == "rag":
                        self._store_llm_translation(request, translation, glossary_result, memory_result)       

        # Calculate confidence
        confidence = self._calculate_confidence(glossary_result, memory_result)
        
        processing_time = time.time() - start_time
        
        return TranslationResponse(
            translation=translation,
            source_text=request.text,
            target_language=request.target_language,
            glossary_matches=[{
                "term": m.term,
                "translation": m.prefered_translation,
                "confidence": m.confidence,
                "notes": m.notes
            } for m in glossary_result.matches],
            memory_matches=[{
                "source_text": m.source_text,
                "target_text": m.target_text,
                "similarity_score": m.similarity_score,
                "confidence": m.confidence
            } for m in memory_result.matches],
            confidence=confidence,
            model_used=translation_source,
            processing_time=processing_time
        )
    
    def _store_llm_translation(
        self,
        request: TranslationRequest,
        translation: str,
        glossary_result: GlossaryExtractionResult,
        memory_result: SearchResult
    ) -> None:
        """Store LLM translation in RAG database with confidence-based logic"""
        try:
            # Calculate confidence for this translation
            confidence = self._calculate_confidence(glossary_result, memory_result)
            
            # Only auto-store if confidence is reasonable
            # Lower threshold (0.5) to store all LLM translations
            if confidence >= 0.5:
                from ..memory.models import TranslationMemoryEntry
                
                entry = TranslationMemoryEntry(
                    source_text=request.text,
                    target_text=translation,
                    source_language=request.source_language,
                    target_language=request.target_language,
                    domain=request.domain,
                    confidence=confidence,
                    metadata={
                        "source": "llm_auto_stored",
                        "llm_provider": settings.llm_provider,
                        "model": settings.model_name,
                        "glossary_terms_used": len(glossary_result.matches),
                        "memory_matches_provided": len(memory_result.matches)
                    }
                )
                
                self.rag_search.add_and_update_index(entry)
                logger.debug("💾 Stored in RAG (confidence: %.2f)", confidence)
            else:
                logger.debug("⏭️  Skipped store (confidence: %.2f)", confidence)
                
        except Exception as e:
            logger.warning("⚠️ RAG store failed: %s", str(e))
    
    async def _apply_glossary_terms(self, translation: str, glossary_result: GlossaryExtractionResult) -> str:
        """Apply glossary term replacements to translation"""
        corrected_translation = translation
        replacements_made = []
        
        # Add debug logging for terms
        logger.debug("Applying glossary terms to translation: '%s...'", translation[:100])

        # Import re at the function level for better locality
        import re
        
        # Process all matches directly - no need for the intermediate term_variations structure
        for match in glossary_result.matches:
            term = match.term
            preferred = match.prefered_translation
            original_translation = match.original_translation
           
            # Use word boundaries to avoid partial replacements
            pattern = re.compile(r'\b' + re.escape(original_translation.lower()) + r'\b', re.IGNORECASE)
            
            # Check if the term appears in the translation
            if pattern.search(corrected_translation.lower()):
                # Replace term with preferred translation
                new_translation = pattern.sub(preferred, corrected_translation)
                
                if new_translation != corrected_translation:
                    logger.debug("  Replaced term '%s' with '%s'", term, preferred)
                    corrected_translation = new_translation
                    replacements_made.append({
                        'term': term,
                        'from': term,
                        'to': preferred
                    })
        
        # If replacements were made, log them and perform grammar correction
        if replacements_made:
            logger.info("Made %d glossary term replacements", len(replacements_made))
            logger.info("📝 Glossary applied: '%s' → '%s'", 
                        translation[:100] + "..." if len(translation) > 100 else translation,
                        corrected_translation[:100] + "..." if len(corrected_translation) > 100 else corrected_translation)
            corrected_translation = await self._correct_grammar(corrected_translation, replacements_made)
            
        return corrected_translation
        
    async def _correct_grammar(self, text: str, replacements_made: list) -> str:
        """Correct grammar issues that might arise from term replacements"""
        # Skip if no LLM client available or no replacements were made
        if not hasattr(self, 'llm_client') or not replacements_made:
            return text
            
        try:
            # Construct a prompt asking the LLM to fix any grammar issues
            correction_prompt = f"""Fix any grammar issues in this text that might have been caused by terminology replacements,
            but DO NOT change any technical terminology. Only fix articles, prepositions, gender agreement, etc.
            
            Original text: '{text}'
            
            The following replacements were made:
            {', '.join([f"'{r['from']}' → '{r['to']}'" for r in replacements_made])}
            
            Return ONLY the corrected text with no explanations or other commentary."""

            corrected_text = await self.llm_client.translate(
                text=correction_prompt,
                target_language="fr",
                source_language="fr"
            )
            if corrected_text and 0.9 <= len(corrected_text) / len(text) <= 1.1:
                return corrected_text
            else:
                logger.warning("Grammar correction skipped: LLM returned text with significant length change")
                return text
        except (ValueError, KeyError, TypeError) as e:
            logger.warning("Error during grammar correction (value/type issue): %s", str(e))
            return text  # Return original text if correction fails
        except IOError as e:
            logger.warning("Error during grammar correction (I/O issue): %s", str(e))
            return text  # Return original text if I/O failure
        except Exception as e:
            # Still catch other exceptions as fallback, but log it differently
            logger.warning("Unexpected error during grammar correction: %s", str(e))
            return text  # Return original text for any unexpected error
    
    def _calculate_confidence(self, glossary_result: GlossaryExtractionResult, memory_result: SearchResult) -> float:
        """Calculate confidence based on glossary and memory matches"""
        confidence = 0.5
        
        if glossary_result.matches:
            glossary_confidence = sum(m.confidence for m in glossary_result.matches) / len(glossary_result.matches)
            confidence += glossary_confidence * 0.3
        
        if memory_result.matches:
            best_match = max(memory_result.matches, key=lambda x: x.similarity_score)
            confidence += best_match.similarity_score * 0.2
        
        return min(confidence, 1.0)
    
    async def test_components(self) -> Dict[str, Any]:
        """Test all components and return detailed results"""
        results = {
            "glossary": {},
            "memory": {},
            "rag": {},
            "llm": {},
            "overall": {}
        }
        
        logger.info("🧪 Starting component testing...")
        
        # Test glossary
        try:
            test_text = "The cloud server and database connection failed"
            glossary_result = self.glossary_manager.extract_terms(test_text, "fr")
            results["glossary"] = {
                "status": "✅ Working",
                "terms_found": len(glossary_result.matches),
                "sample_matches": [{"term": m.term, "translation": m.translation} for m in glossary_result.matches[:3]]
            }
        except Exception as e:
            results["glossary"] = {"status": "❌ Failed", "error": str(e)}
        
        # Test RAG search
        try:
            search_result = self.rag_search.search_similar("The server is down", "fr")
            results["rag"] = {
                "status": "✅ Working",
                "matches_found": len(search_result.matches),
                "index_size": self.rag_search.get_stats()["index_size"]
            }
        except Exception as e:
            results["rag"] = {"status": "❌ Failed", "error": str(e)}
        
        # Test LLM
        try:
            if self.llm_client:
                test_request = TranslationRequest(
                    text="Hello world",
                    target_language="fr"
                )
                result = await self.translate(test_request)
                results["llm"] = {
                    "status": "✅ Working",
                    "translation": result.translation,
                    "processing_time": result.processing_time
                }
            else:
                results["llm"] = {
                    "status": "⚠️  Fallback mode",
                    "note": "Using fallback translation"
                }
        except Exception as e:
            results["llm"] = {"status": "❌ Failed", "error": str(e)}
        
        # Overall status
        working = sum(1 for v in results.values() if isinstance(v, dict) and "✅" in v.get("status", ""))
        total = len([k for k in results.keys() if k != "overall"])
        results["overall"] = {
            "status": f"✅ {working}/{total} components working",
            "timestamp": time.time()
        }
        
        return results
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            return {
                "glossary": {
                    "total_terms": len(self.glossary_manager.get_entries()),
                    "languages": ["fr"]
                },
                "memory": {
                    "total_entries": len(self.rag_search.tm_manager.get_all_entries()),
                    "index_size": self.rag_search.get_stats()["index_size"]
                },
                "llm": {
                    "provider": settings.llm_provider,
                    "model": settings.model_name,
                    "status": "connected" if self.llm_client else "fallback"
                }
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
