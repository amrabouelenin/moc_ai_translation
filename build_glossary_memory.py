#!/usr/bin/env python3
"""
Glossary and Translation Memory Builder

This script analyzes existing translations in CSV files to build:
1. A glossary of domain-specific terms with their translations
2. A translation memory database of sentence pairs

It uses LLM to extract terminology from sentences and stores the data in SQLite.
"""

import os
import csv
import sqlite3
import asyncio
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any
from datetime import datetime
import argparse

# Import existing components
from src.llm.client import LLMFactory
from src.glossary.manager import GlossaryManager
from src.memory.tm_manager import TranslationMemoryManager
from src.glossary.models import GlossaryEntry
from src.memory.models import TranslationMemoryEntry
from src.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/glossary_builder.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class GlossaryMemoryBuilder:
    """Builds glossaries and translation memory from existing translations"""

    def __init__(self, db_path: str = None):
        """Initialize the builder with database connection"""
        self.db_path = db_path or settings.database_url.replace("sqlite:///", "")
        
        # Create custom instances that don't load initial data
        self.glossary_manager = self._create_empty_glossary_manager(self.db_path)
        self.tm_manager = self._create_empty_tm_manager(self.db_path)
        
        # Initialize LLM client - required for glossary term extraction
        try:
            self.llm_client = LLMFactory.create_client()
            logger.info("✅ LLM client initialized successfully")
        except Exception as e:
            logger.error(f"❌ LLM client initialization failed: {e}")
            logger.error("❌ LLM is required for glossary term extraction. Exiting.")
            raise RuntimeError("LLM client initialization failed. Cannot continue without LLM for glossary extraction.")
            
        # Track processed items to avoid duplicates
        self.processed_glossary_terms = set()
        self.processed_translations = set()
    
    def _create_empty_glossary_manager(self, db_path: str) -> GlossaryManager:
        """Create a glossary manager without loading initial data"""
        # Create a custom glossary manager with an empty _load_initial_data method
        glossary_manager = GlossaryManager(db_path)
        
        # Override _load_initial_data method to do nothing
        def no_load(*args, **kwargs):
            logger.info("Skipping initial glossary data loading as requested")
            return
            
        glossary_manager._load_initial_data = no_load
        
        # Clear any existing initial glossary data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if there's any initial data (tech terms not from our translations)
        cursor.execute("""
            DELETE FROM glossary 
            WHERE domain = 'technology' 
            AND notes LIKE 'Infrastructure informatique%'
            AND occurrence_count = 0
        """)
        conn.commit()
        conn.close()
        
        # Initialize the database without loading data
        glossary_manager._init_database()
        
        return glossary_manager
    
    def _create_empty_tm_manager(self, db_path: str) -> TranslationMemoryManager:
        """Create a translation memory manager without loading initial data"""
        # Create a custom translation memory manager that skips loading initial data
        tm_manager = TranslationMemoryManager(db_path)
        
        # Override load_initial_data method to do nothing
        tm_manager.load_initial_data = lambda: None
        
        # Initialize the database without loading data
        tm_manager._init_database()
        
        return tm_manager

    async def extract_glossary_terms(self, text: str, translation: str, 
                                    target_language: str) -> List[Tuple[str, str]]:
        """
        Extract glossary terms from a text using LLM
        
        Args:
            text: Source text (English)
            translation: Translated text
            target_language: Target language code (e.g. 'fr', 'es')
            
        Returns:
            List of tuples containing (term, translation)
        """
        # LLM client should always be available due to our strict check in __init__
        # But we'll still check text/translation validity
        if not text or not translation:
            return []
            
        try:
            # Create a prompt for the LLM to extract glossary terms with stricter guidelines
            extraction_prompt = f"""
            Extract ONLY proper domain-specific technical terminology from these texts as JSON [{{'term': 'example', 'translation': 'exemple'}}].
            
            English: '{text}'  
            {target_language.upper()}: '{translation}'
            
            GUIDELINES FOR TERM EXTRACTION:
            1. Extract ONLY domain-specific technical nouns or noun phrases
            2. DO NOT include verbs, action phrases, or full instructions like "Add field" or "Change value"
            3. Focus on terminology that would appear in a technical glossary
            4. Return 1-3 most important technical terms, or empty array if none exist
            5. Each term should be a standalone technical concept
            
            Example good terms: "database", "flag table", "data element", "neural network"
            Example bad terms: "add field", "change value", "click button", "select option"
            
            Provide ONLY the JSON array with no other text.
            """
            
            # Use LLM to extract terms via the translate method, which all clients implement
            # We're not actually translating but using the LLM to process text
            json_response = await self.llm_client.translate(
                text=extraction_prompt,
                target_language="en",  # Using English as target since we want JSON output
                source_language="en"
            )
            
            # Parse JSON response
            try:
                # Clean up the response to ensure it's valid JSON
                json_text = json_response.strip()
                if json_text.startswith('```json'):
                    json_text = json_text[7:]
                if json_text.startswith('```'):
                    json_text = json_text[3:]
                if json_text.endswith('```'):
                    json_text = json_text[:-3]
                    
                json_text = json_text.strip()
                
                terms_data = json.loads(json_text)
                
                # Additional filter to ensure we only get proper terminology
                filtered_terms = []
                for item in terms_data:
                    term = item["term"].lower().strip()
                    
                    # Skip action phrases and verbs (typically start with these words)
                    skip_prefixes = ['add ', 'change ', 'modify ', 'delete ', 'remove ', 'select ', 'click ']
                    if any(term.startswith(prefix) for prefix in skip_prefixes):
                        continue
                        
                    # Skip terms that are complete sentences or end with punctuation
                    if term.endswith(('.', '!', '?')) or len(term.split()) > 5:
                        continue
                        
                    filtered_terms.append((item["term"], item["translation"]))
                
                return filtered_terms
                
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response: {json_response}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to extract glossary terms: {e}")
            return []

    async def select_preferred_translation(self, term: str, existing_translation: str, 
                                      new_translation: str, target_language: str) -> str:
        """
        Use LLM to determine which translation should be the preferred one
        
        Args:
            term: Source term (English)
            existing_translation: Existing translation in the glossary
            new_translation: New translation being proposed
            target_language: Target language code
            
        Returns:
            The translation that should be preferred
        """
        # Create a prompt for the LLM
        selection_prompt = f"""
        You are a professional translator helping to build a technical glossary.
        For the English term "{term}", there are two different translations in {target_language}:
        
        1. "{existing_translation}" 
        2. "{new_translation}"
        
        Which translation is more accurate and appropriate for a technical glossary?
        Consider:
        - Technical accuracy and precision
        - Common usage in the domain
        - Clarity and appropriateness
        
        Reply with ONLY the better translation, without quotes or explanations.
        """
        
        try:
            # Use LLM to select the preferred translation
            response = await self.llm_client.translate(
                text=selection_prompt,
                target_language="en",  # Using English as we just want the raw selection
                source_language="en"
            )
            
            # Clean response
            preferred = response.strip()
            
            # If the response is ambiguous, default to the existing translation
            if preferred not in [existing_translation, new_translation]:
                logger.warning(f"LLM did not select one of the provided translations. Defaulting to existing.")
                return existing_translation
            
            logger.info(f"LLM selected preferred translation for '{term}': {preferred}")
            return preferred
            
        except Exception as e:
            logger.error(f"Error selecting preferred translation: {e}")
            # Default to existing translation in case of error
            return existing_translation

    # No normalization function needed - we'll use exact term matching
        
    async def add_to_glossary(self, term: str, translation: str, 
                       target_language: str, domain: str = None) -> bool:
        """
        Add a term to the glossary with occurrence tracking
        
        Args:
            term: Source term (English)
            translation: Term translation
            target_language: Target language code
            domain: Optional domain category
            
        Returns:
            True if added or updated, False otherwise
        """
        # Skip empty terms or translations
        if not term or not translation:
            return False
            
        # Keep original term as is (no normalization)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for exact match first (term, translation, language)
        cursor.execute("""
            SELECT id, occurrence_count FROM glossary 
            WHERE term = ? AND translation = ? AND target_language = ?
        """, (term, translation, target_language))
        
        exact_match = cursor.fetchone()
        
        if exact_match:
            # Same term and translation exists, just update occurrence count
            term_id, count = exact_match
            cursor.execute("""
                UPDATE glossary 
                SET occurrence_count = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (count + 1, term_id))
            conn.commit()
            conn.close()
            logger.debug(f"Updated glossary term: {term} -> {translation} (occurrences: {count + 1})")
            return True
            
        # Check if the term exists but with a different translation
        cursor.execute("""
            SELECT id, preferred_translation, translation, occurrence_count, notes 
            FROM glossary 
            WHERE term = ? AND target_language = ?
        """, (term, target_language))
        
        term_match = cursor.fetchone()
        
        if term_match:
            # Term exists with different translation, use LLM to decide preferred
            conn.close()  # Close connection before async call
            term_id, existing_preferred, existing_translation, count, notes = term_match
            
            # Use LLM to determine which translation should be preferred
            preferred = await self.select_preferred_translation(
                term, existing_preferred, translation, target_language
            )
            
            # Build notes about the decision
            if preferred == translation:
                decision_note = f"LLM preferred '{translation}' over '{existing_translation}'" 
            else:
                decision_note = f"LLM preferred '{existing_translation}' over '{translation}'"
                
            updated_notes = f"{notes}\n{decision_note}" if notes else decision_note
            
            # Reopen connection after async operation
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store both translations - preferred in preferred_translation, and new translation in translation
            cursor.execute("""
                UPDATE glossary 
                SET occurrence_count = ?, translation = ?, 
                    preferred_translation = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (count + 1, translation, preferred, updated_notes, term_id))
            
            conn.commit()
            conn.close()
            logger.info(f"Updated glossary term with new translation: {term} -> {translation}, preferred: {preferred}")
            return True
        else:
            # New term, add to glossary
            try:
                # For new terms, translation and preferred_translation are the same
                cursor.execute("""
                    INSERT INTO glossary 
                    (term, preferred_translation, translation, target_language, notes, domain, occurrence_count) 
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (
                    term,              # Store original term exactly as it appears
                    translation,       # Initially the same as translation
                    translation,
                    target_language,
                    "Auto-extracted from existing translations",
                    domain
                ))
                
                term_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                logger.debug(f"Added new glossary term: {term} -> {translation}")
                
                # Add to processed set to avoid duplicates
                self.processed_glossary_terms.add((term, target_language))
                return True
                
            except Exception as e:
                logger.error(f"Failed to add glossary term: {e}")
                conn.close()
                return False

    def add_to_translation_memory(self, source_text: str, target_text: str,
                               source_language: str, target_language: str, 
                               domain: str = None) -> bool:
        """
        Add a translation to the memory with occurrence tracking
        
        Args:
            source_text: Source text
            target_text: Translated text
            source_language: Source language code
            target_language: Target language code
            domain: Optional domain category
            
        Returns:
            True if added or updated, False otherwise
        """
        # Skip empty texts
        if not source_text or not target_text:
            return False
            
        # Check if translation already exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, occurrence_count FROM translation_memory 
            WHERE source_text = ? AND target_text = ? 
            AND source_language = ? AND target_language = ?
        """, (source_text, target_text, source_language, target_language))
        
        result = cursor.fetchone()
        
        if result:
            # Translation exists, update occurrence count
            translation_id, count = result
            cursor.execute("""
                UPDATE translation_memory 
                SET occurrence_count = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (count + 1, translation_id))
            conn.commit()
            conn.close()
            logger.debug(f"Updated translation memory: {source_text} -> {target_text} (occurrences: {count + 1})")
            return True
        else:
            # New translation, add to memory
            try:
                metadata = json.dumps({
                    "source": "auto_extracted",
                    "extraction_date": datetime.now().isoformat()
                })
                
                # Insert with occurrence_count = 1
                cursor.execute("""
                    INSERT INTO translation_memory 
                    (source_text, target_text, source_language, target_language, 
                     domain, confidence, metadata, occurrence_count) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    source_text,
                    target_text,
                    source_language,
                    target_language,
                    domain,
                    0.9,  # High confidence since these are existing translations
                    metadata
                ))
                
                translation_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                logger.debug(f"Added new translation: {source_text} -> {target_text}")
                
                # Add to processed set to avoid duplicates
                self.processed_translations.add((source_text, target_language))
                return True
            except Exception as e:
                logger.error(f"Failed to add translation: {e}")
                conn.close()
                return False

    async def process_csv_file_pair(self, 
                               source_file: Path, 
                               target_file: Path,
                               source_language: str,
                               target_language: str,
                               domain: str = None) -> Dict[str, int]:
        """
        Process a pair of CSV files for translation memory and glossary extraction
        
        Args:
            source_file: Path to source CSV file (English)
            target_file: Path to target CSV file (translated)
            source_language: Source language code
            target_language: Target language code
            domain: Optional domain category
            
        Returns:
            Dictionary with statistics
        """
        logger.info(f"Processing file pair: {source_file.name} and {target_file.name}")
        
        # Statistics
        stats = {
            "glossary_terms_added": 0,
            "translations_added": 0,
            "rows_processed": 0,
            "rows_matched": 0,
            "errors": 0
        }
        
        try:
            # Load source and target CSVs
            source_df = pd.read_csv(source_file, encoding='utf-8')
            target_df = pd.read_csv(target_file, encoding='utf-8')
            
            # Detect ID column for matching rows
            id_columns = ['Id', 'CodeFigure']
            id_column = None
            
            for col in id_columns:
                if col in source_df.columns and col in target_df.columns:
                    id_column = col
                    break
            
            if not id_column:
                logger.warning(f"⚠️ Could not find matching ID column in {source_file.name} and {target_file.name}")
                return stats
            
            # Find translatable columns (those ending with _en in source file)
            translatable_columns = []
            for col in source_df.columns:
                if col.endswith('_en') or col == 'Meaning':
                    # Get corresponding target column name
                    if col.endswith('_en'):
                        target_col = col.replace('_en', f'_{target_language[:2].lower()}')
                    else:
                        # Handle 'Meaning' column
                        target_col = f"Meaning_{target_language[:2].lower()}"
                    
                    if target_col in target_df.columns:
                        translatable_columns.append((col, target_col))
            
            if not translatable_columns:
                logger.warning(f"⚠️ No translatable columns found in {source_file.name} and {target_file.name}")
                return stats
                
            logger.info(f"Found {len(translatable_columns)} translatable column pairs")
            
            # Process each row and extract translations
            for _, source_row in source_df.iterrows():
                if id_column not in source_row:
                    continue
                    
                row_id = source_row[id_column]
                
                # Find corresponding row in target file
                target_row = target_df[target_df[id_column] == row_id]
                if target_row.empty:
                    continue
                    
                target_row = target_row.iloc[0]
                stats["rows_matched"] += 1
                
                # Process each translatable column
                for src_col, tgt_col in translatable_columns:
                    if pd.isna(source_row[src_col]) or pd.isna(target_row[tgt_col]):
                        continue
                        
                    source_text = str(source_row[src_col]).strip()
                    target_text = str(target_row[tgt_col]).strip()
                    
                    if not source_text or not target_text:
                        continue
                    
                    # Add to translation memory
                    tm_added = self.add_to_translation_memory(
                        source_text=source_text,
                        target_text=target_text,
                        source_language=source_language,
                        target_language=target_language,
                        domain=domain
                    )
                    
                    if tm_added:
                        stats["translations_added"] += 1
                    
                    # Extract glossary terms using LLM
                    glossary_terms = await self.extract_glossary_terms(
                        text=source_text,
                        translation=target_text,
                        target_language=target_language
                    )
                    
                    # Add extracted terms to glossary
                    for term, translation in glossary_terms:
                        glossary_added = await self.add_to_glossary(
                            term=term,
                            translation=translation,
                            target_language=target_language,
                            domain=domain
                        )
                        
                        if glossary_added:
                            stats["glossary_terms_added"] += 1
                            logger.info(f"Added glossary term: '{term}' -> '{translation}'")
                
                stats["rows_processed"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"⚠️ Error processing file pair: {e}")
            stats['errors'] += 1
            return stats

    async def build_from_directory(self, 
                             english_dir: Path, 
                             translations_dir: Path,
                             target_language: str,
                             pattern: str = "*.csv",
                             domain: str = None) -> Dict[str, int]:
        """
        Process all matching CSV files in directories to build glossary and translation memory
        
        Args:
            english_dir: Directory containing English CSV files
            translations_dir: Directory containing translated CSV files
            target_language: Target language code
            pattern: File pattern (default: "*.csv")
            domain: Optional domain category
            
        Returns:
            Dictionary with counts of added items
        """
        logger.info(f"Processing directories:\n - EN: {english_dir}\n - {target_language.upper()}: {translations_dir}")
        
        total_stats = {
            "glossary_terms_added": 0,
            "translations_added": 0,
            "files_processed": 0,
            "rows_processed": 0,
            "rows_matched": 0,
            "errors": 0
        }
        
        # Get all English CSV files
        english_files = list(Path(english_dir).glob(pattern))
        
        if not english_files:
            logger.warning(f"No CSV files found in English directory: {english_dir}")
            return total_stats
        
        for en_file in english_files:
            # Construct expected translation filename
            if target_language == 'fr':
                tr_file_name = en_file.name.replace('_en', '_fr').replace('en_', 'fr_')
            elif target_language == 'es':  
                tr_file_name = en_file.name.replace('_en', '_es').replace('en_', 'es_')
            elif target_language == 'ru':
                tr_file_name = en_file.name.replace('_en', '_ru').replace('en_', 'ru_')
            else:
                tr_file_name = en_file.name.replace('_en', f'_{target_language}').replace('en_', f'{target_language}_')
                
            tr_file_path = Path(translations_dir) / tr_file_name
            
            # Check if translation file exists
            if not tr_file_path.exists():
                logger.warning(f"No translation file found: {tr_file_path}")
                continue
                
            # Process file pair
            stats = await self.process_csv_file_pair(
                source_file=en_file, 
                target_file=tr_file_path, 
                source_language="en",
                target_language=target_language,
                domain=domain
            )
            
            # Update total stats
            for key, value in stats.items():
                if key in total_stats:
                    total_stats[key] += value
                    
            total_stats["files_processed"] += 1
            
            logger.info(f"Processed {en_file.name} -> {tr_file_name}: "
                      f"{stats.get('glossary_terms_added', 0)} terms, {stats.get('translations_added', 0)} translations")
            
        return total_stats

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about glossary and translation memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            "total_glossary_entries": 0,
            "total_translation_entries": 0,
            "languages": []
        }
        
        # Count glossary entries
        cursor.execute("SELECT COUNT(*) FROM glossary")
        stats["total_glossary_entries"] = cursor.fetchone()[0]
        
        # Count translation memory entries
        cursor.execute("SELECT COUNT(*) FROM translation_memory")
        stats["total_translation_entries"] = cursor.fetchone()[0]
        
        # Get available languages
        cursor.execute(
            "SELECT DISTINCT target_language FROM glossary UNION SELECT DISTINCT target_language FROM translation_memory"
        )
        stats["languages"] = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return stats


async def main():
    """Main entry point for the glossary and memory builder"""
    parser = argparse.ArgumentParser(
        description="Build glossary and translation memory from existing translations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process French translations in BUFR4
  python build_glossary_memory.py --source-dir repos/BUFR4 --translations-dir repos/BUFR4/french --lang fr
  
  # Process Spanish translations with domain info
  python build_glossary_memory.py --source-dir repos/BUFR4 --translations-dir repos/BUFR4/spanish --lang es --domain meteorology
  
  # Process Russian translations
  python build_glossary_memory.py --source-dir repos/BUFR4 --translations-dir repos/BUFR4/russian --lang ru
        """
    )
    
    parser.add_argument(
        '--source-dir',
        type=Path,
        required=True,
        help='Directory containing source (English) CSV files'
    )
    parser.add_argument(
        '--translations-dir',
        type=Path,
        required=True,
        help='Directory containing translated CSV files'
    )
    parser.add_argument(
        '--lang',
        type=str,
        required=True,
        help='Target language code (e.g., fr, es, ru)'
    )
    parser.add_argument(
        '--domain',
        type=str,
        default=None,
        help='Domain category for the translations'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default="*.csv",
        help='File pattern for CSV files (default: *.csv)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if directories exist
    if not args.source_dir.exists():
        logger.error(f"Source directory not found: {args.source_dir}")
        return
        
    if not args.translations_dir.exists():
        logger.error(f"Translations directory not found: {args.translations_dir}")
        return
    
    # Initialize builder
    builder = GlossaryMemoryBuilder()
    
    # Print initial stats
    initial_stats = builder.get_stats()
    logger.info("Initial database stats:")
    logger.info(f"  - Glossary entries: {initial_stats['total_glossary_entries']}")
    logger.info(f"  - Translation entries: {initial_stats['total_translation_entries']}")
    logger.info(f"  - Languages: {', '.join(initial_stats['languages'])}")
    
    # Process directories
    logger.info(f"Starting build process for language: {args.lang}")
    stats = await builder.build_from_directory(
        args.source_dir,
        args.translations_dir,
        args.lang,
        args.pattern,
        args.domain
    )
    
    # Print results
    logger.info("\n=== Build Results ===")
    logger.info(f"Files processed: {stats['files_processed']}")
    logger.info(f"Rows processed: {stats['rows_processed']}")
    logger.info(f"Rows matched: {stats['rows_matched']}")
    logger.info(f"Glossary terms added: {stats['glossary_terms_added']}")
    logger.info(f"Translations added: {stats['translations_added']}")
    logger.info(f"Errors: {stats['errors']}")
    
    # Print final stats
    final_stats = builder.get_stats()
    logger.info("\n=== Final Database Stats ===")
    logger.info(f"Glossary entries: {final_stats['total_glossary_entries']}")
    logger.info(f"Translation entries: {final_stats['total_translation_entries']}")
    logger.info(f"Languages: {', '.join(final_stats['languages'])}")


if __name__ == "__main__":
    asyncio.run(main())
