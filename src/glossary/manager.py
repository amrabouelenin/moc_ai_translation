import re
import json
import sqlite3
from typing import List, Optional, Dict
from pathlib import Path
from .models import GlossaryEntry, GlossaryMatch, GlossaryExtractionResult
from ..core.config import settings


class GlossaryManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_url.replace("sqlite:///", "")
        self._init_database()
        self._load_initial_data()
    
    def _init_database(self):
        """Initialize the glossary database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS glossary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL,
                preferred_translation TEXT NOT NULL,
                target_language TEXT NOT NULL DEFAULT 'fr',
                notes TEXT,
                domain TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_glossary_term ON glossary(term);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_glossary_lang ON glossary(target_language);
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_initial_data(self):
        """Load initial glossary data"""
        initial_data = [
            {"term": "cloud server", "preferred_translation": "serveur cloud", "notes": "Infrastructure informatique"},
            {"term": "API", "preferred_translation": "API", "notes": "Interface de programmation d'applications"},
            {"term": "database", "preferred_translation": "base de données", "notes": "Système de gestion de données"},
            {"term": "machine learning", "preferred_translation": "apprentissage automatique", "notes": "IA et data science"},
            {"term": "neural network", "preferred_translation": "réseau de neurones", "notes": "Architecture d'IA"},
            {"term": "algorithm", "preferred_translation": "algorithme", "notes": "Méthode de calcul"},
            {"term": "framework", "preferred_translation": "framework", "notes": "Structure de développement"},
            {"term": "deployment", "preferred_translation": "déploiement", "notes": "Mise en production"},
            {"term": "debugging", "preferred_translation": "débogage", "notes": "Processus de correction"},
            {"term": "authentication", "preferred_translation": "authentification", "notes": "Sécurité et accès"},
            {"term": "authorization", "preferred_translation": "autorisation", "notes": "Contrôle d'accès"},
            {"term": "cache", "preferred_translation": "cache", "notes": "Mémoire temporaire"},
            {"term": "endpoint", "preferred_translation": "point de terminaison", "notes": "API endpoint"},
            {"term": "middleware", "preferred_translation": "middleware", "notes": "Logiciel intermédiaire"},
            {"term": "microservice", "preferred_translation": "microservice", "notes": "Architecture logicielle"}
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM glossary")
        if cursor.fetchone()[0] == 0:
            for entry in initial_data:
                cursor.execute('''
                    INSERT INTO glossary (term, preferred_translation, notes, domain)
                    VALUES (?, ?, ?, ?)
                ''', (entry["term"], entry["preferred_translation"], entry["notes"], "technology"))
        
        conn.commit()
        conn.close()
    
    def add_entry(self, entry: GlossaryEntry) -> int:
        """Add a new glossary entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO glossary (term, preferred_translation, target_language, notes, domain)
            VALUES (?, ?, ?, ?, ?)
        ''', (entry.term, entry.preferred_translation, entry.target_language, entry.notes, entry.domain))
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return entry_id
    
    def get_entries(self, target_language: str = "fr") -> List[GlossaryEntry]:
        """Get all glossary entries for a target language"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT term, preferred_translation, target_language, notes, domain, created_at, updated_at
            FROM glossary
            WHERE target_language = ?
        ''', (target_language,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            GlossaryEntry(
                term=row[0],
                preferred_translation=row[1],
                target_language=row[2],
                notes=row[3],
                domain=row[4]
            )
            for row in rows
        ]
    
    def extract_terms(self, text: str, target_language: str = "fr") -> GlossaryExtractionResult:
        """Extract glossary terms from input text"""
        entries = self.get_entries(target_language)
        matches = []
        terms_found = []
        
        text_lower = text.lower()
        print(f"Extracting terms from text: {text_lower}")
        for entry in entries:
            term_lower = entry.term.lower()
            
            # Exact match
            if term_lower in text_lower:
                match = GlossaryMatch(
                    term=entry.term,
                    translation=entry.preferred_translation,
                    notes=entry.notes,
                    confidence=1.0
                )
                matches.append(match)
                terms_found.append(entry.term)
                continue
            
            # Simple substring matching for partial terms
            if any(term_lower in word.lower() for word in text.split()):
                match = GlossaryMatch(
                    term=entry.term,
                    translation=entry.preferred_translation,
                    notes=entry.notes,
                    confidence=0.8
                )
                matches.append(match)
                terms_found.append(entry.term)
        
        return GlossaryExtractionResult(matches=matches, terms_found=terms_found)
    
    def import_from_csv(self, csv_path: str, target_language: str = "fr") -> int:
        """Import glossary entries from CSV file"""
        import csv
        
        count = 0
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                entry = GlossaryEntry(
                    term=row['term'],
                    preferred_translation=row['preferred_translation'],
                    target_language=target_language,
                    notes=row.get('notes'),
                    domain=row.get('domain')
                )
                self.add_entry(entry)
                count += 1
        
        return count
