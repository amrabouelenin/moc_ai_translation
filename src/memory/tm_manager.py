import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import TranslationMemoryEntry, TranslationMatch, SearchResult
from ..core.config import settings


class TranslationMemoryManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_url.replace("sqlite:///", "")
        self._init_database()
    
    def _init_database(self):
        """Initialize the translation memory database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS translation_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_text TEXT NOT NULL,
                target_text TEXT NOT NULL,
                source_language TEXT NOT NULL DEFAULT 'en',
                target_language TEXT NOT NULL,
                domain TEXT,
                confidence REAL DEFAULT 1.0,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tm_source ON translation_memory(source_text);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tm_lang ON translation_memory(source_language, target_language);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tm_domain ON translation_memory(domain);
        ''')
        
        conn.commit()
        conn.close()
    
    def add_entry(self, entry: TranslationMemoryEntry) -> int:
        """Add a new translation memory entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata_json = json.dumps(entry.metadata) if entry.metadata else None
        
        cursor.execute('''
            INSERT INTO translation_memory 
            (source_text, target_text, source_language, target_language, domain, confidence, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.source_text,
            entry.target_text,
            entry.source_language,
            entry.target_language,
            entry.domain,
            entry.confidence,
            metadata_json
        ))
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return entry_id
    
    def search_exact(self, source_text: str, target_language: str, source_language: str = "en") -> List[TranslationMatch]:
        """Search for exact matches in translation memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT source_text, target_text, confidence, metadata
            FROM translation_memory
            WHERE source_text = ? AND target_language = ? AND source_language = ?
            ORDER BY confidence DESC
        ''', (source_text, target_language, source_language))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            TranslationMatch(
                source_text=row[0],
                target_text=row[1],
                similarity_score=1.0,
                confidence=row[2],
                metadata=json.loads(row[3]) if row[3] else None
            )
            for row in rows
        ]
    
    def get_all_entries(self, target_language: str = None) -> List[TranslationMemoryEntry]:
        """Get all translation memory entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if target_language:
            cursor.execute('''
                SELECT source_text, target_text, source_language, target_language, 
                       domain, confidence, metadata, created_at, updated_at
                FROM translation_memory
                WHERE target_language = ?
            ''', (target_language,))
        else:
            cursor.execute('''
                SELECT source_text, target_text, source_language, target_language, 
                       domain, confidence, metadata, created_at, updated_at
                FROM translation_memory
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            TranslationMemoryEntry(
                source_text=row[0],
                target_text=row[1],
                source_language=row[2],
                target_language=row[3],
                domain=row[4],
                confidence=row[5],
                metadata=json.loads(row[6]) if row[6] else None
            )
            for row in rows
        ]
    
    def load_initial_data(self):
        """Load initial translation memory data"""
        initial_data = [
            {
                "source_text": "The server is down",
                "target_text": "Le serveur est hors service",
                "target_language": "fr",
                "domain": "infrastructure",
                "confidence": 0.95
            },
            {
                "source_text": "Please restart the application",
                "target_text": "Veuillez redémarrer l'application",
                "target_language": "fr",
                "domain": "troubleshooting",
                "confidence": 0.9
            },
            {
                "source_text": "Database connection failed",
                "target_text": "La connexion à la base de données a échoué",
                "target_language": "fr",
                "domain": "database",
                "confidence": 0.98
            },
            {
                "source_text": "Authentication required",
                "target_text": "Authentification requise",
                "target_language": "fr",
                "domain": "security",
                "confidence": 0.92
            },
            {
                "source_text": "Invalid input format",
                "target_text": "Format d'entrée invalide",
                "target_language": "fr",
                "domain": "validation",
                "confidence": 0.88
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM translation_memory")
        if cursor.fetchone()[0] == 0:
            for entry in initial_data:
                cursor.execute('''
                    INSERT INTO translation_memory 
                    (source_text, target_text, target_language, domain, confidence)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    entry["source_text"],
                    entry["target_text"],
                    entry["target_language"],
                    entry["domain"],
                    entry["confidence"]
                ))
        
        conn.commit()
        conn.close()
