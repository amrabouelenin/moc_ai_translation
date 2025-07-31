```mermaid
sequenceDiagram
    participant User
    participant API
    participant Translator
    participant GlossaryManager
    participant LLMClient
    participant VectorIndex
    participant Database
    participant TMManager
    participant RAGSearch

    User->>API: Submit text for translation
    API->>Translator: Forward request
    Translator->>GlossaryManager: Check glossary for terms
    GlossaryManager-->>Translator: Return glossary terms
    Translator->>VectorIndex: Search for high-confidence matches
    VectorIndex-->>Translator: Return high-confidence matches
    alt High-confidence match found
        Translator-->>API: Skip LLM call, return high-confidence match
    else No high-confidence match
        Translator->>LLMClient: Query LLM for translation
        LLMClient-->>Translator: Return translation
    end
    Translator->>Database: Store translation result
    Database-->>API: Provide stored translation
    API-->>User: Return translated text
```
