import numpy as np
import json
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import faiss
import os
from pathlib import Path
from .models import TranslationMatch, SearchResult, TranslationMemoryEntry
from .tm_manager import TranslationMemoryManager
from ..core.config import settings


class RAGSearch:
    def __init__(self, tm_manager: TranslationMemoryManager = None):
        self.tm_manager = tm_manager or TranslationMemoryManager()
        self.model = SentenceTransformer(settings.embedding_model)
        self.index = None
        self.texts = []
        self.embeddings = []
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create a new one"""
        index_path = Path(settings.vector_db_path)
        
        if index_path.exists():
            self.index = faiss.read_index(str(index_path))
            # Load corresponding texts
            texts_path = index_path.with_suffix('.json')
            if texts_path.exists():
                with open(texts_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.texts = data.get('texts', [])
                    self.embeddings = data.get('embeddings', [])
        else:
            self._create_index()
    
    def _create_index(self):
        """Create a new FAISS index from translation memory"""
        entries = self.tm_manager.get_all_entries()
        
        if not entries:
            # Load initial data if empty
            self.tm_manager.load_initial_data()
            entries = self.tm_manager.get_all_entries()
        
        if entries:
            self.texts = [entry.source_text for entry in entries]
            embeddings = self.model.encode(self.texts)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            self.index.add(embeddings.astype('float32'))
            
            # Save index and texts
            self._save_index()
    
    def _save_index(self):
        """Save FAISS index and metadata"""
        index_path = Path(settings.vector_db_path)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(self.index, str(index_path))
        
        # Save texts and embeddings
        texts_path = index_path.with_suffix('.json')
        with open(texts_path, 'w', encoding='utf-8') as f:
            json.dump({
                'texts': self.texts,
                'embeddings': [emb.tolist() for emb in self.embeddings]
            }, f, ensure_ascii=False, indent=2)
    
    def search_similar(
        self,
        query: str,
        target_language: str,
        source_language: str = "en",
        top_k: int = None
    ) -> SearchResult:
        """Search for semantically similar translations"""
        if not self.index or self.index.ntotal == 0:
            return SearchResult()
        
        top_k = top_k or settings.top_k_matches
        
        # Encode query
        query_embedding = self.model.encode([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        # Search FAISS index
        scores, indices = self.index.search(
            query_embedding.astype('float32'),
            min(top_k, self.index.ntotal)
        )
        
        matches = []
        exact_matches = 0
        semantic_matches = 0
        
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for invalid indices
                continue
            
            similarity_score = float(score)
            
            # Skip if below threshold
            if similarity_score < settings.similarity_threshold:
                continue
            
            source_text = self.texts[idx]
            
            # Get exact matches from TM
            exact_tm_matches = self.tm_manager.search_exact(
                source_text, target_language, source_language
            )
            
            if exact_tm_matches:
                for tm_match in exact_tm_matches:
                    matches.append(TranslationMatch(
                        source_text=tm_match.source_text,
                        target_text=tm_match.target_text,
                        similarity_score=similarity_score,
                        confidence=tm_match.confidence,
                        metadata=tm_match.metadata
                    ))
                    
                    if similarity_score == 1.0:
                        exact_matches += 1
                    else:
                        semantic_matches += 1
        print(f"Semantic matches found: {len(matches)}. Skipping LLM call.")
        return SearchResult(
            matches=matches,
            total_matches=len(matches),
            exact_matches=exact_matches,
            semantic_matches=semantic_matches
        )
    
    def add_and_update_index(self, entry: TranslationMemoryEntry):
        """Add new entry to TM and update FAISS index"""
        # Add to translation memory
        entry_id = self.tm_manager.add_entry(entry)
        
        # Update FAISS index
        if self.index is None:
            self._create_index()
        else:
            # Add new embedding
            new_embedding = self.model.encode([entry.source_text])
            new_embedding = new_embedding / np.linalg.norm(new_embedding, axis=1, keepdims=True)
            
            self.texts.append(entry.source_text)
            self.index.add(new_embedding.astype('float32'))
            
            # Save updated index
            self._save_index()
    
    def get_stats(self) -> dict:
        """Get RAG search statistics"""
        stats = {
            "total_entries": 0,
            "index_size": 0,
            "embedding_model": settings.embedding_model,
            "similarity_threshold": settings.similarity_threshold,
            "top_k_matches": settings.top_k_matches
        }
        
        if self.index:
            stats["index_size"] = self.index.ntotal
        
        entries = self.tm_manager.get_all_entries()
        stats["total_entries"] = len(entries)
        
        return stats
