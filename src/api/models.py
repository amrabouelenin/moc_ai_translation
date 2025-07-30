from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    text: str = Field(..., description="Text to translate", min_length=1)
    target_language: str = Field(default="fr", description="Target language code (e.g., 'fr', 'es', 'de')")
    source_language: Optional[str] = Field(default="en", description="Source language code")
    domain: Optional[str] = Field(None, description="Domain context for translation")
    use_glossary: bool = Field(default=True, description="Whether to use glossary terms")
    use_memory: bool = Field(default=True, description="Whether to use translation memory")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class TranslationResponse(BaseModel):
    translation: str = Field(..., description="Translated text")
    source_text: str = Field(..., description="Original source text")
    target_language: str = Field(..., description="Target language code")
    glossary_matches: List[Dict[str, Any]] = Field(default_factory=list, description="Glossary terms used")
    memory_matches: List[Dict[str, Any]] = Field(default_factory=list, description="Translation memory matches")
    confidence: float = Field(default=1.0, description="Overall translation confidence")
    model_used: str = Field(..., description="LLM model used for translation")
    processing_time: float = Field(..., description="Processing time in seconds")


class FeedbackRequest(BaseModel):
    source_text: str = Field(..., description="Original source text")
    target_text: str = Field(..., description="Translated text")
    target_language: str = Field(..., description="Target language code")
    is_accepted: bool = Field(..., description="Whether the translation is accepted")
    feedback: Optional[str] = Field(None, description="Optional feedback text")
    confidence: Optional[float] = Field(None, description="User confidence rating")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    version: str = Field(default="1.0.0", description="API version")
    models_loaded: bool = Field(..., description="Whether models are loaded")
    database_connected: bool = Field(..., description="Whether database is connected")
