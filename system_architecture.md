```mermaid
title AI Translation System Architecture

actor User

subgraph "API Layer"
  FastAPI["FastAPI Server"]
end

subgraph "Core Logic"
  Orchestrator["Orchestrator (Translator)"]
  Glossary["Glossary Manager"]
  Memory["Translation Memory"]
  Prompt["MCP-Style Prompt"]
end

subgraph "LLM Interaction"
  LLM["Azure OpenAI GPT"]
end

subgraph "Data Storage"
  FAISS["FAISS Index"]
  GlossaryDB["Glossary Database"]
end

User --> FastAPI : Submit_Translation_Request
FastAPI --> Orchestrator : Forward_Request
Orchestrator --> Glossary : Check_Glossary_Terms
Glossary --> GlossaryDB : Query_Glossary
GlossaryDB --> Glossary : Return_Matches
Orchestrator --> Memory : Search_Translation_Memory
Memory --> FAISS : Query_Semantic_Index
FAISS --> Memory : Return_Matches
Orchestrator --> Prompt : Construct_MCP_Style_Prompt
Prompt --> LLM : Query_LLM_for_Translation
LLM --> Orchestrator : Return_Translation
Orchestrator --> FastAPI : Compile_Response
FastAPI --> User : Return_Translated_Text
```
