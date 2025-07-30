from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class GlossaryEntry(BaseModel):
    term: str = Field(..., description="Original term in source language")
    preferred_translation: str = Field(..., description="Preferred translation in target language")
    target_language: str = Field(default="fr", description="Target language code")
    notes: Optional[str] = Field(None, description="Additional context or usage notes")
    domain: Optional[str] = Field(None, description="Domain or category of the term")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GlossaryMatch(BaseModel):
    term: str
    translation: str
    notes: Optional[str] = None
    confidence: float = 1.0


class GlossaryExtractionResult(BaseModel):
    matches: List[GlossaryMatch] = Field(default_factory=list)
    terms_found: List[str] = Field(default_factory=list)
