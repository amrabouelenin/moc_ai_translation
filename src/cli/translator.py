"""
CLI entry point for CSV translation.
Provides command-line interface for translating CSV files with column-based approach.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional
import time

from .file_handler import CSVFileHandler
from ..core.translator import TranslationOrchestrator

# Configure logging
import os

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure file handler for debug logs
file_handler = logging.FileHandler('logs/translation_debug.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Configure console handler for essential info only
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(message)s'))

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.handlers = []  # Remove any existing handlers
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Get module logger
logger = logging.getLogger(__name__)


class TranslationCLI:
    """Command-line interface for CSV translation"""
    
    def __init__(self):
        self.file_handler = CSVFileHandler()
        self.translator = None
    
    def setup_translator(self, llm_backend: str = "azure", memory_mode: str = "rag"):
        """Initialize the translation orchestrator"""
        try:
            logger.info("🚀 Initializing AI Translation System...")
            logger.info(f"   Backend: {llm_backend} | Memory: {memory_mode}")
            self.translator = TranslationOrchestrator(
                llm_backend=llm_backend,
                memory_mode=memory_mode
            )
            logger.info("✅ Translation system ready")
        except Exception as e:
            logger.error(f"❌ Failed to initialize translator: {e}")
            sys.exit(1)
    
    async def translate_file(
        self,
        source_path: Path,
        target_languages: List[str],
        output_dir: Optional[Path] = None,
        batch_size: int = 5,
        force: bool = False,
        memory_mode: str = "rag"  # NEW
    ):
        """
        Translate a single CSV file.
        
        Args:
            source_path: Path to source CSV file
            target_languages: List of target language codes
            output_dir: Optional custom output directory
            batch_size: Number of rows to process concurrently
            force: Whether to force re-translation of already translated files
        """
        start_time = time.time()
        
        # Build literal dictionary ONCE before translating file
        if memory_mode == "literal":
            source_dir = source_path.parent
            for target_lang in target_languages:
                logger.info(f"📖 Building literal dictionary for {target_lang}...")
                count = self.translator.literal_search.build_from_csv_files(
                    source_dir=source_dir,
                    target_language=target_lang
                )
                logger.info(f"✅ Dictionary ready: {count} entries")
        
        logger.info(f"📄 Source: {source_path} | Target: {', '.join(target_languages)} | Batch: {batch_size}")
        
        
        output_files = await self.file_handler.translate_csv(
            source_path=source_path,
            target_languages=target_languages,
            translator=self.translator,
            output_dir=output_dir,
            batch_size=batch_size,
            force=force,
            memory_mode=memory_mode
        )
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"✅ TRANSLATION COMPLETED in {elapsed_time:.2f}s")
        for lang, path in output_files.items():
            logger.info(f"   📁 {lang.upper()}: {path}")
        
        return output_files
    
    async def translate_directory(
        self,
        source_dir: Path,
        target_languages: List[str],
        output_dir: Optional[Path] = None,
        batch_size: int = 5,
        pattern: str = "*_en_*.csv",
        force: bool = False,
        memory_mode: str = "rag"  # ADD THIS
    ):
        """
        Translate all matching CSV files in a directory.
        
        Args:
            source_dir: Directory containing source CSV files
            target_languages: List of target language codes
            output_dir: Optional custom output directory
            batch_size: Number of rows to process concurrently
            pattern: Glob pattern for file matching
            force: Whether to force re-translation of already translated files
        """
        logger.info(f"🔍 Scanning directory: {source_dir}")
        logger.info(f"🔎 Pattern: {pattern}")
        
        # Find all matching files
        csv_files = list(source_dir.glob(pattern))
        
        if not csv_files:
            logger.warning(f"⚠️  No files matching pattern '{pattern}' found in {source_dir}")
            return {}
        
        logger.info(f"📋 Found {len(csv_files)} file(s) to translate")
        
        all_output_files = {}
        
        for i, csv_file in enumerate(csv_files, 1):
            logger.info(f"Processing file {i}/{len(csv_files)}: {csv_file.name}")
            
            try:
                output_files = await self.translate_file(
                    source_path=csv_file,
                    target_languages=target_languages,
                    output_dir=output_dir,
                    batch_size=batch_size,
                    force=force,
                    memory_mode=memory_mode
                )
                all_output_files[csv_file.name] = output_files
            except Exception as e:
                logger.error(f"❌ Failed to translate {csv_file.name}: {e}")
                continue
        
        return all_output_files


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="AI Translation CLI - Translate CSV files with column-based approach",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Translate single file to French
  python -m src.cli.translator --source repos/BUFR4/BUFR_TableD_en_05.csv --target fr
  
  # Translate single file to multiple languages
  python -m src.cli.translator --source repos/BUFR4/BUFR_TableD_en_05.csv --targets fr,es,ar
  
  # Translate all files in directory
  python -m src.cli.translator --source-dir repos/BUFR4 --targets fr,es,ar
  
  # Translate with custom output directory
  python -m src.cli.translator --source file.csv --target fr --output-dir translated/
  
  # Adjust batch size for performance
  python -m src.cli.translator --source file.csv --target fr --batch-size 10
        """
    )
    
    # Source options (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        '--source',
        type=Path,
        help='Path to source CSV file'
    )
    source_group.add_argument(
        '--source-dir',
        type=Path,
        help='Directory containing source CSV files'
    )
    
    parser.add_argument(
        '--llm-backend',
        type=str,
        default='azure',
        choices=['azure', 'mcp'],
        help='LLM backend to use: azure (standard prompt) or mcp (active retrieval)'
    )
    # Target language options (mutually exclusive)
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        '--target',
        type=str,
        help='Single target language code (e.g., fr, es, ar)'
    )
    target_group.add_argument(
        '--targets',
        type=str,
        help='Comma-separated target language codes (e.g., fr,es,ar)'
    )
    parser.add_argument(
        '--memory-mode',
        type=str,
        choices=['rag', 'literal'],
        default='rag',
        help='Memory search mode: rag (semantic similarity) or literal (exact match dictionary)'
    )
    # Optional arguments
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Custom output directory (default: same as source)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=5,
        help='Number of rows to process concurrently (default: 5)'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*_en_*.csv',
        help='File pattern for directory mode (default: *_en_*.csv)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-translation even if target file already exists'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse target languages
    if args.target:
        target_languages = [args.target]
    else:
        target_languages = [lang.strip() for lang in args.targets.split(',')]
    
    # Initialize CLI
    cli = TranslationCLI()
    cli.setup_translator(
        llm_backend=args.llm_backend,
        memory_mode=args.memory_mode
    )
    

    if args.source:
        # Single file mode
        if not args.source.exists():
            logger.error(f"❌ Source file not found: {args.source}")
            sys.exit(1)
        
        await cli.translate_file(
            source_path=args.source,
            target_languages=target_languages,
            output_dir=args.output_dir,
            batch_size=args.batch_size,
            force=args.force,
            memory_mode=args.memory_mode
        )
    
    elif args.source_dir:
        # Directory mode
        if not args.source_dir.exists():
            logger.error(f"❌ Source directory not found: {args.source_dir}")
            sys.exit(1)
        
        await cli.translate_directory(
            source_dir=args.source_dir,
            target_languages=target_languages,
            output_dir=args.output_dir,
            batch_size=args.batch_size,
            pattern=args.pattern,
            force=args.force,
            memory_mode=args.memory_mode
        )
    
    logger.info("\n🎉 All translations completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
