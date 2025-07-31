# LLM Client

This directory contains components for interacting with the Large Language Model (LLM).

## Components

### 1. `client.py`
- **Purpose**: Manages LLM interactions, including prompt construction and translation requests.
- **Key Functions**:
  - `_build_prompt`: Constructs MCP-style prompts using glossary and memory matches.
  - `translate`: Sends translation requests to the LLM.

### 2. `__init__.py`
- **Purpose**: Initializes the LLM client module.

## Workflow
1. **Prompt Construction**: Builds structured prompts combining glossary and memory matches.
2. **LLM Query**: Sends the prompt to the LLM and retrieves the translation.

## Key Updates
- **Hybrid RAGSearch Logic**: LLM is only queried for low-confidence matches, reducing unnecessary calls.
