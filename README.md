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
│   FastAPI       │    │  Translation     │    │   Azure       │
│   Server        │───▶│  Orchestrator    │───▶│  OpenAI       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌────────┐            ┌─────────────┐          ┌─────────────┐
    │Glossary│            │Translation  │          │   FAISS   │
    │Manager │            │Memory       │          │   Index   │
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
