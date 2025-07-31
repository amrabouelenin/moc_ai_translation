```mermaid
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

User --> FastAPI : Submit Translation Request
FastAPI --> Orchestrator : Forward Request
Orchestrator --> Glossary : Check Glossary Terms
Glossary --> GlossaryDB : Query Glossary
GlossaryDB --> Glossary : Return Matches
Orchestrator --> Memory : Search Translation Memory
Memory --> FAISS : Query Semantic Index
FAISS --> Memory : Return Matches
Orchestrator --> Prompt : Construct Prompt
Prompt --> LLM : Query LLM
LLM --> Orchestrator : Return Translation
Orchestrator --> FastAPI : Compile Response
FastAPI --> User : Return Translation
```
