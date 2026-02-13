"""
File handler for CSV translation operations.
Handles reading, processing, and writing CSV files with column-based translation.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import asyncio

logger = logging.getLogger(__name__)


class CSVFileHandler:
    """Handles CSV file operations for translation"""
    
    def __init__(self):
        self.supported_languages = ["fr", "es", "ar", "zh", "ru", "pt", "de", "it", "ja"]
        self.output_csv = Path("glossary.csv")
        self.glossary_data = []  # List of dicts for CSV rows
        self.max_terms = 100  # Maximum number of terms to collect
    
    def detect_translatable_columns(self, headers: List[str]) -> List[Tuple[str, str]]:
        """
        Detect columns that need translation (ending with _en).
        
        Args:
            headers: List of column headers
            
        Returns:
            List of tuples (original_header, base_name) e.g., [('Title_en', 'Title')]
        """
        translatable = []
        for header in headers:
            if header.endswith('_en'):
                base_name = header[:-3]  # Remove '_en' suffix
                translatable.append((header, base_name))
        
        logger.debug(f"📋 Detected {len(translatable)} translatable columns")
        return translatable
    
    def read_csv(self, file_path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
        """
        Read CSV file and return headers and rows.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Tuple of (headers, rows)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                rows = list(reader)
            
            logger.debug(f"✅ Read {len(rows)} rows")
            return headers, rows
        except Exception as e:
            logger.error(f"❌ Failed to read CSV: {e}")
            raise
    
    def write_csv(
        self,
        file_path: Path,
        headers: List[str],
        rows: List[Dict[str, str]]
    ) -> None:
        """
        Write translated data to CSV file.
        
        Args:
            file_path: Output file path
            headers: Column headers
            rows: Data rows
        """
        try:
            # Create output directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
            
            logger.info(f"✅ Written {len(rows)} rows to {file_path.name}")
        except Exception as e:
            logger.error(f"❌ Failed to write CSV: {e}")
            raise
    
    def generate_output_path(
        self,
        source_path: Path,
        target_language: str,
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Generate output file path for translated CSV in language-specific subdirectory.
        
        Args:
            source_path: Original file path
            target_language: Target language code (e.g., 'fr', 'es')
            output_dir: Optional custom output directory
            
        Returns:
            Path for output file in language subdirectory
        """
        # Replace '_en' with target language in filename
        original_name = source_path.stem
        suffix = source_path.suffix
        
        if '_en' in original_name:
            new_name = original_name.replace('_en', f'_{target_language}')
        else:
            # If no '_en' found, append language before extension
            new_name = f"{original_name}_{target_language}"
        
        output_filename = f"{new_name}{suffix}"
        
        if output_dir:
            # Custom output directory with language subfolder
            language_dir = output_dir / target_language
            language_dir.mkdir(parents=True, exist_ok=True)
            return language_dir / output_filename
        else:
            # Create language subdirectory in same parent as source
            language_dir = source_path.parent / target_language
            language_dir.mkdir(parents=True, exist_ok=True)
            return language_dir / output_filename
    
    def create_translated_headers(
        self,
        original_headers: List[str],
        target_language: str
    ) -> List[str]:
        """
        Create new headers with translated column names.
        
        Args:
            original_headers: Original column headers
            target_language: Target language code
            
        Returns:
            New headers with language suffix replaced
        """
        new_headers = []
        for header in original_headers:
            if header.endswith('_en'):
                base_name = header[:-3]
                new_headers.append(f"{base_name}_{target_language}")
            else:
                new_headers.append(header)
        
        # Add translated_by column header
        new_headers.append("translated_by")
        
        return new_headers
    
    def _load_reference_translation(
        self, 
        source_path: Path, 
        target_lang: str
    ) -> Dict[str, Dict[str, str]]:
        """
        Load existing translation to preserve empty columns and reuse translations.
        
        Args:
            source_path: Source file path
            target_lang: Target language code
            
        Returns:
            Dictionary mapping Id -> row data
        """
        # Map language codes to directory names
        lang_dir_map = {
            'fr': 'french',
            'es': 'spanish',
            'ru': 'russian'
        }
        
        lang_dir_name = lang_dir_map.get(target_lang, target_lang)
        reference_dir = source_path.parent / lang_dir_name
        
        base_name = source_path.stem
        if '_en' in base_name:
            ref_name = base_name.replace('_en', f'_{target_lang}')
        else:
            ref_name = f"{base_name}_{target_lang}"
        
        reference_path = reference_dir / f"{ref_name}{source_path.suffix}"
        
        if not reference_path.exists():
            logger.debug(f"No reference file found at {reference_path}")
            return {}
        
        try:
            reference_lookup = {}
            with open(reference_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_id = row.get('Id')
                    if row_id:
                        reference_lookup[row_id] = row
            
            return reference_lookup
        except Exception as e:
            logger.warning(f"Failed to load reference file: {e}")
            return {}
        
    async def translate_row(
        self,
        row: Dict[str, str],
        translatable_columns: List[Tuple[str, str]],
        target_language: str,
        translator,
        memory_mode: str = "rag",
        reference_lookup: Optional[Dict[str, Dict[str, str]]] = None
    ) -> Dict[str, str]:
        """
        Translate a single row of CSV data.
        
        Args:
            row: Dictionary representing a CSV row
            translatable_columns: Columns to translate
            target_language: Target language code
            translator: TranslationOrchestrator instance
            
        Returns:
            Translated row dictionary
        """
        from ..api.models import TranslationRequest
        
        translated_row = row.copy()
        
        # Track glossary usage across the entire row
        row_glossary_matches = 0
        row_model_used = None
        
        # Get reference row if available
        row_id = row.get('Id')
        reference_row = reference_lookup.get(row_id) if reference_lookup and row_id else None
        
        # For non-translatable columns, handle based on column type
        if reference_row:
            # Columns that should be copied from source (numeric/technical data)
            preserve_from_source = ['BUFR_Scale', 'BUFR_ReferenceValue', 
                                    'BUFR_DataWidth_Bits', 'CREX_Scale', 'CREX_DataWidth_Char']
            
            # Unit columns that might have translated versions in reference
            unit_columns = ['BUFR_Unit', 'CREX_Unit']
            
            for col in list(translated_row.keys()):
                # Skip Id and translatable columns (they're handled separately)
                if col == 'Id' or col.endswith('_en'):
                    continue
                
                # Skip columns that should be preserved from source
                if col in preserve_from_source:
                    continue
                
                # For unit columns, check if reference has a translated version
                if col in unit_columns:
                    ref_translated_col = f"{col}_{target_language}"
                    ref_value = reference_row.get(ref_translated_col, "")
                    if ref_value and ref_value.strip():
                        # Use the translated unit from reference
                        translated_row[col] = ref_value
                        logger.debug(f"📋 Using translated unit from reference: {col} = {ref_value}")
                        continue
                    # Otherwise, keep the value from source (already copied via row.copy())
                    continue
                
                # For other non-translatable columns (like noteIDs), check reference and use empty if reference is empty
                ref_value = reference_row.get(col, "")
                if not ref_value or ref_value.strip() == "":
                    translated_row[col] = ""
                    logger.debug(f"⏭️  Clearing {col} for Id={row_id} - empty in reference")
        
        for original_col, base_name in translatable_columns:
            cell_value = row.get(original_col, "").strip()
            new_col_name = f"{base_name}_{target_language}"
            
            # Check if this column should be skipped based on reference
            if reference_row:
                ref_value = reference_row.get(new_col_name, "")
                if not ref_value or ref_value.strip() == "":
                    translated_row[new_col_name] = ""
                    logger.debug(f"⏭️  Skipping {new_col_name} for Id={row_id} - empty in reference")
                    continue
                else:
                    # Has value in reference - reuse it
                    translated_row[new_col_name] = ref_value
                    logger.debug(f"♻️  Reusing {new_col_name} for Id={row_id} - from reference")
                    continue
            
            # Skip empty cells
            if not cell_value:
                translated_row[new_col_name] = ""
                continue
            
 
            # Check if we have any pre-existing translation in another column
            # This helps LLM extract better glossary terms from parallel texts
            cached_translation = None
            
            # Look for any existing target language columns in this row
            for col_name, value in translated_row.items():
                # Look for columns that already contain translations to the target language
                # e.g. if we're translating to 'fr', look for columns ending with '_fr'
                if col_name.endswith(f"_{target_language}") and value:
                    cached_translation = value
                    break
            
            # Create translation request
            request = TranslationRequest(
                text=cell_value,
                target_language=target_language,
                source_language="en",
                use_glossary=True,
                use_memory=True,
                memory_search_mode=memory_mode,
                cached_translation=cached_translation,
                metadata={}
            )
            
            # Translate using orchestrator
            response = await translator.translate(request)
            row_model_used = response.model_used  # Track the model used

            # Store in new column
            new_col_name = f"{base_name}_{target_language}"
            translated_row[new_col_name] = response.translation
            
            # Accumulate glossary matches for the entire row
            if response.glossary_matches:
                row_glossary_matches += len(response.glossary_matches)
            
            logger.debug(f"✅ '{cell_value}' -> '{response.translation}'")
    
        # After processing all cells, set the translated_by field
        # For MCP, the model_used already contains full metadata, so use it as-is
        # After processing all cells, set the translated_by field
        # Handle case where all columns were reused from reference
        if row_model_used is None:
            # All columns were reused from reference, no translation was performed
            translated_by = "Original"
        elif "MCP" in row_model_used:
            translated_by = f"AI Translator: {row_model_used}"
        else:
            # For standard Azure backend, add glossary tracking
            translated_by = f"AI Translator: {row_model_used}"
            if row_glossary_matches > 0:
                translated_by += f", Glossary Used ({row_glossary_matches} terms)"
            else:
                translated_by += ", Glossary Not Used"
        
        translated_row["translated_by"] = translated_by
        
        # logger.debug(f"✅ '{cell_value}' -> '{response.translation}' ({translated_by})")
        
        # Remove original _en columns
        for original_col, _ in translatable_columns:
            if original_col in translated_row:
                del translated_row[original_col]
        
        return translated_row
    
    async def translate_csv(
        self,
        source_path: Path,
        target_languages: List[str],
        translator,
        output_dir: Optional[Path] = None,
        batch_size: int = 5,
        force: bool = False,
        memory_mode: str = "rag"
    ) -> Dict[str, Path]:
        """
        Translate entire CSV file to one or more target languages.
        
        Args:
            source_path: Path to source CSV file
            target_languages: List of target language codes
            translator: TranslationOrchestrator instance
            output_dir: Optional custom output directory
            batch_size: Number of rows to process concurrently
            force: Force re-translation even if target file already exists
            memory_mode: 'rag' or 'literal'
            
        Returns:
            Dictionary mapping language -> output file path
        """
        logger.info(f"🔄 Translating {source_path.name} to: {', '.join(target_languages)}")
        
        # Read source file
        original_headers, rows = self.read_csv(source_path)
        
        # Detect translatable columns
        translatable_columns = self.detect_translatable_columns(original_headers)
        
        if not translatable_columns:
            logger.warning(f"⚠️  No translatable columns (ending with _en) found in {source_path.name}")
            return {}
        
        output_files = {}
        
        for target_lang in target_languages:
            logger.info(f"🌍 Processing for: {target_lang.upper()}")
            
            # Load reference translation to preserve empty columns
            reference_lookup = self._load_reference_translation(source_path, target_lang)
            if reference_lookup:
                logger.info(f"📖 Loaded {len(reference_lookup)} reference rows for column preservation")
            
            # Generate output path to check if it already exists
            output_path = self.generate_output_path(source_path, target_lang, output_dir)
            
            # Check if target file already exists
            if output_path.exists() and not force:
                logger.info(f"⏩ Target file already exists: {output_path}. Skipping translation.")
                logger.info(f"   Use --force flag to override existing translations.")
                output_files[target_lang] = output_path
                continue
            
            # Create new headers
            new_headers = self.create_translated_headers(original_headers, target_lang)
            
            # Translate rows in batches
            translated_rows = []
            total_rows = len(rows)
            
            for i in range(0, total_rows, batch_size):
                batch = rows[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total_rows + batch_size - 1) // batch_size
                
                logger.debug(f"📦 Batch {batch_num}/{total_batches} ({len(batch)} rows)")
                
                # Translate batch concurrently
                tasks = [
                    self.translate_row(row, translatable_columns, target_lang, translator, memory_mode, reference_lookup)
                    for row in batch
                ]
                batch_results = await asyncio.gather(*tasks)
                translated_rows.extend(batch_results)
                
                logger.debug(f"✅ Batch {batch_num}/{total_batches} completed")
            
            # Generate output path
            output_path = self.generate_output_path(source_path, target_lang, output_dir)
            
            # Write translated file
            self.write_csv(output_path, new_headers, translated_rows)
            
            output_files[target_lang] = output_path
            logger.info(f"✅ Translation to {target_lang.upper()} completed: {output_path}")
        
        return output_files
