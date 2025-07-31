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

## Detailed Explanation of RAG and FAISS

### RAG (Retrieval-Augmented Generation)
- **Purpose**: Enhances translation by retrieving relevant context from a knowledge base (translation memory) before generating a response.
- **Workflow**:
  1. Encode the input query using SentenceTransformer.
  2. Normalize the embeddings for efficient similarity comparison.
  3. Search the FAISS index to retrieve top-K similar entries.
  4. Filter matches based on a similarity threshold.
  5. Check the translation memory for exact matches.
  6. Return the results to the translator.

### FAISS (Facebook AI Similarity Search)
- **Purpose**: Provides fast and scalable similarity search for dense vectors.
- **Key Features**:
  - Supports billions of vectors with efficient indexing.
  - Uses clustering and quantization techniques for speed.
  - Integrates seamlessly with Python for embedding-based search.

### How It Works
1. **Index Creation**:
   - Embeddings from the translation memory are indexed using FAISS.
   - The index is stored on disk for persistence.
2. **Query Processing**:
   - The input query is encoded into an embedding.
   - The embedding is normalized and searched against the FAISS index.
3. **Result Filtering**:
   - Matches are filtered based on a similarity threshold to ensure relevance.

### References
- [FAISS Documentation](https://faiss.ai/)
- [SentenceTransformers](https://www.sbert.net/)
- [RAG: Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401)
