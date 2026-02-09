import re
import json
import sqlite3
from typing import List, Optional, Dict
from pathlib import Path
from .models import GlossaryEntry, GlossaryMatch, GlossaryExtractionResult
from ..core.config import settings
from ..llm.client import LLMFactory
import json
import logging
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
                translation TEXT,
                target_language TEXT NOT NULL DEFAULT 'fr',
                notes TEXT,
                domain TEXT,
                occurrence_count INTEGER DEFAULT 0,
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
        
        # Check if translation column exists, add if not
        try:
            cursor.execute("SELECT translation FROM glossary LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE glossary ADD COLUMN translation TEXT")
            
        # Check if occurrence_count column exists, add if not
        try:
            cursor.execute("SELECT occurrence_count FROM glossary LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE glossary ADD COLUMN occurrence_count INTEGER DEFAULT 0")
            
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
            SELECT term, preferred_translation, target_language, notes, domain, created_at, updated_at, translation, occurrence_count
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
                domain=row[4],
                translation=row[1],       # Use only preferred_translation, ignoring translation column
                occurrence_count=row[8] or 0
            )
            for row in rows
        ]
    
    # Traditional pattern-matching extraction method removed in favor of LLM-based approach
        
    async def extract_terms(self, text: str, translation: str = None, target_language: str = "fr") -> GlossaryExtractionResult:
        """Extract glossary terms from input text using LLM
        
        Extract terms works during the build process and also during the translation process. 
        during the build process there is no translation available so the translation parameter is optional.
        
        Args:
            text: Source text to extract terms from
            translation: Optional translated text to help with term extraction
            target_language: Target language code (default: 'fr')    
        Returns:
            GlossaryExtractionResult with extracted terms and their translations
        """
        try:
            llm_client = LLMFactory.create_client()
        except Exception as e:
            import logging
            logging.warning("Could not initialize LLM for term extraction: %s", str(e))
            # Return empty result when LLM client is unavailable
            return GlossaryExtractionResult()

        try:
            json_response = await llm_client.extract_terms(
                text=text,
                translation=translation,
                target_language=target_language
            )
            
            # Parse JSON response with improved error handling
            try:
                # Clean up the response to ensure it's valid JSON
                json_text = json_response.strip()
                
                # Handle various markdown code block formats
                if json_text.startswith('```json'):
                    json_text = json_text[7:]
                elif json_text.startswith('```'):
                    json_text = json_text[3:]
                if json_text.endswith('```'):
                    json_text = json_text[:-3]
                
                # Remove any non-JSON text before the array start and after array end
                start_idx = json_text.find('[')
                if start_idx >= 0:
                    end_idx = json_text.rfind(']')
                    if end_idx > start_idx:
                        json_text = json_text[start_idx:end_idx+1]
                
                json_text = json_text.strip()
                
                # Log the cleaned JSON for debugging
                import logging
                logging.info("Cleaned JSON response: %s", json_text)
            
              
                # Handle empty array case
                if json_text == "[]" or not json_text:
                    return GlossaryExtractionResult()
                    
                # Try to parse the JSON
                terms_data = json.loads(json_text)
                
                # Create matches from LLM-extracted terms
                matches = []
                terms_found = []
                
                for item in terms_data:
                    term = item["term"].strip()
                    
                    # If translation was provided in the prompt, it should be in the response
                    if translation and "translation" in item:
                        translation_text = item["translation"].strip()
                    else:
                        # When no translation was provided, we won't have one in the response
                        translation_text = ""
                   
                    # Skip action phrases and verbs (typically start with these words)
                    skip_prefixes = ['add ', 'change ', 'modify ', 'delete ', 'remove ', 'select ', 'click ']
                    if any(term.lower().startswith(prefix) for prefix in skip_prefixes):
                        continue
                        
                    # Skip terms that are complete sentences or end with punctuation
                    if term.endswith(('.', '!', '?')):
                        continue
                        
                    # Limit terms to a maximum of 3 words
                    if len(term.split()) > 3:
                        # Extract the core part of the term - always take last 3 words as they're often most specific
                        term_parts = term.split()
                        term = " ".join(term_parts[-3:])
                        
                        import logging
                        logging.info(f"⚠️ Term too long, shortened to: '{term}' (3 words max)")
                        
                        
                    # Skip terms that are too short or too long after processing
                    if len(term.split()) > 3:
                        continue
                    
                    # Check if term exists in glossary
                    existing_entry = next((e for e in self.get_entries(target_language) 
                                         if e.term.lower() == term.lower()), None)
                    
                    if existing_entry:
                        # Use existing entry's data - only using preferred_translation
                        match = GlossaryMatch(
                            term=existing_entry.term,
                            prefered_translation=existing_entry.preferred_translation,
                            original_translation=translation_text,  # Not using translation column
                            notes=existing_entry.notes,
                            confidence=1.0
                        )
                        
                        # Add debug logging
                        import logging
                        logging.info(f"✓ ACTUAL GLOSSARY MATCH: Term '{existing_entry.term}' found in glossary -> '{existing_entry.preferred_translation}'") 
                    else:
                       
                        if translation_text:
                            # Use extracted data when we have a translation
                            match = GlossaryMatch(
                                term=term,
                                prefered_translation=translation_text, # Use as preferred translation
                                original_translation=translation_text,    # Not using original translation
                                notes="Extracted by LLM",
                                confidence=0.9
                            )
                            
                            # Add debug logging
                            import logging
                            logging.info(f"ℹ️ LLM EXTRACTED TERM: '{term}' -> '{translation_text}' (not in glossary yet)")
                            
                            # Auto-save this term to the glossary database
                            conn = sqlite3.connect(self.db_path)
                            cursor = conn.cursor()
                            try:
                                cursor.execute("""
                                    INSERT INTO glossary 
                                    (term, preferred_translation, target_language, notes, domain, occurrence_count) 
                                    VALUES (?, ?, ?, ?, ?, 1)
                                """, (
                                    term,
                                    translation_text,
                                    target_language,
                                    f"Auto-added from LLM extraction by translator.py (source text: {text[:30]}...)",
                                    None  # No domain information available
                                ))
                                conn.commit()
                                logging.info(f"✅ AUTO-ADDED TO GLOSSARY: Term '{term}' saved to glossary database")
                            except Exception as e:
                                logging.warning(f"⚠️ Failed to auto-add term to glossary: {e}")
                            finally:
                                conn.close()
                            
                        else:
                            # When we don't have a translation yet, just use the term
                            # Look for existing glossary entries for this term
                            entries = self.get_entries(target_language)
                            matching_entries = [e for e in entries if e.term.lower() == term.lower()]
                            
                            if matching_entries:
                                # Use existing glossary entry if available
                                entry = matching_entries[0]
                                match = GlossaryMatch(
                                    term=term,
                                    prefered_translation=entry.preferred_translation,
                                    original_translation=None,  # Not using translation column
                                    notes="Existing glossary match found by LLM",
                                    confidence=0.95
                                )
                                
                                # Add debug logging
                                import logging
                                logging.info(f"✓ ACTUAL GLOSSARY MATCH: LLM found term '{term}' in glossary -> '{entry.preferred_translation}'")
                                
                                
                            else:
                                # We found a term but have no translation yet
                                match = GlossaryMatch(
                                    term=term,
                                    prefered_translation="",  # No translation available yet
                                    original_translation=None,
                                    notes="Term identified by LLM, awaiting translation",
                                    confidence=0.7
                                )
                                
                                # Add debug logging
                                import logging
                                logging.info(f"ℹ️ LLM IDENTIFIED TERM: '{term}' (no translation available yet)")
                                
                    
                    matches.append(match)
                    terms_found.append(term)
                logging.info("Extracted matches: %s", matches)
                # No longer combining with pattern-based extraction - LLM is the only source of terms
                
                return GlossaryExtractionResult(matches=matches, terms_found=terms_found)
                
            except json.JSONDecodeError as e:
                import logging
                logging.warning(f"Failed to parse LLM response: {e} - {json_response}")
                # Return empty result set if JSON parsing fails
                return GlossaryExtractionResult()
                
        except Exception as e:
            import logging
            logging.error(f"Failed to extract terms using LLM: {e}")
            # Return empty result set if extraction fails completely
            return GlossaryExtractionResult()
    
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
