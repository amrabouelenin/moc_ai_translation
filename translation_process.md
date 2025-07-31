```mermaid
graph TD
    User[User]
    subgraph AI_Translation_System[AI Translation System]
        API[API Layer]
        subgraph Core[Core Logic]
            Translator[Translator]
            GlossaryManager[Glossary Manager]
            LLMClient[LLM Client]
        end
        Database[Database]
        VectorIndex[Vector Index]
    end

    User -->|Submit text for translation| API
    API -->|Forward request| Core
    Core -->|Process translation request| Translator
    Translator -->|Check glossary for terms| GlossaryManager
    Translator -->|Search for high-confidence matches| VectorIndex
    Translator -->|Skip LLM call if high-confidence match| Translator
    Translator -->|Query LLM for translation if no high-confidence match| LLMClient
    Translator -->|Store translation result| Database
    Database -->|Provide stored translation| API
    API -->|Return translated text| User
```
