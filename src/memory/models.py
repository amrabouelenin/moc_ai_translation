from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TranslationMemoryEntry(BaseModel):
    source_text: str = Field(..., description="Original source text")
    target_text: str = Field(..., description="Translated target text")
    source_language: str = Field(default="en", description="Source language code")
    target_language: str = Field(..., description="Target language code")
    domain: Optional[str] = Field(None, description="Domain or context")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Translation confidence score")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TranslationMatch(BaseModel):
    source_text: str
    target_text: str
    similarity_score: float
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    matches: list[TranslationMatch] = Field(default_factory=list)
    total_matches: int = 0
    exact_matches: int = 0
    semantic_matches: int = 0
