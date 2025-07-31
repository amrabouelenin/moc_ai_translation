# Glossary Management

This directory contains components for managing glossary terms and their translations.

## Components

### 1. `manager.py`
- **Purpose**: Manages glossary entries and term extraction.
- **Key Functions**:
  - `add_entry`: Adds a new term to the glossary.
  - `extract_terms`: Extracts glossary terms from input text.

### 2. `models.py`
- **Purpose**: Defines data models for glossary entries and extraction results.

### 3. `__init__.py`
- **Purpose**: Initializes the glossary management module.

## Workflow
1. **Term Extraction**: Identifies glossary terms in the input text.
2. **Glossary Updates**: Adds or updates glossary entries as needed.

## Key Updates
- **Integration with Translation Workflow**: Glossary terms are included in the prompt construction and translation process to ensure consistent terminology.
