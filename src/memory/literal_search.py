import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .models import TranslationMatch, SearchResult
import json
logger = logging.getLogger(__name__)


class LiteralDictionarySearch:
    """
    Literal exact-match dictionary for translation lookup.
    Builds dictionary from existing translated CSV files on-the-fly.
    Key: English source text (normalized)
    Value: Translation from corresponding filename/row/cell
    """
    
    def __init__(self):
        self.dictionary = {}  # {(filename, source_text, target_lang): target_text}
        self.metadata = {}    # {(filename, source_text, target_lang): {file, row, cell}}
        self.current_source_file = None  # Track the file being translated
        
        # New global dictionary with occurrence counting
        self.global_dictionary = {}  # {(source_text.lower(), source_lang, target_lang): [target_text, occurrence_count]}
        
    def build_from_single_file(
        self,
        source_file: Path,
        target_language: str
    ) -> int:
        """
        Build dictionary from a single source-target file pair.
        
        Args:
            source_file: Path to source CSV file
            target_language: Target language to build dictionary for
            
        Returns:
            Number of entries added to dictionary
        """
        self.dictionary.clear()
        self.metadata.clear()
        
        # Find corresponding translated file
        translated_file = self._find_translated_file(source_file, target_language)
        
        if not translated_file or not translated_file.exists():
            logger.warning(f"⚠️ No translated file found for {source_file.name}")
            return 0
        
        # Read both files and build dictionary
        self._extract_translations(source_file, translated_file, target_language)
        
        logger.info(f"📖 Built literal dictionary: {len(self.dictionary)} entries for {target_language}")
        # Save dictionary to JSON for debugging
        dict_for_json = {f"{k[0]}|||{k[1]}|||{k[2]}": v for k, v in self.dictionary.items()}
        with open("literal_dictionary_debug.json", "w", encoding='utf-8') as f:
            json.dump(dict_for_json, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Dictionary saved to literal_dictionary_debug.json")
        return len(self.dictionary)
    
    def build_from_csv_files(
        self, 
        source_dir: Path, 
        target_language: str,
        pattern: str = "*_en*.csv",
        source_language: str = "en"
    ) -> int:
        """
        Build global dictionary from existing translated CSV files in target language directory.
        
        Args:
            source_dir: Directory containing source CSV files
            target_language: Target language to build dictionary for
            pattern: Pattern to match source files (default: "*_en*.csv")
            source_language: Source language code (default: "en")
            
        Returns:
            Number of unique entries added to global dictionary
        """
        # Clear global dictionary for fresh build
        self.global_dictionary.clear()
        
        # Map language codes to directory names
        lang_dir_map = {
            'fr': 'french',
            'es': 'spanish', 
            'ru': 'russian'
        }
        
        # Find target language directory, respecting 'english' ancestry
        lang_dir_name = lang_dir_map.get(target_language, target_language)
        source_parts = source_dir.parts
        if 'english' in source_parts:
            idx = list(source_parts).index('english')
            repo_root = Path(*source_parts[:idx])
            sub_parts = source_parts[idx + 1:]
            target_dir = repo_root / lang_dir_name
            if sub_parts:
                target_dir = target_dir.joinpath(*sub_parts)
        else:
            target_dir = source_dir / lang_dir_name
            if not target_dir.exists():
                target_dir = source_dir.parent / lang_dir_name

        if not target_dir.exists():
            logger.warning(f"⚠️ Target language directory not found: {target_dir}")
            return 0
            
        # Find all target language CSV files
        target_files = list(target_dir.glob(f"*_{target_language}*.csv"))
        logger.info(f"🔍 Found {len(target_files)} {target_language} files to process")
        
        total_pairs_processed = 0
        
        for target_file in target_files:
            # Find corresponding source file
            source_file = self._find_source_file_for_target(target_file, source_language, source_dir)
            
            if not source_file or not source_file.exists():
                logger.debug(f"⚠️ No source file found for {target_file.name}")
                continue
                
            # Extract translations and add to global dictionary
            pairs_count = self._extract_to_global_dictionary(source_file, target_file, source_language, target_language)
            total_pairs_processed += pairs_count
            
        logger.info(f"📖 Built global dictionary: {len(self.global_dictionary)} unique entries for {source_language}->{target_language}")
        logger.info(f"📊 Processed {total_pairs_processed} translation pairs from {len(target_files)} files")
        
        # Save global dictionary to JSON for debugging
        global_dict_for_json = {f"{k[0]}|||{k[1]}|||{k[2]}": {"translation": v[0], "count": v[1]} for k, v in self.global_dictionary.items()}
        with open("global_dictionary_debug.json", "w", encoding='utf-8') as f:
            json.dump(global_dict_for_json, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Global dictionary saved to global_dictionary_debug.json")
        
        return len(self.global_dictionary)
    
    def _find_translated_file(self, source_file: Path, target_language: str) -> Optional[Path]:
        """Find the corresponding translated file for a source file"""
        # Map language codes to directory names
        lang_dir_map = {
            'fr': 'french',
            'es': 'spanish',
            'ru': 'russian'
        }
        
        # Check in language subdirectory, respecting 'english' ancestry
        lang_dir_name = lang_dir_map.get(target_language, target_language)
        source_parts = source_file.parent.parts
        if 'english' in source_parts:
            idx = list(source_parts).index('english')
            repo_root = Path(*source_parts[:idx])
            sub_parts = source_parts[idx + 1:]
            lang_dir = repo_root / lang_dir_name
            if sub_parts:
                lang_dir = lang_dir.joinpath(*sub_parts)
        else:
            lang_dir = source_file.parent / lang_dir_name
            if not lang_dir.exists():
                lang_dir = source_file.parent.parent / lang_dir_name
        translated_name = source_file.name.replace('_en', f'_{target_language}')
        translated_path = lang_dir / translated_name
        
        return translated_path if translated_path.exists() else None
    
    def _find_source_file_for_target(self, target_file: Path, source_language: str, source_dir: Path) -> Optional[Path]:
        """Find the corresponding source file for a target file"""
        # Map language codes to directory names
        lang_dir_map = {
            'en': '',
            'fr': 'french',
            'es': 'spanish',
            'ru': 'russian'
        }
        
        # Extract target language from filename by finding the pattern _XX_ where XX is language code
        stem_parts = target_file.stem.split('_')
        target_lang_from_file = None
        
        # Find the language code in the filename parts
        for part in stem_parts:
            if part in ['en', 'es', 'fr', 'ru'] and len(part) == 2:
                target_lang_from_file = part
                break
        
        if not target_lang_from_file:
            logger.warning(f"Could not extract language code from {target_file.name}")
            return None
        
        # Generate source file name by replacing target language with source language
        source_name = target_file.name.replace(f'_{target_lang_from_file}', f'_{source_language}')
        
        # Look in source directory (or parent for English files)
        if source_language == 'en':
            source_path = source_dir / source_name
        else:
            source_dir_name = lang_dir_map.get(source_language, source_language)
            source_path = source_dir / source_dir_name / source_name
        
        return source_path if source_path.exists() else None
        
    def _extract_translations(
        self, 
        source_file: Path, 
        translated_file: Path, 
        target_language: str
    ):
        """Extract source-target pairs from aligned CSV files"""
        try:
            # Read source file
            with open(source_file, 'r', encoding='utf-8') as f:
                source_reader = csv.DictReader(f)
                source_headers = source_reader.fieldnames or []
                source_rows = list(source_reader)
            
            # Read translated file (with BOM handling)
            with open(translated_file, 'r', encoding='utf-8-sig') as f:
                translated_reader = csv.DictReader(f)
                translated_headers = translated_reader.fieldnames or []
                translated_rows = list(translated_reader)
            
            # Find column pairs (_en -> _target_lang)
            column_pairs = self._find_column_pairs(source_headers, translated_headers, target_language)
            
            # Build a lookup dictionary for translated rows by ID
            id_column = None
            for candidate in ('Id', 'ID', 'id', 'CodeFigure'):
                if candidate in source_headers and candidate in translated_headers:
                    id_column = candidate
                    break
            
            if not id_column:
                logger.warning(f"⚠️ No ID column ('Id'/'ID' or 'CodeFigure') found in {source_file.name}, skipping")
                return

            # Create lookup: {id_value: translated_row}
            translated_lookup = {}
            for translated_row in translated_rows:
                row_id = translated_row.get(id_column)
                if row_id:
                    translated_lookup[row_id] = translated_row

            # Extract translations by matching IDs
            for row_idx, source_row in enumerate(source_rows):
                row_id = source_row.get(id_column)
                
                if not row_id or row_id not in translated_lookup:
                    continue
                
                translated_row = translated_lookup[row_id]
                
                for source_col, target_col in column_pairs:
                    source_text = source_row.get(source_col, "").strip()
                    target_text = translated_row.get(target_col, "").strip()
                    
                    if source_text and target_text:
                        # Normalize key (case-insensitive) and include filename
                        key = (source_file.name, source_text.lower(), target_language)
                        
                        # Store translation
                        self.dictionary[key] = target_text
                        
                        # Store metadata
                        self.metadata[key] = {
                            'filename': source_file.name,
                            'row_id': row_id,
                            'row': row_idx + 2,  # +2 for header and 1-indexed
                            'cell': target_col
                        }
            
            logger.debug(f"✅ Extracted from {source_file.name}: {len(column_pairs)} column pairs")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract from {source_file.name}: {e}")
    
    def _extract_to_global_dictionary(
        self, 
        source_file: Path, 
        target_file: Path, 
        source_language: str,
        target_language: str
    ) -> int:
        """Extract source-target pairs and add to global dictionary with occurrence counting"""
        try:
            # Read source file
            with open(source_file, 'r', encoding='utf-8') as f:
                source_reader = csv.DictReader(f)
                source_headers = source_reader.fieldnames or []
                source_rows = list(source_reader)
            
            # Read target file (with BOM handling)
            with open(target_file, 'r', encoding='utf-8-sig') as f:
                target_reader = csv.DictReader(f)
                target_headers = target_reader.fieldnames or []
                target_rows = list(target_reader)
            
            # Find column pairs (_source -> _target)
            column_pairs = self._find_column_pairs_for_languages(source_headers, target_headers, source_language, target_language)
            
            # Build a lookup dictionary for target rows by ID
            id_column = None
            for candidate in ('Id', 'ID', 'id', 'CodeFigure'):
                if candidate in source_headers and candidate in target_headers:
                    id_column = candidate
                    break
            
            if not id_column:
                logger.warning(f"⚠️ No ID column ('Id'/'ID' or 'CodeFigure') found in {source_file.name}, skipping")
                return 0

            # Create lookup: {id_value: target_row}
            target_lookup = {}
            for target_row in target_rows:
                row_id = target_row.get(id_column)
                if row_id:
                    target_lookup[row_id] = target_row

            pairs_processed = 0
            
            # Extract translations by matching IDs
            for row_idx, source_row in enumerate(source_rows):
                row_id = source_row.get(id_column)
                
                if not row_id or row_id not in target_lookup:
                    continue
                
                target_row = target_lookup[row_id]
                
                for source_col, target_col in column_pairs:
                    source_text = source_row.get(source_col, "").strip()
                    target_text = target_row.get(target_col, "").strip()
                    
                    if source_text and target_text:
                        # Normalize key for global dictionary (case-insensitive, language-specific)
                        key = (source_text.lower(), source_language, target_language)
                        
                        # Add to global dictionary with occurrence counting
                        if key in self.global_dictionary:
                            # If same translation, increment count
                            if self.global_dictionary[key][0] == target_text:
                                self.global_dictionary[key][1] += 1
                            else:
                                # Different translation for same source - create new entry with variation
                                logger.debug(f"🔄 Translation variation: '{source_text}' -> '{target_text}' (existing: '{self.global_dictionary[key][0]}')")
                                # For now, keep the most frequent one, could be enhanced to handle variations
                                if self.global_dictionary[key][1] == 1:  # First occurrence was different
                                    self.global_dictionary[key] = [target_text, 1]
                        else:
                            # New entry
                            self.global_dictionary[key] = [target_text, 1]
                        
                        pairs_processed += 1
            
            logger.debug(f"✅ Processed {pairs_processed} pairs from {source_file.name}")
            return pairs_processed
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract to global dictionary from {source_file.name}: {e}")
            return 0
    
    def _find_column_pairs(
        self, 
        source_headers: List[str], 
        translated_headers: List[str], 
        target_language: str
    ) -> List[tuple]:
        """Find matching column pairs between source and translated files"""
        pairs = []
        
        for source_col in source_headers:
            if source_col.endswith('_en'):
                base_name = source_col[:-3]
                target_col = f"{base_name}_{target_language}"
                
                if target_col in translated_headers:
                    pairs.append((source_col, target_col))
        
            elif source_col == 'CodeFigure':
                base_name = source_col
                target_col = f"{base_name}"
                if target_col in translated_headers:
                    pairs.append((source_col, target_col))
        return pairs
    
    def _find_column_pairs_for_languages(
        self, 
        source_headers: List[str], 
        target_headers: List[str], 
        source_language: str,
        target_language: str
    ) -> List[tuple]:
        """Find matching column pairs between source and target files for specific languages"""
        pairs = []
        
        for source_col in source_headers:
            if source_col.endswith(f'_{source_language}'):
                base_name = source_col[:-len(f'_{source_language}')]
                target_col = f"{base_name}_{target_language}"
                
                if target_col in target_headers:
                    pairs.append((source_col, target_col))
        
            elif source_col == 'CodeFigure':
                base_name = source_col
                target_col = f"{base_name}"
                if target_col in target_headers:
                    pairs.append((source_col, target_col))
        return pairs
    
    def set_current_source_file(self, source_file_path: Path):
        """Set the current source file being translated for lookup context"""
        self.current_source_file = Path(source_file_path).name
        logger.debug(f"🎯 Set current source file for literal lookup: {self.current_source_file}")
    
    def search_literal(
        self, 
        query: str, 
        target_language: str, 
        source_language: str = "en"
    ) -> SearchResult:
        """
        Perform literal exact match lookup.
        
        Args:
            query: Source text to look up
            target_language: Target language
            source_language: Source language (default: en)
            
        Returns:
            SearchResult with exact match or empty result
        """
        # Normalize query for lookup
        normalized_query = query.strip().lower()
        
        # Try to find match with current source file first
        if self.current_source_file:
            key = (self.current_source_file, normalized_query, target_language)
            
            if key in self.dictionary:
                target_text = self.dictionary[key]
                metadata = self.metadata.get(key, {})
                
                # Clean up the target text if it has obvious formatting issues
                cleaned_target = self._clean_target_text(target_text)
                
                match = TranslationMatch(
                    source_text=query,
                    target_text=cleaned_target,  # Use cleaned version
                    similarity_score=1.0,  # Exact match
                    confidence=1.0,  # Always 1.0 for exact matches
                    metadata=metadata
                )
                
                logger.debug(f"✅ Literal match: '{query}' -> '{target_text}' (from {metadata.get('filename', 'unknown')})")
                
                return SearchResult(
                    matches=[match],
                    total_matches=1,
                    exact_matches=1,
                    semantic_matches=0
                )
        
        return SearchResult()  # No match found
    
    def search_global_literal(
        self, 
        query: str, 
        target_language: str,
        source_language: str = "en"
    ) -> SearchResult:
        """
        Perform literal exact match lookup in global dictionary.
        Try multiple variations of the query to handle parentheses and formatting differences.
        
        Args:
            query: Source text to look up
            source_language: Source language code (default: "en")
            target_language: Target language code
            
        Returns:
            SearchResult with exact match or empty result
        """
        # Try different variations of the query
        query_variations = [
            query.strip().lower(),  # Original normalized
            query.strip().lower().replace('(', '').replace(')', ''),  # Without parentheses
            query.strip().lower().replace(' (', ' ').replace(') ', ' '),  # Remove parentheses with spaces
            f"({query.strip().lower()})",  # Add parentheses
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for variation in query_variations:
            if variation not in seen:
                seen.add(variation)
                unique_variations.append(variation)
        
        # Try each variation
        for normalized_query in unique_variations:
            key = (normalized_query, source_language, target_language)
            
            if key in self.global_dictionary:
                target_text, occurrence_count = self.global_dictionary[key]
                
                # Clean up the target text if it has obvious formatting issues
                cleaned_target = self._clean_target_text(target_text)
                
                # Create metadata with occurrence information
                metadata = {
                    'source_language': source_language,
                    'target_language': target_language,
                    'occurrence_count': occurrence_count,
                    'dictionary_type': 'global',
                    'matched_variation': normalized_query,
                    'original_target': target_text,
                    'cleaned_target': cleaned_target if cleaned_target != target_text else None
                }
                
                match = TranslationMatch(
                    source_text=query,
                    target_text=cleaned_target,  # Use cleaned version
                    similarity_score=1.0,  # Exact match
                    confidence=1.0,  # Always 1.0 for exact matches
                    metadata=metadata
                )
                
                logger.debug(f"✅ Global literal match: '{query}' -> '{cleaned_target}' (count: {occurrence_count}, matched: '{normalized_query}')")
                
                return SearchResult(
                    matches=[match],
                    total_matches=1,
                    exact_matches=1,
                    semantic_matches=0
                )
        
        return SearchResult()  # No match found
    
    def _clean_target_text(self, text: str) -> str:
        """
        Clean up target text to remove obvious formatting issues.
        This includes removing double parentheses, extra commas, etc.
        
        Args:
            text: Target text to clean
            
        Returns:
            Cleaned target text
        """
        if not text:
            return text
            
        cleaned = text
        
        # Remove double parentheses like ((text)) -> (text)
        cleaned = cleaned.replace('(((', '((').replace(')))', '))')
        cleaned = cleaned.replace('((', '(').replace('))', ')')
        
        # Fix double commas like ,, -> ,
        cleaned = cleaned.replace(',,', ',')
        
        # Remove trailing commas
        cleaned = cleaned.rstrip(',')
        
        # Remove multiple spaces
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def get_stats(self) -> dict:
        """Get dictionary statistics"""
        return {
            "file_specific_entries": len(self.dictionary),
            "global_entries": len(self.global_dictionary),
            "file_languages": list(set(lang for _, _, lang in self.dictionary.keys())),
            "global_language_pairs": list(set((src_lang, target_lang) for _, src_lang, target_lang in self.global_dictionary.keys()))
        }
    
    def add_translation(
        self,
        source_text: str,
        target_text: str,
        target_language: str,
        metadata: Optional[Dict] = None
    ):
        """
        Add a new translation to the dictionary during runtime.
        
        Args:
            source_text: Source text
            target_text: Translated text
            target_language: Target language
            metadata: Optional metadata (filename, row, cell)
        """
        # Use current source file if available, otherwise use metadata filename
        filename = self.current_source_file
        if not filename and metadata:
            filename = metadata.get('filename', 'unknown')
        if not filename:
            filename = 'unknown'
            
        # Normalize key with filename
        key = (filename, source_text.strip().lower(), target_language)
        
        # Add to dictionary
        self.dictionary[key] = target_text
        
        # Add metadata if provided
        if metadata:
            self.metadata[key] = metadata
        
        logger.debug(f"➕ Added to dictionary: '{source_text}' -> '{target_text}' (file: {filename})")