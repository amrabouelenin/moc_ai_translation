import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ..core.translator import TranslationOrchestrator
from ..api.models import TranslationRequest, TranslationResponse, FeedbackRequest, HealthResponse
from ..core.config import settings
from ..memory.models import TranslationMemoryEntry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Translation System",
    description="Advanced AI translation with glossary, RAG, and MCP-style prompts",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize translator
translator = TranslationOrchestrator()


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("🚀 Starting AI Translation System...")
    logger.info("📡 Server: http://0.0.0.0:8000")
    logger.info("🔧 LLM Provider: Azure OpenAI")
    logger.info("📊 Database: sqlite:///./translation.db")
    logger.info("📚 Vector DB: ./data/vector_index.faiss")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with system info"""
    return {
        "message": "AI Translation System is running",
        "docs": "/docs",
        "health": "/health",
        "test": "/test",
        "stats": "/stats",
        "glossary_debug": "/debug/glossary",
        "memory_debug": "/debug/memory",
        "mcp_debug": "/debug/mcp",
        "feedback": "/feedback",
        "translate": "/translate"
    }


@app.get("/health", tags=["Health"])
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    try:
        # Test database connection
        stats = translator.get_system_stats()
        return HealthResponse(
            status="healthy",
            models_loaded=True,
            database_connected=True
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            models_loaded=False,
            database_connected=False
        )


@app.post("/translate", response_model=TranslationResponse, tags=["Translation"])
async def translate(request: TranslationRequest) -> TranslationResponse:
    """Main translation endpoint"""
    try:
        logger.info(f"📥 Translation request: {request.text[:50]}... -> {request.target_language}")
        response = await translator.translate(request)
        logger.info(f"📤 Translation response: {response.translation}")
        return response
    except Exception as e:
        logger.error(f"❌ Translation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback", tags=["Feedback"])
async def submit_feedback(feedback: FeedbackRequest) -> Dict[str, str]:
    """Submit feedback for translations"""
    try:
        logger.info(f"💬 Feedback received: accepted={feedback.is_accepted}")
        
        # If accepted, add to translation memory
        if feedback.is_accepted:
            entry = TranslationMemoryEntry(
                source_text=feedback.source_text,
                target_text=feedback.target_text,
                target_language=feedback.target_language,
                confidence=feedback.confidence or 0.9
            )
            translator.rag_search.add_and_update_index(entry)
            logger.info("✅ Added to translation memory")
        
        return {"message": "Feedback received successfully"}
    except Exception as e:
        logger.error(f"❌ Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test", tags=["Testing"])
async def run_tests() -> Dict[str, Any]:
    """Run comprehensive system tests"""
    logger.info("🧪 Running system tests...")
    return await translator.test_components()


@app.get("/stats", tags=["System"])
async def get_stats() -> Dict[str, Any]:
    """Get system statistics"""
    return translator.get_system_stats()


@app.get("/debug/glossary", tags=["Debug"])
async def debug_glossary(text: str, target_language: str = "fr") -> Dict[str, Any]:
    """Debug glossary extraction"""
    try:
        result = translator.glossary_manager.extract_terms(text, target_language)
        return {
            "text": text,
            "target_language": target_language,
            "matches": [{"term": m.term, "translation": m.translation, "confidence": m.confidence} for m in result.matches],
            "terms_found": result.terms_found
        }
    except Exception as e:
        logger.error(f"❌ Glossary debug failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/memory", tags=["Debug"])
async def debug_memory(text: str, target_language: str = "fr") -> Dict[str, Any]:
    """Debug translation memory search"""
    try:
        result = translator.rag_search.search_similar(text, target_language)
        return {
            "text": text,
            "target_language": target_language,
            "matches": [{
                "source_text": m.source_text,
                "target_text": m.target_text,
                "similarity_score": m.similarity_score,
                "confidence": m.confidence
            } for m in result.matches],
            "total_matches": result.total_matches,
            "exact_matches": result.exact_matches,
            "semantic_matches": result.semantic_matches
        }
    except Exception as e:
        logger.error(f"❌ Memory debug failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/mcp", tags=["Debug"])
async def debug_mcp(text: str, target_language: str = "fr") -> Dict[str, Any]:
    """Debug MCP prompt construction"""
    try:
        # Simulate the MCP prompt building
        glossary_result = translator.glossary_manager.extract_terms(text, target_language)
        memory_result = translator.rag_search.search_similar(text, target_language)
        
        # Build prompt using internal method
        prompt_parts = []
        prompt_parts.append("You are a professional translator specializing in technical and business content.")
        prompt_parts.append(f"Translate the following text from en to {target_language}:")
        
        if glossary_result.matches:
            prompt_parts.append("\n=== GLOSSARY TERMS ===")
            for match in glossary_result.matches:
                prompt_parts.append(f"Term: {match.term}")
                prompt_parts.append(f"Translation: {match.translation}")
                if match.notes:
                    prompt_parts.append(f"Notes: {match.notes}")
                prompt_parts.append("")
        
        if memory_result.matches:
            prompt_parts.append("=== TRANSLATION MEMORY ===")
            for i, match in enumerate(memory_result.matches[:3], 1):
                prompt_parts.append(f"Example {i}:")
                prompt_parts.append(f"Source: {match.source_text}")
                prompt_parts.append(f"Translation: {match.target_text}")
                prompt_parts.append(f"Similarity: {match.similarity_score:.2f}")
                prompt_parts.append("")
        
        prompt_parts.append("=== INSTRUCTIONS ===")
        prompt_parts.append("1. Use the exact glossary terms provided above")
        prompt_parts.append("2. Follow the style and tone from the translation memory examples")
        prompt_parts.append("3. Maintain technical accuracy")
        prompt_parts.append("4. Provide only the translation, no additional text")
        prompt_parts.append(f"\n=== SOURCE TEXT ===")
        prompt_parts.append(text)
        prompt_parts.append("\n=== TRANSLATION ===")
        
        prompt = "\n".join(prompt_parts)
        
        return {
            "text": text,
            "target_language": target_language,
            "glossary_matches": len(glossary_result.matches),
            "memory_matches": len(memory_result.matches),
            "prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt,
            "prompt_length": len(prompt)
        }
    except Exception as e:
        logger.error(f"❌ MCP debug failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
