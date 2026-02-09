from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class GlossaryEntry(BaseModel):
    term: str = Field(..., description="Original term in source language")
    preferred_translation: str = Field(..., description="Preferred translation in target language")
    target_language: str = Field(default="fr", description="Target language code")
    translation: Optional[str] = Field(None, description="Original translation before any preference selection")
    notes: Optional[str] = Field(None, description="Additional context or usage notes")
    domain: Optional[str] = Field(None, description="Domain or category of the term")
    occurrence_count: int = Field(0, description="Number of times this term has been seen")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GlossaryMatch(BaseModel):
    term: str
    original_translation: Optional[str] = Field(None, description="Original translation in target language")
    prefered_translation: str = Field(..., description="Preferred translation in target language")
    notes: Optional[str] = Field(None, description="Additional context or usage notes")
    confidence: float = Field(1.0, description="Confidence level of the match")


class GlossaryExtractionResult(BaseModel):
    matches: List[GlossaryMatch] = Field(default_factory=list)
    terms_found: List[str] = Field(default_factory=list)
