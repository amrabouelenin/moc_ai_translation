# Memory Management

This directory contains components for managing translation memory and performing semantic searches.

## Components

### 1. `rag_search.py`
- **Purpose**: Implements semantic search using FAISS and manages translation memory.
- **Key Functions**:
  - `search_similar`: Searches for semantically similar translations in the memory.
  - `add_and_update_index`: Adds new entries to the translation memory and updates the FAISS index.

### 2. `tm_manager.py`
- **Purpose**: Manages the translation memory database.
- **Key Functions**:
  - `get_all_entries`: Retrieves all entries from the translation memory.
  - `add_entry`: Adds a new entry to the translation memory.

### 3. `__init__.py`
- **Purpose**: Initializes the memory management module.

## Workflow
1. **Translation Memory Search**: Searches for high-confidence matches in the memory.
2. **FAISS Indexing**: Uses FAISS for efficient semantic search.
3. **Memory Updates**: Updates the memory with new translations.

## Key Updates
- **Hybrid RAGSearch Logic**: High-confidence matches skip LLM calls, improving efficiency and reducing costs.
