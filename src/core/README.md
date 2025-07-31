# Core Translation Logic

This directory contains the core logic for the AI Translation System. Below is an explanation of the key components and their roles in the translation process.

## Components

### 1. `translator.py`
- **Purpose**: Orchestrates the translation process by coordinating glossary checks, translation memory searches, and LLM queries.
- **Key Functions**:
  - `translate`: Main function to handle translation requests.
  - `_fallback_translate`: Provides a fallback translation using memory matches or simple word-by-word translation.
  - `_calculate_confidence`: Calculates the confidence score based on glossary and memory matches.

### 2. `config.py`
- **Purpose**: Manages system-wide configuration settings.
- **Key Features**:
  - Reads settings like API host, port, LLM provider, and database paths.

### 3. `__init__.py`
- **Purpose**: Initializes the core logic module.

## Workflow
1. **Glossary Check**: Extracts terms from the glossary and includes them in the translation process.
2. **Translation Memory Search**: Searches for high-confidence matches in the translation memory.
3. **LLM Query**: Queries the LLM for translations if no high-confidence match is found.
4. **Fallback Translation**: Provides a fallback translation if the LLM query fails.

## Key Updates
- **Hybrid RAGSearch Logic**: High-confidence matches skip LLM calls, improving efficiency and reducing costs.
