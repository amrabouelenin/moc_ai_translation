# AI Translation System

A comprehensive AI-powered translation system with glossary management, translation memory, and RAG-based semantic search capabilities.

## 🚀 Features

- ✅ **AI Translation** using Azure OpenAI GPT-4o
- ✅ **Glossary Management** - Automatic term extraction from customizable glossaries
- ✅ **Translation Memory** - Semantic search using RAG with FAISS
- ✅ **MCP-Style Prompts** - Structured prompts combining glossary and memory
- ✅ **REST API** - FastAPI-based web service
- ✅ **Multi-language Support** - Configurable source/target languages
- ✅ **Docker Support** - Containerized deployment ready

## 📋 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

The system is pre-configured for Azure OpenAI with your provided settings:

```bash
# .env file is already configured with your Azure settings
# AZURE_OPENAI_API_KEY=open_api_key
# AZURE_OPENAI_ENDPOINT=https://moc-translator.openai.azure.com/
# AZURE_OPENAI_DEPLOYMENT_NAME=WIS2-MoC-gpt-4o
```

### 3. Run the System

```bash
python run.py
```

The server will start at `http://localhost:8000`

### 4. Test Translation

```bash
curl -X POST "http://localhost:8000/translate" \
  -H "Content-Type: application/json" \
  -d '{"text": "The cloud server failed to respond.", "target_language": "fr"}'
```

## 🐳 Docker Deployment

```bash
docker build -t ai-translation .
docker run -p 8000:8000 ai-translation
```

## 📡 API Endpoints

### POST `/translate`
Translate text with AI assistance.

**Request:**
```json
{
  "text": "The cloud server failed to respond.",
  "target_language": "fr",
  "source_language": "en",
  "use_glossary": true,
  "use_memory": true
}
```

**Response:**
```json
{
  "translation": "Le serveur cloud n'a pas répondu.",
  "source_text": "The cloud server failed to respond.",
  "target_language": "fr",
  "glossary_matches": [
    {
      "term": "cloud server",
      "translation": "serveur cloud",
      "confidence": 1.0
    }
  ],
  "memory_matches": [...],
  "confidence": 0.92,
  "model_used": "azure:WIS2-MoC-gpt-4o",
  "processing_time": 1.234
}
```

### GET `/health`
System health check.

### GET `/stats`
System statistics including glossary and memory counts.

### POST `/feedback`
Submit user feedback and optionally add to translation memory.

## 🧪 Testing the APIs

### 1. Test Translation API

```bash
curl -X POST "http://localhost:8000/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "target_language": "fr",
    "source_language": "en",
    "use_glossary": true,
    "use_memory": true
  }'
```

**Expected Response:**
```json
{
  "translation": "Bonjour, comment ça va ?",
  "source_text": "Hello, how are you?",
  "target_language": "fr",
  "glossary_matches": [],
  "memory_matches": [],
  "confidence": 0.92,
  "model_used": "azure:WIS2-MoC-gpt-4o",
  "processing_time": 1.234
}
```

### 2. Test Health Check API

```bash
curl -X GET "http://localhost:8000/health"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": 1625256000
}
```

### 3. Test System Stats API

```bash
curl -X GET "http://localhost:8000/stats"
```

**Expected Response:**
```json
{
  "glossary": {
    "total_terms": 100,
    "languages": ["fr"]
  },
  "memory": {
    "total_entries": 500,
    "index_size": 500
  },
  "llm": {
    "provider": "azure",
    "model": "WIS2-MoC-gpt-4o",
    "status": "connected"
  }
}
```

### 4. Test Feedback API

```bash
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "source_text": "Hello, how are you?",
    "target_text": "Bonjour, comment ça va ?",
    "target_language": "fr",
    "is_accepted": true,
    "confidence": 0.9
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Feedback submitted successfully."
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (azure/openai/anthropic/local) | `azure` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | *configured* |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | *configured* |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Azure deployment name | `WIS2-MoC-gpt-4o` |
| `DATABASE_URL` | SQLite database path | `sqlite:///./translation.db` |
| `VECTOR_DB_PATH` | FAISS index path | `./data/vector_index.faiss` |

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │  Translation     │    │   Azure         │
│   Server        │───▶│  Orchestrator    │───▶│  OpenAI         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌────────┐            ┌─────────────┐          ┌─────────────┐
    │Glossary│            │Translation  │          │   FAISS     │
    │Manager │            │Memory       │          │   Index     │
    └────────┘            └─────────────┘          └─────────────┘
```

## 🎯 Example Usage

### Python Client
```python
import requests

# Translate text
response = requests.post("http://localhost:8000/translate", json={
    "text": "The database connection failed",
    "target_language": "fr"
})
print(response.json())
```

### JavaScript Client
```javascript
const response = await fetch('http://localhost:8000/translate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'The API is not responding',
    target_language: 'fr'
  })
});
const result = await response.json();
console.log(result);
```

## 🔍 Development

### Adding New Glossary Terms
```python
from src.glossary.manager import GlossaryManager

manager = GlossaryManager()
manager.add_entry(GlossaryEntry(
    term="microservice",
    preferred_translation="microservice",
    target_language="fr",
    notes="Architecture logicielle"
))
```

### Extending LLM Support
The system supports multiple LLM providers:
- Azure OpenAI (configured)
- OpenAI GPT
- Anthropic Claude
- Local models (Ollama)

## 🛠️ Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Azure authentication**: Verify your API key and endpoint
   ```bash
   echo $AZURE_OPENAI_API_KEY
   ```

3. **Database issues**: Check file permissions for SQLite
   ```bash
   ls -la *.db
   ```

## 📈 Performance Tips

- Use `use_glossary=False` for faster processing when glossary is not needed
- Use `use_memory=False` to skip RAG search for simple translations
- Monitor `/stats` endpoint for system health
- Use Docker for consistent deployment environments

## 🔄 Future Enhancements

- Support for additional languages
- Real-time translation memory updates
- Advanced confidence scoring
- Batch translation support
- Webhook notifications

## 🛠️ Detailed Sequential Steps for Translation Workflow

1. **User Input**:
   - The user submits a text for translation via the `/translate` API endpoint.
   - Example input:
     ```json
     {
       "text": "Hello, how are you?",
       "target_language": "fr",
       "source_language": "en",
       "use_glossary": true,
       "use_memory": true
     }
     ```

2. **API Layer**:
   - The API receives the request and forwards it to the core logic for processing.

3. **Core Logic**:
   - The `Translator` component orchestrates the translation process.

4. **Glossary Check**:
   - The `GlossaryManager` checks if any terms in the input text have predefined translations in the glossary.
   - If matches are found, they are included in the response.

5. **Translation Memory Search**:
   - The `RAGSearch` component searches the FAISS index for semantically similar translations.
   - If matches are found, they are included in the response.

6. **LLM Query**:
   - If no exact or semantic matches are found, the `LLMClient` queries the LLM (e.g., Azure OpenAI GPT) to generate a translation.

7. **Prompt Construction**:
   - The `Translator` combines results from the glossary, translation memory, and LLM to construct a final prompt.

8. **Translation Generation**:
   - The LLM generates the translation based on the constructed prompt.

9. **Response Compilation**:
   - The API compiles the final response, including:
     - Translated text
     - Glossary matches
     - Memory matches
     - Confidence score
     - Model used
     - Processing time
   - Example response:
     ```json
     {
       "translation": "Bonjour, comment ça va ?",
       "source_text": "Hello, how are you?",
       "target_language": "fr",
       "glossary_matches": [],
       "memory_matches": [],
       "confidence": 0.92,
       "model_used": "azure:WIS2-MoC-gpt-4o",
       "processing_time": 1.234
     }
     ```

10. **User Feedback**:
    - The user can submit feedback via the `/feedback` API endpoint to improve future translations.
    - Example feedback input:
      ```json
      {
        "source_text": "Hello, how are you?",
        "target_text": "Bonjour, comment ça va ?",
        "target_language": "fr",
        "is_accepted": true,
        "confidence": 0.9
      }
      ```

### Querying the LLM for Low-Confidence Matches

If the system does not find a high-confidence match (e.g., similarity score ≤ 0.8) in the translation memory or vector index, it queries the LLM for a translation. This ensures that the system can still provide a translation even when existing matches are insufficiently reliable.

- **High-Confidence Matches**: Matches with a similarity score > 0.8 are used directly without querying the LLM.
- **Low-Confidence Matches**: The LLM is queried to generate a translation when no high-confidence match is found.
