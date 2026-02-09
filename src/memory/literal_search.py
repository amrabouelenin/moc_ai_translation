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
        self.dictionary = {}  # {(source_text, target_lang): target_text}
        self.metadata = {}    # {(source_text, target_lang): {file, row, cell}}
        
    def build_from_csv_files(
        self, 
        source_dir: Path, 
        target_language: str,
        pattern: str = "*_en*.csv"
    ) -> int:
        """
        Build dictionary from existing translated CSV files.
        
        Args:
            source_dir: Directory containing source CSV files
            target_language: Target language to build dictionary for
            pattern: Pattern to match source files
            
        Returns:
            Number of entries added to dictionary
        """
        self.dictionary.clear()
        self.metadata.clear()
        
        # Find all English source files
        source_files = list(source_dir.glob(pattern))
        
        for source_file in source_files:
            # Find corresponding translated file
            translated_file = self._find_translated_file(source_file, target_language)
            
            if not translated_file or not translated_file.exists():
                continue
            
            # Read both files and build dictionary
            self._extract_translations(source_file, translated_file, target_language)
        
        logger.info(f"📖 Built literal dictionary: {len(self.dictionary)} entries for {target_language}")
        # Save dictionary to JSON for debugging
        dict_for_json = {f"{k[0]}|||{k[1]}": v for k, v in self.dictionary.items()}
        with open("literal_dictionary_debug.json", "w", encoding='utf-8') as f:
            json.dump(dict_for_json, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Dictionary saved to literal_dictionary_debug.json")
        
        return len(self.dictionary)
    
    def _find_translated_file(self, source_file: Path, target_language: str) -> Optional[Path]:
        """Find the corresponding translated file for a source file"""
        # Check in language subdirectory
        lang_dir = source_file.parent / 'french' # explicitily
        translated_name = source_file.name.replace('_en', f'_{target_language}')
        translated_path = lang_dir / translated_name
        
        return translated_path if translated_path.exists() else None
    
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
            
            # Read translated file
            with open(translated_file, 'r', encoding='utf-8') as f:
                translated_reader = csv.DictReader(f)
                translated_headers = translated_reader.fieldnames or []
                translated_rows = list(translated_reader)
            
            # Find column pairs (_en -> _target_lang)
            column_pairs = self._find_column_pairs(source_headers, translated_headers, target_language)
            
            # Extract translations row by row
            for row_idx, (source_row, translated_row) in enumerate(zip(source_rows, translated_rows)):
                for source_col, target_col in column_pairs:
                    source_text = source_row.get(source_col, "").strip()
                    target_text = translated_row.get(target_col, "").strip()
                    
                    if source_text and target_text:
                        # Normalize key (case-insensitive)
                        key = (source_text.lower(), target_language)
                        
                        # Store translation
                        self.dictionary[key] = target_text
                        
                        # Store metadata
                        self.metadata[key] = {
                            'filename': source_file.name,
                            'row': row_idx + 2,  # +2 for header and 1-indexed
                            'cell': target_col
                        }
            
            logger.debug(f"✅ Extracted from {source_file.name}: {len(column_pairs)} column pairs")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract from {source_file.name}: {e}")
    
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
        
        return pairs
    
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
        key = (normalized_query, target_language)
        
        # Exact match lookup
        if key in self.dictionary:
            target_text = self.dictionary[key]
            metadata = self.metadata.get(key, {})
            
            match = TranslationMatch(
                source_text=query,
                target_text=target_text,
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
    
    def get_stats(self) -> dict:
        """Get dictionary statistics"""
        return {
            "total_entries": len(self.dictionary),
            "languages": list(set(lang for _, lang in self.dictionary.keys()))
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
        # Normalize key
        key = (source_text.strip().lower(), target_language)
        
        # Add to dictionary
        self.dictionary[key] = target_text
        
        # Add metadata if provided
        if metadata:
            self.metadata[key] = metadata
        
        logger.debug(f"➕ Added to dictionary: '{source_text}' -> '{target_text}'")