# Data Directory

This directory contains the data files used by the AI Translation System, including vector indices and metadata for translation memory.

## Contents

### 1. `vector_index.faiss`
- **Purpose**: Stores the FAISS index for semantic search.
- **Details**:
  - Contains dense vector representations of translation memory entries.
  - Used for efficient similarity search during translation.

### 2. `vector_index.json`
- **Purpose**: Stores metadata associated with the FAISS index.
- **Details**:
  - Includes the original text and embeddings used to create the FAISS index.
  - Acts as a reference for reconstructing or updating the index.

## How the Data is Created
1. **Translation Memory Entries**:
   - Entries are added to the translation memory using the `tm_manager` module.
   - Each entry includes source text, target text, and metadata.
2. **Embedding Generation**:
   - Text entries are encoded into dense vector representations using SentenceTransformer.
   - These embeddings are normalized for efficient similarity comparison.
3. **FAISS Indexing**:
   - The embeddings are added to the FAISS index for fast retrieval.
   - The index is periodically updated as new entries are added.
4. **Metadata Storage**:
   - The `vector_index.json` file is updated alongside the FAISS index to ensure consistency.

## Key References
- [FAISS Documentation](https://faiss.ai/)
- [SentenceTransformers](https://www.sbert.net/)

## Notes
- Ensure the FAISS index and metadata file are always in sync to avoid inconsistencies.
- Use the `rag_search` module to manage and update these files.
