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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranslationOrchestrator:
    def __init__(self):
        self.glossary_manager = GlossaryManager()
        self.rag_search = RAGSearch()
        try:
            self.llm_client = LLMFactory.create_client()
            logger.info("✅ LLM client initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️  LLM client initialization failed: {e}")
            self.llm_client = None
    
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """Main translation orchestrator with fallback"""
        start_time = time.time()
        
        logger.info(f"🔄 Starting translation: '{request.text}' -> {request.target_language}")
        
        # Step 1: Extract glossary terms
        glossary_result = GlossaryExtractionResult()
        if request.use_glossary:
            glossary_result = self.glossary_manager.extract_terms(
                request.text, 
                request.target_language
            )
            logger.info(f"📚 Glossary matches found: {len(glossary_result.matches)}")
        
        # Step 2: Search translation memory
        memory_result = SearchResult()
        if request.use_memory:
            memory_result = self.rag_search.search_similar(
                request.text,
                request.target_language,
                request.source_language
            )
            logger.info(f"🧠 Memory matches found: {len(memory_result.matches)}")
        
        # Step 3: Get translation
        translation = ""
        if self.llm_client:
            if memory_result.matches:
                best_match = max(memory_result.matches, key=lambda x: x.similarity_score)
                if best_match.similarity_score > 0.8:
                    translation = best_match.target_text
                    logger.info(f"✅ Using high-confidence memory match: '{translation}'")
                else:
                    try:
                        translation = await self.llm_client.translate(
                            request.text,
                            request.target_language,
                            request.source_language,
                            glossary_result.matches,
                            memory_result.matches,
                            request.domain
                        )
                        logger.info(f"✅ Translation completed via LLM: '{translation}'")
                    except Exception as e:
                        logger.error(f"❌ LLM translation failed: {e}")
                        translation = self._fallback_translate(request, memory_result)
            else:
                try:
                    translation = await self.llm_client.translate(
                        request.text,
                        request.target_language,
                        request.source_language,
                        glossary_result.matches,
                        memory_result.matches,
                        request.domain
                    )
                    logger.info(f"✅ Translation completed via LLM: '{translation}'")
                except Exception as e:
                    logger.error(f"❌ LLM translation failed: {e}")
                    translation = self._fallback_translate(request, memory_result)
        else:
            # Fallback translation
            translation = self._fallback_translate(request, memory_result)
        
        # Calculate confidence
        confidence = self._calculate_confidence(glossary_result, memory_result)
        
        processing_time = time.time() - start_time
        
        return TranslationResponse(
            translation=translation,
            source_text=request.text,
            target_language=request.target_language,
            glossary_matches=[{
                "term": m.term,
                "translation": m.translation,
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
            model_used=settings.llm_provider if self.llm_client else "fallback",
            processing_time=processing_time
        )
    
    def _fallback_translate(self, request: TranslationRequest, memory_result: SearchResult) -> str:
        """Fallback translation using memory matches"""
        if memory_result.matches:
            best_match = max(memory_result.matches, key=lambda x: x.similarity_score)
            if best_match.similarity_score > 0.8:
                return best_match.target_text
        
        # Simple word-by-word translation
        text = request.text
        glossary = self.glossary_manager.get_entries(request.target_language)
        
        for entry in glossary:
            text = text.replace(entry.term, entry.preferred_translation)
        
        return text
    
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
